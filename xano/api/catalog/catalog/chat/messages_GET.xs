query "catalog/chat/messages" verb=GET {
  api_group = "Catalog"
  auth = "user"

  input {
    int conversation_id
    int after_message_id?
    int limit? filters=min:1
  }

  stack {
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
      output = ["id", "donation_id", "donor_id", "interested_user_id"]
    } as $conversation
  
    precondition ($conversation != null && ($conversation.donor_id == $auth.id || $conversation.interested_user_id == $auth.id)) {
      error_type = "notfound"
      error = "Conversa não encontrada."
    }
  
    db.get donation {
      field_name = "id"
      field_value = $conversation.donation_id
      output = ["id"]
    } as $donation
  
    precondition ($donation != null) {
      error_type = "notfound"
      error = "Conversa não encontrada."
    }
  
    db.query chat_message {
      where = ($db.chat_message.conversation_id == $conversation.id && ($input.after_message_id == null || $db.chat_message.id > $input.after_message_id))
      return = {type: "count"}
    } as $remaining_count
  
    db.query chat_message {
      where = ($db.chat_message.conversation_id == $conversation.id && ($input.after_message_id == null || $db.chat_message.id > $input.after_message_id))
      sort = {id: "asc"}
      return = {
        type: "list"
        paging: {page: 1, per_page: $page_limit, metadata: false}
      }
      output = ["id", "conversation_id", "sender_id", "text", "created_at"]
    } as $messages
  
    db.get user {
      field_name = "id"
      field_value = $conversation.donor_id
      output = ["name"]
    } as $donor_user

    db.get user {
      field_name = "id"
      field_value = $conversation.interested_user_id
      output = ["name"]
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

    var $messages_with_names {
      value = []
    }

    var $last_message_id {
      value = null
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

        var.update $messages_with_names {
          value = $messages_with_names
            |push:```
              {
                id: $message.id,
                conversation_id: $message.conversation_id,
                sender_first_name: $sender_first_name,
                text: $message.text,
                created_at: $message.created_at
              }
              ```
        }

        var.update $last_message_id {
          value = $message.id
        }
      }
    }

    var $has_more {
      value = $remaining_count > $page_limit
    }

    var $next_after_message_id {
      value = null
    }

    conditional {
      if ($has_more && $last_message_id != null) {
        var.update $next_after_message_id {
          value = $last_message_id
        }
      }
    }
  }

  response = {
    messages              : $messages_with_names
    has_more              : $has_more
    next_after_message_id: $next_after_message_id
  }
  guid = "_vyIXcGn_BV6HB8-w8xgjvBdiAw"
}
