query "catalog/donations/publish" verb=POST {
  api_group = "Catalog"
  auth = "user"

  input {
    int category_id
    text title filters=trim|min:1
    text description? filters=trim
    enum condition {
      values = ["Ótimo", "Bom", "Regular"]
    }
    enum delivery_method {
      values = ["Retirada", "Entrega", "A combinar"]
    }
    enum contact_preference {
      values = ["WhatsApp", "E-mail", "Chat do DoaFácil"]
    }
    file[]? photos?
  }

  stack {
    precondition ($input.photos == null || ($input.photos|count) <= 5) {
      error_type = "inputerror"
      error = "Selecione no máximo cinco fotos."
    }

    db.get category {
      field_name = "id"
      field_value = $input.category_id
      output = ["id", "name"]
    } as $category

    precondition ($category != null) {
      error_type = "inputerror"
      error = "Categoria inválida."
    }

    db.get user {
      field_name = "id"
      field_value = $auth.id
      output = ["id", "city", "state"]
    } as $owner

    precondition ($owner != null && $owner.city != "" && $owner.state != "") {
      error_type = "inputerror"
      error = "Complete a cidade e o estado no seu perfil antes de publicar."
    }

    var $uploaded_photos {
      value = []
    }

    var $photo_position {
      value = 0
    }

    var $cover_photo {
      value = null
    }

    conditional {
      if ($input.photos != null && ($input.photos|count) > 0) {
        foreach ($input.photos) {
          each as $file {
            storage.create_image {
              value    = $file
              access   = "public"
              filename = $file.name
            } as $stored_photo

            var.update $photo_position {
              value = $photo_position + 1
            }

            var.update $uploaded_photos {
              value = $uploaded_photos|push:{file: $stored_photo, position: $photo_position}
            }

            conditional {
              if ($photo_position == 1) {
                var.update $cover_photo {
                  value = $stored_photo
                }
              }
            }
          }
        }
      }
    }

    db.transaction {
      stack {
        db.add donation {
          data = {
            owner_id           : $auth.id
            category_id        : $input.category_id
            title              : $input.title
            description        : $input.description
            photo              : $cover_photo
            city               : $owner.city
            state              : $owner.state
            condition          : $input.condition
            delivery_method    : $input.delivery_method
            contact_preference : $input.contact_preference
            status             : "disponível"
          }

          output = [
            "id"
            "created_at"
            "updated_at"
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

        foreach ($uploaded_photos) {
          each as $uploaded_photo {
            db.add donation_photo {
              data = {
                donation_id: $donation.id
                position   : $uploaded_photo.position
                photo      : $uploaded_photo.file
              }
            }
          }
        }
      }
    }
  }

  response = {
    donation: $donation
    photos  : $uploaded_photos
  }
  guid = "8cK4Vejm3ius0GMv4YZhslS6U6A"
}
