query "auth/profile" verb=GET {
  api_group = "Authentication"
  auth = "user"

  input {
  }

  stack {
    db.get user {
      field_name = "id"
      field_value = $auth.id
      output = [
        "id"
        "created_at"
        "name"
        "email"
        "city"
        "state"
        "about"
        "photo"
      ]
    } as $user
  
    var $photo_url {
      value = null
    }
  
    conditional {
      if ($user != null && $user.photo != null) {
        conditional {
          if ($env.PUBLIC_BASE_URL == null || $env.PUBLIC_BASE_URL == "") {
            throw {
              name = "ConfigurationError"
              value = "PUBLIC_BASE_URL não está configurada."
            }
          }
        }
      
        var.update $photo_url {
          value = $env.PUBLIC_BASE_URL ~ $user.photo.path
        }
      }
    }
  }

  response = {
    id        : $user.id
    created_at: $user.created_at
    name      : $user.name
    email     : $user.email
    city      : $user.city
    state     : $user.state
    about     : $user.about
    photo     : $photo_url
  }

  guid = "3534i_qpVQ6peS-fJTAmjDdGFn8"
}