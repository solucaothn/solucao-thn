query "auth/profile" verb=PATCH {
  api_group = "Authentication"
  auth = "user"

  input {
    text name filters=trim|min:1
    text city filters=trim|min:1
    text state filters=trim|min:1
  }

  stack {
    db.edit user {
      field_name = "id"
      field_value = $auth.id
      data = {
        name : $input.name
        city : $input.city
        state: $input.state
      }
    
      output = ["id", "created_at", "name", "email", "city", "state"]
    } as $user
  }

  response = $user
  guid = "5sLnTADXTk-9mMY50gCQsuwcbFA"
}