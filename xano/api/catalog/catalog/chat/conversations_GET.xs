query "catalog/chat/conversations" verb=GET {
  api_group = "Catalog"
  auth = "user"

  input {
    int page? filters=min:1
    int limit? filters=min:1
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
        type: "list"
        paging: {page: $page_number, per_page: $page_limit, metadata: false}
      }
      output = ["id", "donation_id", "donor_id", "interested_user_id", "last_message_at"]
    } as $conversations
  
    var $other_user_ids {
      value = []
    }

    foreach ($conversations) {
      each as $conversation {
        conditional {
          if ($conversation.donor_id == $auth.id) {
            var.update $other_user_ids {
              value = $other_user_ids|push:$conversation.interested_user_id
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

    db.query user {
      where = $db.user.id in $other_user_ids
      return = {type: "list"}
      output = ["id", "name"]
    } as $other_users

    var $conversation_items {
      value = []
    }

    foreach ($conversations) {
      each as $conversation {
        var $other_user_id {
          value = $conversation.donor_id
        }

        conditional {
          if ($conversation.donor_id == $auth.id) {
            var.update $other_user_id {
              value = $conversation.interested_user_id
            }
          }
        }

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

        var.update $conversation_items {
          value = $conversation_items
            |push:```
              {
                conversation_id: $conversation.id,
                donation_id: $conversation.donation_id,
                last_message_at: $conversation.last_message_at,
                other_user_first_name: $other_user_first_name
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
}
