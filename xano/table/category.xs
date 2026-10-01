// Categories are maintained directly by an operator in the Xano workspace.
table category {
  auth = false

  schema {
    int id
    timestamp created_at?=now
    text name filters=trim
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree|unique", field: [{name: "name", op: "asc"}]}
  ]

  guid = "e7Dv3ECphkEJyB2JxLfa379u4Lk"
}