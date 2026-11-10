query "catalog/chat/conversations/start" verb=POST {
  api_group = "Catalog"
  auth = "user"

  input {
    int donation_id
  }

  stack {
    db.get donation {
      field_name = "id"
      field_value = $input.donation_id
      output = ["id", "owner_id", "status", "contact_preference"]
    } as $donation
  
    precondition ($donation != null) {
      error_type = "notfound"
      error = "Conversa não encontrada."
    }
  
    db.query chat_conversation {
      where = ($db.chat_conversation.donation_id == $input.donation_id && $db.chat_conversation.interested_user_id == $auth.id)
      return = {type: "single"}
      output = ["id", "donation_id", "donor_id", "interested_user_id", "last_message_at"]
    } as $conversation
  
    var $created_new {
      value = false
    }
  
    conditional {
      if ($conversation == null) {
        precondition ($donation.status == "disponível" && $donation.owner_id != $auth.id && $donation.contact_preference == "Chat do DoaFácil") {
          error_type = "notfound"
          error = "Conversa não encontrada."
        }
      
        try_catch {
          try {
            db.transaction {
              stack {
                db.add chat_conversation {
                  data = {
                    donation_id       : $donation.id
                    donor_id          : $donation.owner_id
                    interested_user_id: $auth.id
                    last_message_at   : "now"
                  }
                  output = ["id", "donation_id", "donor_id", "interested_user_id", "last_message_at"]
                } as $created_conversation
              
                var.update $conversation {
                  value = $created_conversation
                }
              
                var.update $created_new {
                  value = true
                }
              
                function.run "Quick Start/log_event" {
                  input = {
                    user_id: $auth.id
                    action : "chat_started"
                  }
                } as $chat_started_event
              }
            }
          }
          catch {
            db.query chat_conversation {
              where = ($db.chat_conversation.donation_id == $input.donation_id && $db.chat_conversation.interested_user_id == $auth.id)
              return = {type: "single"}
              output = ["id", "donation_id", "donor_id", "interested_user_id", "last_message_at"]
            } as $existing_conversation
          
            precondition ($existing_conversation != null) {
              error_type = "notfound"
              error = "Conversa não encontrada."
            }

            var.update $conversation {
              value = $existing_conversation
            }
          }
        }
      }
    }
  
    db.get user {
      field_name = "id"
      field_value = $conversation.donor_id
      output = ["name"]
    } as $donor

    var $donor_first_name {
      value = "Usuário"
    }

    conditional {
      if ($donor != null) {
        var.update $donor_first_name {
          value = (($donor.name ?? "")|trim|split:" "|first)
        }
      }
    }
  }

  response = {
    conversation_id      : $conversation.id
    donation_id          : $conversation.donation_id
    last_message_at      : $conversation.last_message_at
    other_user_first_name: $donor_first_name
  }
  guid = "glP_tB6dJlsTKyRbf5SADE-yHXo"
}
