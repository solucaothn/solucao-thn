query "catalog/chat/messages" verb=GET {
  api_group = "Catalog"
  auth = "user"

  input {
    int conversation_id
    int after_message_id?
    int before_message_id?
    int limit?
    int edited_since?
  }

  stack {
    // Horário do servidor no início da consulta; o frontend o devolve como
    // edited_since na consulta seguinte (o relógio do navegador não entra).
    var $server_time {
      value = now
    }
  
    precondition ($input.after_message_id == null || $input.before_message_id == null) {
      error_type = "inputerror"
      error = "Informe somente um cursor de mensagens."
    }
  
    precondition ($input.limit == null || $input.limit > 0) {
      error_type = "inputerror"
      error = "O limite da página deve ser maior que zero."
    }
  
    var $page_limit {
      value = 50
    }
  
    conditional {
      if ($input.limit != null) {
        var.update $page_limit {
          value = $input.limit
        }
      }
    }
  
    conditional {
      if ($page_limit > 100) {
        var.update $page_limit {
          value = 100
        }
      }
    }
  
    db.get chat_conversation {
      field_name = "id"
      field_value = $input.conversation_id
      output = [
        "id"
        "donation_id"
        "donor_id"
        "interested_user_id"
        "donor_last_read_message_id"
        "interested_last_read_message_id"
      ]
    } as $conversation
  
    precondition ($conversation != null && ($conversation.donor_id == $auth.id || $conversation.interested_user_id == $auth.id)) {
      error_type = "notfound"
      error = "Conversa não encontrada."
    }
  
    db.get donation {
      field_name = "id"
      field_value = $conversation.donation_id
      output = ["id", "title", "status"]
    } as $donation
  
    precondition ($donation != null) {
      error_type = "notfound"
      error = "Conversa não encontrada."
    }
  
    var $messages {
      value = []
    }
  
    var $has_older {
      value = false
    }
  
    var $has_newer {
      value = false
    }
  
    // Resultado da consulta decrescente (sem cursor ou com before_message_id).
    var $recent_messages {
      value = []
    }
  
    // Mensagens já exibidas que foram editadas desde a consulta anterior.
    var $edited_raw {
      value = []
    }
  
    conditional {
      if ($input.after_message_id != null) {
        // Mensagens novas (atualização automática), em ordem crescente.
        db.query chat_message {
          where = ($db.chat_message.conversation_id == $conversation.id && $db.chat_message.id > $input.after_message_id)
          return = {type: "count"}
        } as $newer_count
      
        db.query chat_message {
          where = ($db.chat_message.conversation_id == $conversation.id && $db.chat_message.id > $input.after_message_id)
          sort = {id: "asc"}
          return = {
            type  : "list"
            paging: {page: 1, per_page: $page_limit, metadata: false}
          }
        
          output = [
            "id"
            "conversation_id"
            "sender_id"
            "text"
            "created_at"
            "edited_at"
          ]
        } as $newer_messages
      
        var.update $messages {
          value = $newer_messages
        }
      
        var.update $has_newer {
          value = $newer_count > $page_limit
        }
      
        // Edições das mensagens até after_message_id desde edited_since, com
        // 5 s de folga (repetições são substituídas pelo id no frontend).
        conditional {
          if ($input.edited_since != null) {
            var $edited_floor {
              value = $input.edited_since - 5000
            }
          
            db.query chat_message {
              where = ($db.chat_message.conversation_id == $conversation.id && $db.chat_message.id <= $input.after_message_id && $db.chat_message.edited_at >= $edited_floor)
              sort = {id: "asc"}
              return = {
                type  : "list"
                paging: {page: 1, per_page: 100, metadata: false}
              }
            
              output = [
                "id"
                "conversation_id"
                "sender_id"
                "text"
                "created_at"
                "edited_at"
              ]
            } as $edited_since_messages
          
            var.update $edited_raw {
              value = $edited_since_messages
            }
          }
        }
      }
    
      else {
        // Últimas N mensagens, ou as anteriores a before_message_id:
        // busca em ordem decrescente e monta a lista em ordem cronológica
        // inserindo cada mensagem no início (foreach + unshift, mesmo padrão
        // de foreach + push usado no projeto).
      
        // Duas consultas separadas: nenhuma comparação com $input nulo
        // dentro do where.
        conditional {
          if ($input.before_message_id == null) {
            db.query chat_message {
              where = $db.chat_message.conversation_id == $conversation.id
              sort = {id: "desc"}
              return = {
                type  : "list"
                paging: {page: 1, per_page: $page_limit, metadata: false}
              }
            
              output = [
                "id"
                "conversation_id"
                "sender_id"
                "text"
                "created_at"
                "edited_at"
              ]
            } as $latest_messages
          
            var.update $recent_messages {
              value = $latest_messages
            }
          }
        
          else {
            db.query chat_message {
              where = ($db.chat_message.conversation_id == $conversation.id && $db.chat_message.id < $input.before_message_id)
              sort = {id: "desc"}
              return = {
                type  : "list"
                paging: {page: 1, per_page: $page_limit, metadata: false}
              }
            
              output = [
                "id"
                "conversation_id"
                "sender_id"
                "text"
                "created_at"
                "edited_at"
              ]
            } as $previous_messages
          
            var.update $recent_messages {
              value = $previous_messages
            }
          }
        }
      
        foreach ($recent_messages) {
          each as $recent_message {
            var.update $messages {
              value = $messages|unshift:$recent_message
            }
          }
        }
      
        conditional {
          if (($messages|count) > 0) {
            var $oldest_message {
              value = $messages|first
            }
          
            db.query chat_message {
              where = ($db.chat_message.conversation_id == $conversation.id && $db.chat_message.id < $oldest_message.id)
              return = {type: "count"}
            } as $older_count
          
            var.update $has_older {
              value = $older_count > 0
            }
          }
        }
      }
    }
  
    // Marca a conversa como lida para quem lê, até a mensagem mais nova
    // devolvida. Só avança (nunca volta atrás), não mexe no campo da outra
    // pessoa e não registra evento de log.
    conditional {
      if (($messages|count) > 0) {
        var $newest_message {
          value = $messages|last
        }
      
        conditional {
          if ($conversation.donor_id == $auth.id) {
            conditional {
              if ($newest_message.id > ($conversation.donor_last_read_message_id ?? 0)) {
                db.edit chat_conversation {
                  field_name = "id"
                  field_value = $conversation.id
                  data = {donor_last_read_message_id: $newest_message.id}
                } as $donor_read_update
              }
            }
          }
        
          else {
            conditional {
              if ($newest_message.id > ($conversation.interested_last_read_message_id ?? 0)) {
                db.edit chat_conversation {
                  field_name = "id"
                  field_value = $conversation.id
                  data = {interested_last_read_message_id: $newest_message.id}
                } as $interested_read_update
              }
            }
          }
        }
      }
    }
  
    // "Visto": última mensagem lida pela OUTRA pessoa (decisão aprovada pelo
    // Higor na chat-visto-edicao). Só esse id, sem horário da leitura.
    var $other_last_read_message_id {
      value = $conversation.donor_last_read_message_id ?? 0
    }
  
    conditional {
      if ($conversation.donor_id == $auth.id) {
        var.update $other_last_read_message_id {
          value = $conversation.interested_last_read_message_id ?? 0
        }
      }
    }
  
    db.get user {
      field_name = "id"
      field_value = $conversation.donor_id
      output = ["name", "photo"]
    } as $donor_user
  
    db.get user {
      field_name = "id"
      field_value = $conversation.interested_user_id
      output = ["name", "photo"]
    } as $interested_user
  
    var $donor_first_name {
      value = "Usuário"
    }
  
    conditional {
      if ($donor_user != null) {
        var.update $donor_first_name {
          value = (($donor_user.name ?? "")|trim|split:" "|first)
        }
      }
    }
  
    var $interested_first_name {
      value = "Usuário"
    }
  
    conditional {
      if ($interested_user != null) {
        var.update $interested_first_name {
          value = (($interested_user.name ?? "")|trim|split:" "|first)
        }
      }
    }
  
    // Foto só da OUTRA pessoa participante (nunca a de quem consulta).
    var $other_user {
      value = $donor_user
    }
  
    conditional {
      if ($conversation.donor_id == $auth.id) {
        var.update $other_user {
          value = $interested_user
        }
      }
    }
  
    var $other_user_photo {
      value = null
    }
  
    conditional {
      if ($other_user != null && $other_user.photo != null) {
        conditional {
          if ($env.PUBLIC_BASE_URL == null || $env.PUBLIC_BASE_URL == "") {
            throw {
              name = "ConfigurationError"
              value = "PUBLIC_BASE_URL não está configurada."
            }
          }
        }
      
        var.update $other_user_photo {
          value = $env.PUBLIC_BASE_URL ~ $other_user.photo.path
        }
      }
    }
  
    var $messages_with_names {
      value = []
    }
  
    foreach ($messages) {
      each as $message {
        var $sender_first_name {
          value = $interested_first_name
        }
      
        conditional {
          if ($message.sender_id == $conversation.donor_id) {
            var.update $sender_first_name {
              value = $donor_first_name
            }
          }
        }
      
        // Autoria calculada a partir da sessão; sender_id não vai na resposta.
        var $sent_by_me {
          value = $message.sender_id == $auth.id
        }
      
        var.update $messages_with_names {
          value = $messages_with_names
            |push:```
              {
                id: $message.id,
                conversation_id: $message.conversation_id,
                sender_first_name: $sender_first_name,
                sent_by_me: $sent_by_me,
                text: $message.text,
                created_at: $message.created_at,
                edited_at: $message.edited_at
              }
              ```
        }
      }
    }
  
    // Mesmo formato para as editadas (laço igual ao de cima).
    var $edited_with_names {
      value = []
    }
  
    foreach ($edited_raw) {
      each as $edited_message {
        var $edited_sender_first_name {
          value = $interested_first_name
        }
      
        conditional {
          if ($edited_message.sender_id == $conversation.donor_id) {
            var.update $edited_sender_first_name {
              value = $donor_first_name
            }
          }
        }
      
        var $edited_sent_by_me {
          value = $edited_message.sender_id == $auth.id
        }
      
        var.update $edited_with_names {
          value = $edited_with_names
            |push:```
              {
                id: $edited_message.id,
                conversation_id: $edited_message.conversation_id,
                sender_first_name: $edited_sender_first_name,
                sent_by_me: $edited_sent_by_me,
                text: $edited_message.text,
                created_at: $edited_message.created_at,
                edited_at: $edited_message.edited_at
              }
              ```
        }
      }
    }
  }

  response = {
    messages                  : $messages_with_names
    donation_title            : $donation.title
    donation_status           : $donation.status
    has_older                 : $has_older
    has_newer                 : $has_newer
    other_last_read_message_id: $other_last_read_message_id
    other_user_photo          : $other_user_photo
    edited_messages           : $edited_with_names
    server_time               : $server_time
  }

  guid = "_vyIXcGn_BV6HB8-w8xgjvBdiAw"
}