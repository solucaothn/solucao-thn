// Remove a foto de perfil da própria pessoa (a pessoa vem sempre do token) e
// apaga o arquivo do armazenamento. Sem foto, responde 200 do mesmo jeito.
query "auth/profile/photo" verb=DELETE {
  api_group = "Authentication"
  auth = "user"

  input {
  }

  stack {
    db.get user {
      field_name = "id"
      field_value = $auth.id
      output = ["id", "photo"]
    } as $current
  
    db.edit user {
      field_name = "id"
      field_value = $auth.id
      data = {photo: null}
      output = ["id"]
    } as $updated
  
    conditional {
      if ($current != null && $current.photo != null) {
        storage.delete_file {
          pathname = $current.photo.path
        }
      }
    }
  }

  response = {photo: null}
  guid = "bOuUm83kecK6ENuEw8HCQxNnUY0"
}