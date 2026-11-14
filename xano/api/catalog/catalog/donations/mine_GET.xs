query "catalog/donations/mine" verb=GET {
  api_group = "Catalog"
  auth = "user"

  input {
    int page?=1
  }

  stack {
    db.get user {
      field_name = "id"
      field_value = $auth.id
      output = ["name", "email", "about", "photo", "email_verified"]
    } as $owner
  
    var $owner_photo {
      value = null
    }
  
    conditional {
      if ($owner != null && $owner.photo != null) {
        conditional {
          if ($env.PUBLIC_BASE_URL == null || $env.PUBLIC_BASE_URL == "") {
            throw {
              name = "ConfigurationError"
              value = "PUBLIC_BASE_URL não está configurada."
            }
          }
        }
      
        var.update $owner_photo {
          value = $env.PUBLIC_BASE_URL ~ $owner.photo.path
        }
      }
    }
  
    var $first_name {
      value = (($owner.name ?? "")|trim|split:" "|first)
    }
  
    var $page {
      value = $input.page
    }
  
    conditional {
      if ($input.page < 1) {
        var.update $page {
          value = 1
        }
      }
    }
  
    db.query donation {
      where = $db.donation.owner_id == $auth.id && ($db.donation.status == "disponível" || $db.donation.status == "reservada")
      return = {type: "count"}
    } as $active
  
    db.query donation {
      where = $db.donation.owner_id == $auth.id && $db.donation.status == "concluída"
      return = {type: "count"}
    } as $completed
  
    db.query donation {
      where = $db.donation.owner_id == $auth.id
      return = {type: "count"}
    } as $total
  
    var $page_total {
      value = $total
        |to_decimal
        |divide:6
        |ceil
        |to_int
    }
  
    db.query donation {
      where = $db.donation.owner_id == $auth.id
      sort = {created_at: "desc"}
      return = {
        type  : "list"
        paging: {page: $page, per_page: 6, metadata: false}
      }
    
      output = ["id", "created_at", "title", "photo", "condition", "status"]
    } as $donations
  
    var $items {
      value = []
    }
  
    foreach ($donations) {
      each as $item {
        var $photo_url {
          value = null
        }
      
        conditional {
          if ($item.photo != null) {
            conditional {
              if ($env.PUBLIC_BASE_URL == null || $env.PUBLIC_BASE_URL == "") {
                throw {
                  name = "ConfigurationError"
                  value = "PUBLIC_BASE_URL não está configurada."
                }
              }
            }
          
            var.update $photo_url {
              value = $env.PUBLIC_BASE_URL ~ $item.photo.path
            }
          }
        }
      
        var.update $items {
          value = $items
            |push:```
              {
                id: $item.id,
                created_at: $item.created_at,
                title: $item.title,
                photo: $photo_url,
                condition: $item.condition,
                status: $item.status
              }
              ```
        }
      }
    }
  }

  response = {
    owner     : ```
      {
        first_name: $first_name
        email     : $owner.email
        about     : $owner.about
        photo     : $owner_photo
        email_verified: $owner.email_verified == true
      }
      ```
    counts    : ```
      {
        active   : $active
        completed: $completed
      }
      ```
    items     : $items
    page      : $page
    per_page  : 6
    total     : $total
    page_total: $page_total
  }

  guid = "izhhWxuMHSUH0Y8ItxV2XhfM6HU"
}