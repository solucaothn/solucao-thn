query "catalog/donations/detail" verb=GET {
  api_group = "Catalog"

  input {
    int donation_id
  }

  stack {
    db.get donation {
      field_name = "id"
      field_value = $input.donation_id
      output = [
        "id"
        "owner_id"
        "category_id"
        "title"
        "description"
        "photo"
        "city"
        "state"
        "condition"
        "delivery_method"
        "contact_preference"
        "status"
      ]
    } as $donation

    precondition ($donation != null) {
      error_type = "notfound"
      error = "Doação não encontrada."
    }

    precondition ($donation.status == "disponível") {
      error_type = "notfound"
      error = "Doação não encontrada."
    }

    db.get category {
      field_name = "id"
      field_value = $donation.category_id
      output = ["name"]
    } as $category

    db.get user {
      field_name = "id"
      field_value = $donation.owner_id
      output = ["name"]
    } as $owner

    precondition ($category != null && $owner != null) {
      error_type = "notfound"
      error = "Doação não encontrada."
    }

    var $donor_first_name {
      value = (($owner.name ?? "")|trim|split:" "|first)
    }

    var $photo_urls {
      value = []
    }

    var $photo_paths {
      value = []
    }

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

        var.update $photo_urls {
          value = $photo_urls|push:($env.PUBLIC_BASE_URL ~ $donation.photo.path)
        }

        var.update $photo_paths {
          value = $photo_paths|push:$donation.photo.path
        }
      }
    }

    db.query donation_photo {
      where = $db.donation_photo.donation_id == $input.donation_id
      sort = {position: "asc"}
      return = {type: "list"}
      output = ["position", "photo"]
    } as $additional_photos

    foreach ($additional_photos) {
      each as $additional_photo {
        conditional {
          if ($additional_photo.photo != null) {
            conditional {
              if (($photo_paths|find:$$ == $additional_photo.photo.path) == null) {
                conditional {
                  if ($env.PUBLIC_BASE_URL == null || $env.PUBLIC_BASE_URL == "") {
                    throw {
                      name = "ConfigurationError"
                      value = "PUBLIC_BASE_URL não está configurada."
                    }
                  }
                }

                var.update $photo_urls {
                  value = $photo_urls|push:($env.PUBLIC_BASE_URL ~ $additional_photo.photo.path)
                }

                var.update $photo_paths {
                  value = $photo_paths|push:$additional_photo.photo.path
                }
              }
            }
          }
        }
      }
    }
  }

  response = {
    id: $donation.id
    title: $donation.title
    description: $donation.description
    condition: $donation.condition
    category: $category.name
    city: $donation.city
    state: $donation.state
    delivery_method: $donation.delivery_method
    contact_preference: $donation.contact_preference
    photos: $photo_urls
    donor_first_name: $donor_first_name
  }
  guid = "4fMeGBKAefzsbLsPbgpmV6tA7FM"
}
