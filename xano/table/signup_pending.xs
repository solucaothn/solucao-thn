table signup_pending {
  auth = false

  schema {
    int id
    timestamp created_at?=now
    text name filters=trim|min:1
    email email filters=trim|lower
    text city filters=trim|min:1
    text state filters=trim|min:1
    password code_hash?
    timestamp code_expires_at?
    int attempts?=0
    bool code_used?=false
    timestamp pending_expires_at?
    timestamp last_sent_at?
    timestamp sent_at_2?
    timestamp sent_at_3?
    timestamp sent_at_4?
    timestamp sent_at_5?
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree|unique", field: [{name: "email"}]}
  ]
  guid = "1gCmQOb76Dqm67gu89rTctRWi1A"
}
