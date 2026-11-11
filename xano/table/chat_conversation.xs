table chat_conversation {
  auth = false

  schema {
    int id
    timestamp created_at?=now
    int donation_id {
      table = "donation"
    }
  
    int donor_id {
      table = "user"
    }
  
    int interested_user_id {
      table = "user"
    }
  
    timestamp last_message_at?=now
  
    // Última mensagem lida por cada participante (0 = nenhuma).
    int donor_last_read_message_id?
  
    int interested_last_read_message_id?
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {
      type : "btree|unique"
      field: [{name: "donation_id"}, {name: "interested_user_id"}]
    }
    {
      type : "btree"
      field: [{name: "donor_id"}, {name: "last_message_at", op: "desc"}]
    }
    {
      type : "btree"
      field: [
        {name: "interested_user_id"}
        {name: "last_message_at", op: "desc"}
      ]
    }
  ]

  guid = "czOeNUu5FPVd8pdjzigtH3eQmuY"
}