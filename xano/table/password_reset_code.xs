table password_reset_code {
  auth = false

  schema {
    int id
    timestamp created_at?=now
    int user_id {
      table = "user"
    }
    password code_hash?
    timestamp code_expires_at?
    int attempts?=0
    bool code_used?=false
    text reset_token_hash?
    timestamp reset_token_expires_at?
    bool reset_token_used?=true
    timestamp last_sent_at?
    timestamp sent_at_2?
    timestamp sent_at_3?
    timestamp sent_at_4?
    timestamp sent_at_5?
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree|unique", field: [{name: "user_id"}]}
    {type: "btree", field: [{name: "reset_token_hash"}]}
  ]
}
