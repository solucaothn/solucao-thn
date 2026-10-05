query "catalog/donations/recent" verb=GET {
  api_group = "Catalog"

  input {
  }

  stack {
    db.query donation {
      where = $db.donation.status == "disponível"
      sort = {created_at: "desc"}
      return = {
        type: "list"
        paging: {page: 1, per_page: 4, metadata: false}
      }
      output = ["id", "created_at", "title", "photo", "condition"]
    } as $donations

    var $cards { value = [] }

    foreach ($donations) {
      each as $donation {
        var $photo_url { value = null }

        conditional {
          if ($donation.photo != null) {
            conditional {
              if ($env.PUBLIC_BASE_URL == null || $env.PUBLIC_BASE_URL == "") {
                throw {
                  name = "ConfigurationError"
                  value = "PUBLIC_BASE_URL não está configurada."
                }
              }
            }

            var.update $photo_url {
              value = $env.PUBLIC_BASE_URL ~ $donation.photo.path
            }
          }
        }

        var.update $cards {
          value = $cards|push:{
            id: $donation.id,
            created_at: $donation.created_at,
            title: $donation.title,
            photo: $photo_url,
            condition: $donation.condition
          }
        }
      }
    }
  }

  response = $cards
}
