query "catalog/chat/conversations" verb=GET {
  api_group = "Catalog"
  auth = "user"

  input {
    int page?
    int limit?
  }

  stack {
    precondition (($input.page == null || $input.page > 0) && ($input.limit == null || $input.limit > 0)) {
      error_type = "inputerror"
      error = "A página e o limite devem ser maiores que zero."
    }
  
    var $page_number {
      value = 1
    }
  
    var $page_limit {
      value = 20
    }
  
    conditional {
      if ($input.page != null) {
        var.update $page_number {
          value = $input.page
        }
      }
    }
  
    conditional {
      if ($input.limit != null) {
        var.update $page_limit {
          value = $input.limit
        }
      }
    }
  
    conditional {
      if ($page_limit > 50) {
        var.update $page_limit {
          value = 50
        }
      }
    }
  
    db.query chat_conversation {
      where = ($db.chat_conversation.donor_id == $auth.id || $db.chat_conversation.interested_user_id == $auth.id)
      return = {type: "count"}
    } as $total_count
  
    db.query chat_conversation {
      where = ($db.chat_conversation.donor_id == $auth.id || $db.chat_conversation.interested_user_id == $auth.id)
      sort = {last_message_at: "desc", id: "desc"}
      return = {
        type  : "list"
        paging: {
          page    : $page_number
          per_page: $page_limit
          metadata: false
        }
      }
    
      output = [
        "id"
        "donation_id"
        "donor_id"
        "interested_user_id"
        "last_message_at"
        "donor_last_read_message_id"
        "interested_last_read_message_id"
      ]
    } as $conversations
  
    var $other_user_ids {
      value = []
    }
  
    var $donation_ids {
      value = []
    }
  
    foreach ($conversations) {
      each as $conversation {
        var.update $donation_ids {
          value = $donation_ids|push:$conversation.donation_id
        }
      
        conditional {
          if ($conversation.donor_id == $auth.id) {
            var.update $other_user_ids {
              value = $other_user_ids
                |push:$conversation.interested_user_id
            }
          }
        
          else {
            var.update $other_user_ids {
              value = $other_user_ids|push:$conversation.donor_id
            }
          }
        }
      }
    }
  
    var $other_users {
      value = []
    }
  
    conditional {
      if (($other_user_ids|count) > 0) {
        db.query user {
          where = $db.user.id in $other_user_ids
          return = {type: "list"}
          output = ["id", "name", "photo"]
        } as $found_users
      
        var.update $other_users {
          value = $found_users
        }
      }
    }
  
    var $donations {
      value = []
    }
  
    conditional {
      if (($donation_ids|count) > 0) {
        db.query donation {
          where = $db.donation.id in $donation_ids
          return = {type: "list"}
          output = ["id", "title", "status"]
        } as $found_donations
      
        var.update $donations {
          value = $found_donations
        }
      }
    }
  
    var $conversation_items {
      value = []
    }
  
    foreach ($conversations) {
      each as $conversation {
        var $other_user_id {
          value = $conversation.donor_id
        }
      
        // Última mensagem lida por quem consulta (nunca a da outra pessoa).
        var $my_last_read {
          value = $conversation.interested_last_read_message_id ?? 0
        }
      
        conditional {
          if ($conversation.donor_id == $auth.id) {
            var.update $other_user_id {
              value = $conversation.interested_user_id
            }
          
            var.update $my_last_read {
              value = $conversation.donor_last_read_message_id ?? 0
            }
          }
        }
      
        // Não lidas: mensagens da outra pessoa posteriores à última lida.
        db.query chat_message {
          where = ($db.chat_message.conversation_id == $conversation.id && $db.chat_message.sender_id != $auth.id && $db.chat_message.id > $my_last_read)
          return = {type: "count"}
        } as $unread_count
      
        var $other_user {
          value = $other_users|find:$$.id == $other_user_id
        }
      
        var $other_user_first_name {
          value = "Usuário"
        }
      
        conditional {
          if ($other_user != null) {
            var.update $other_user_first_name {
              value = (($other_user.name ?? "")|trim|split:" "|first)
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
      
        var $donation {
          value = $donations|find:$$.id == $conversation.donation_id
        }
      
        var $donation_title {
          value = "Doação"
        }
      
        var $donation_status {
          value = ""
        }
      
        conditional {
          if ($donation != null) {
            var.update $donation_title {
              value = $donation.title
            }
          
            var.update $donation_status {
              value = $donation.status
            }
          }
        }
      
        var.update $conversation_items {
          value = $conversation_items
            |push:```
              {
                conversation_id: $conversation.id,
                donation_id: $conversation.donation_id,
                last_message_at: $conversation.last_message_at,
                other_user_first_name: $other_user_first_name,
                other_user_photo: $other_user_photo,
                donation_title: $donation_title,
                donation_status: $donation_status,
                unread_count: $unread_count
              }
              ```
        }
      }
    }
  
    var $has_more {
      value = ($page_number * $page_limit) < $total_count
    }
  
    var $next_page {
      value = null
    }
  
    conditional {
      if ($has_more) {
        var.update $next_page {
          value = $page_number + 1
        }
      }
    }
  }

  response = {
    conversations: $conversation_items
    page         : $page_number
    limit        : $page_limit
    has_more     : $has_more
    next_page    : $next_page
  }

  guid = "v-tcgoaNzPmISQLnDJgaLh7GTQg"
}