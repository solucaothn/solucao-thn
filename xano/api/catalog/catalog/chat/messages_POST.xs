query "catalog/chat/messages" verb=POST {
  api_group = "Catalog"
  auth = "user"

  input {
    int conversation_id
    text? message_text? filters=trim
  }

  stack {
    precondition ($input.message_text != null && ($input.message_text|strlen) > 0 && ($input.message_text|strlen) <= 1000) {
      error_type = "inputerror"
      error = "A mensagem deve conter entre 1 e 1000 caracteres."
    }
  
    var $message {
      value = null
    }
  
    db.transaction {
      stack {
        db.get chat_conversation {
          field_name = "id"
          field_value = $input.conversation_id
          output = ["id", "donation_id", "donor_id", "interested_user_id"]
        } as $conversation
      
        precondition ($conversation != null && ($conversation.donor_id == $auth.id || $conversation.interested_user_id == $auth.id)) {
          error_type = "notfound"
          error = "Conversa não encontrada."
        }
      
        db.get donation {
          field_name = "id"
          field_value = $conversation.donation_id
          output = ["id", "status"]
        } as $donation
      
        precondition ($donation != null && ($donation.status == "disponível" || $donation.status == "reservada")) {
          error_type = "notfound"
          error = "Conversa não encontrada."
        }
      
        var $rate_window_start {
          value = now
            |add_secs_to_timestamp:(-60|to_int)
        }
      
        db.query chat_message {
          where = ($db.chat_message.sender_id == $auth.id && $db.chat_message.created_at >= $rate_window_start)
          return = {type: "count"}
        } as $recent_message_count
      
        precondition ($recent_message_count < 10) {
          error_type = "toomanyrequests"
          error = "Limite de mensagens atingido. Tente novamente em instantes."
        }
      
        db.add chat_message {
          data = {
            conversation_id: $conversation.id
            sender_id      : $auth.id
            text           : $input.message_text
          }
        
          output = [
            "id"
            "conversation_id"
            "sender_id"
            "text"
            "created_at"
            "edited_at"
          ]
        } as $message
      
        db.edit chat_conversation {
          field_name = "id"
          field_value = $conversation.id
          data = {last_message_at: "now"}
        } as $updated_conversation
      
        function.run "Quick Start/log_event" {
          input = {user_id: $auth.id, action: "chat_message_sent"}
        } as $chat_message_event
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
    id               : $message.id
    conversation_id  : $message.conversation_id
    sender_first_name: $sender_first_name
    sent_by_me       : true
    text             : $message.text
    created_at       : $message.created_at
    edited_at        : $message.edited_at
  }

  guid = "xj3dbcReD9PMSUm3CVazuR3KHzA"
}