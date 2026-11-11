query "catalog/chat/messages" verb=PATCH {
  api_group = "Catalog"
  auth = "user"

  input {
    int message_id
    text? message_text? filters=trim
  }

  stack {
    // 1. Tamanho antes de qualquer consulta, como no envio.
    precondition ($input.message_text != null && ($input.message_text|strlen) > 0 && ($input.message_text|strlen) <= 1000) {
      error_type = "inputerror"
      error = "A mensagem deve conter entre 1 e 1000 caracteres."
    }
  
    // 2. Só quem enviou pode editar; o resto recebe o 404 genérico.
    db.get chat_message {
      field_name = "id"
      field_value = $input.message_id
      output = [
        "id"
        "conversation_id"
        "sender_id"
        "text"
        "created_at"
        "edited_at"
      ]
    } as $message
  
    precondition ($message != null && $message.sender_id == $auth.id) {
      error_type = "notfound"
      error = "Conversa não encontrada."
    }
  
    // 3. Defesa extra: a conversa existe e a pessoa participa dela.
    db.get chat_conversation {
      field_name = "id"
      field_value = $message.conversation_id
      output = ["id", "donation_id", "donor_id", "interested_user_id"]
    } as $conversation
  
    precondition ($conversation != null && ($conversation.donor_id == $auth.id || $conversation.interested_user_id == $auth.id)) {
      error_type = "notfound"
      error = "Conversa não encontrada."
    }
  
    // 4. Doação disponível ou reservada; concluída recebe o 404 do envio.
    db.get donation {
      field_name = "id"
      field_value = $conversation.donation_id
      output = ["id", "status"]
    } as $donation
  
    precondition ($donation != null && ($donation.status == "disponível" || $donation.status == "reservada")) {
      error_type = "notfound"
      error = "Conversa não encontrada."
    }
  
    // 5. Prazo de 15 minutos desde o envio.
    var $edit_window_start {
      value = now
        |add_secs_to_timestamp:(-900|to_int)
    }
  
    precondition ($message.created_at >= $edit_window_start) {
      error_type = "inputerror"
      error = "O prazo para editar esta mensagem terminou."
    }
  
    var $current_message {
      value = $message
    }
  
    // Texto igual ao atual: não grava, não marca edição e não registra log.
    conditional {
      if ($input.message_text != $message.text) {
        db.edit chat_message {
          field_name = "id"
          field_value = $message.id
          data = {text: $input.message_text, edited_at: "now"}
          output = [
            "id"
            "conversation_id"
            "sender_id"
            "text"
            "created_at"
            "edited_at"
          ]
        } as $edited_message
      
        var.update $current_message {
          value = $edited_message
        }
      
        function.run "Quick Start/log_event" {
          input = {user_id: $auth.id, action: "chat_message_edited"}
        } as $chat_message_edited_event
      }
    }
  
    db.get user {
      field_name = "id"
      field_value = $auth.id
      output = ["name"]
    } as $sender
  
    var $sender_first_name {
      value = "Usuário"
    }
  
    conditional {
      if ($sender != null) {
        var.update $sender_first_name {
          value = (($sender.name ?? "")|trim|split:" "|first)
        }
      }
    }
  }

  response = {
    id               : $current_message.id
    conversation_id  : $current_message.conversation_id
    sender_first_name: $sender_first_name
    sent_by_me       : true
    text             : $current_message.text
    created_at       : $current_message.created_at
    edited_at        : $current_message.edited_at
  }

  guid = "GneTJ_l8hlumFL7bvVgS8zpQ3mA"
}