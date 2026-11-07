query "catalog/donations" verb=DELETE {
  api_group = "Catalog"
  auth = "user"

  input {
    int donation_id
  }

  stack {
    db.transaction {
      stack {
        db.get donation {
          field_name = "id"
          field_value = $input.donation_id
          output = ["id", "owner_id"]
        } as $existing
      
        precondition ($existing != null) {
          error_type = "notfound"
          error = "Doação não encontrada."
        }
      
        precondition ($existing.owner_id == $auth.id) {
          error_type = "accessdenied"
          error = "Você não pode excluir esta doação."
        }
      
        db.query chat_conversation {
          where = $db.chat_conversation.donation_id == $input.donation_id
          return = {type: "list"}
          output = ["id"]
        } as $conversations
      
        foreach ($conversations) {
          each as $conversation {
            db.bulk.delete chat_message {
              where = $db.chat_message.conversation_id == $conversation.id
            } as $deleted_messages
          }
        }
      
        db.bulk.delete chat_conversation {
          where = $db.chat_conversation.donation_id == $input.donation_id
        } as $deleted_conversations
      
        db.del donation {
          field_name = "id"
          field_value = $input.donation_id
        }
      }
    }
  }

  response = {deleted: true, donation_id: $input.donation_id}
  guid = "cx1nJnH1koCQANBMO9sVI5LrViw"
}