table chat_message {
  auth = false

  schema {
    int id
    timestamp created_at?=now
    int conversation_id {
      table = "chat_conversation"
    }
  
    int sender_id {
      table = "user"
    }
  
    text text filters=trim
  
    // Horário da última edição; vazio enquanto a mensagem não foi editada.
    timestamp edited_at?
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {
      type : "btree"
      field: [{name: "conversation_id"}, {name: "id"}]
    }
    {
      type : "btree"
      field: [{name: "sender_id"}, {name: "created_at", op: "desc"}]
    }
  ]

  guid = "garkBTBvuO66CwyhPrmt9vWzHPs"
}