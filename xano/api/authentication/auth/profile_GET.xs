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
        "email_verified"
      ]
    } as $user

    // Contadores da própria pessoa (os mesmos da donations/mine): ativas são
    // as disponíveis e as reservadas; concluídas, as concluídas.
    db.query donation {
      where = $db.donation.owner_id == $auth.id && ($db.donation.status == "disponível" || $db.donation.status == "reservada")
      return = {type: "count"}
    } as $active

    db.query donation {
      where = $db.donation.owner_id == $auth.id && $db.donation.status == "concluída"
      return = {type: "count"}
    } as $completed
  
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
    email_verified: $user.email_verified == true
    counts    : ```
      {
        active   : $active
        completed: $completed
      }
      ```
  }

  guid = "3534i_qpVQ6peS-fJTAmjDdGFn8"
}