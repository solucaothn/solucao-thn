query "catalog/donations/donor" verb=GET {
  api_group = "Catalog"

  input {
    int donation_id
    int page?=1
  }

  stack {
    db.get donation {
      field_name = "id"
      field_value = $input.donation_id
      output = ["id", "owner_id", "city", "state", "status"]
    } as $donation
  
    precondition ($donation != null) {
      error_type = "notfound"
      error = "Doação não encontrada."
    }
  
    precondition ($donation.status == "disponível") {
      error_type = "notfound"
      error = "Doação não encontrada."
    }
  
    db.get user {
      field_name = "id"
      field_value = $donation.owner_id
      output = ["name", "created_at", "about", "photo", "email_verified"]
    } as $owner
  
    precondition ($owner != null) {
      error_type = "notfound"
      error = "Doação não encontrada."
    }
  
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
  
    var $member_since {
      value = $owner.created_at
        |format_timestamp:"Y-m":"America/Sao_Paulo"
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
  
    // Contadores públicos de quem doa (os mesmos da donations/mine), separados
    // do $total da lista, que conta só as disponíveis.
    db.query donation {
      where = $db.donation.owner_id == $donation.owner_id && ($db.donation.status == "disponível" || $db.donation.status == "reservada")
      return = {type: "count"}
    } as $active

    db.query donation {
      where = $db.donation.owner_id == $donation.owner_id && $db.donation.status == "concluída"
      return = {type: "count"}
    } as $completed

    db.query donation {
      where = $db.donation.owner_id == $donation.owner_id && $db.donation.status == "disponível"
      return = {type: "count"}
    } as $total
  
    var $page_total {
      value = $total
        |to_decimal
        |divide:12
        |ceil
        |to_int
    }
  
    db.query donation {
      where = $db.donation.owner_id == $donation.owner_id && $db.donation.status == "disponível"
      sort = {created_at: "desc"}
      return = {
        type  : "list"
        paging: {page: $page, per_page: 12, metadata: false}
      }
    
      output = ["id", "created_at", "title", "photo", "condition"]
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
                condition: $item.condition
              }
              ```
        }
      }
    }
  }

  response = {
    donor     : ```
      {
        first_name  : $first_name
        city        : $donation.city
        state       : $donation.state
        member_since: $member_since
        about       : $owner.about
        photo       : $owner_photo
        email_verified: $owner.email_verified == true
        counts      : {active: $active, completed: $completed}
      }
      ```
    items     : $items
    page      : $page
    per_page  : 12
    total     : $total
    page_total: $page_total
  }

  guid = "q-TbCTVvSSA-q3ugqr5t17qbHpo"
}