query "catalog/chat/unread_total" verb=GET {
  api_group = "Catalog"
  auth = "user"

  input {
  }

  stack {
    // Todas as conversas da pessoa, sem paginação; só os campos da contagem.
    db.query chat_conversation {
      where = ($db.chat_conversation.donor_id == $auth.id || $db.chat_conversation.interested_user_id == $auth.id)
      return = {type: "list"}
      output = [
        "id"
        "donor_id"
        "donor_last_read_message_id"
        "interested_last_read_message_id"
      ]
    } as $conversations
  
    var $unread_total {
      value = 0
    }
  
    foreach ($conversations) {
      each as $conversation {
        // Última mensagem lida por quem consulta.
        var $my_last_read {
          value = $conversation.interested_last_read_message_id ?? 0
        }
      
        conditional {
          if ($conversation.donor_id == $auth.id) {
            var.update $my_last_read {
              value = $conversation.donor_last_read_message_id ?? 0
            }
          }
        }
      
        // Mesma contagem do GET conversations: mensagens da outra pessoa
        // posteriores à última lida.
        db.query chat_message {
          where = ($db.chat_message.conversation_id == $conversation.id && $db.chat_message.sender_id != $auth.id && $db.chat_message.id > $my_last_read)
          return = {type: "count"}
        } as $conversation_unread
      
        var.update $unread_total {
          value = $unread_total + $conversation_unread
        }
      }
    }
  }

  response = {unread_total: $unread_total}
  guid = "I6jgIvMU_TN58bkM3WxfnFA52yo"
}