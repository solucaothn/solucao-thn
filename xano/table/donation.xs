// A donation is owned by the authenticated user who created it.
table donation {
  auth = false

  schema {
    int id
    timestamp created_at?=now
    timestamp updated_at?=now
    int owner_id
    int category_id
    text title filters=trim|min:1
    text description? filters=trim
    enum status? {
      values = ["disponível", "reservada", "concluída"]
    }
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree", field: [{name: "owner_id", op: "asc"}]}
    {type: "btree", field: [{name: "category_id", op: "asc"}]}
    {type: "btree", field: [{name: "status", op: "asc"}]}
  ]

  guid = "HzbNLi_lqmaCvHEH0q5DKPZ8QWQ"
}