query "auth/profile" verb=GET {
  api_group = "Authentication"
  auth = "user"

  input {
  }

  stack {
    db.get user {
      field_name = "id"
      field_value = $auth.id
      output = ["id", "created_at", "name", "email", "city", "state"]
    } as $user
  }

  response = $user
  guid = "3534i_qpVQ6peS-fJTAmjDdGFn8"
}