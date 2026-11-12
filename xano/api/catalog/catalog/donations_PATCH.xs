query "catalog/donations" verb=PATCH {
  api_group = "Catalog"
  auth = "user"

  input {
    int donation_id
    int category_id
    text title filters=trim|min:1|max:100
    text description filters=trim|min:1|max:2000
    enum condition {
      values = ["Ótimo", "Bom", "Regular"]
    }
  
    enum delivery_method {
      values = ["A combinar"]
    }
  
    enum contact_preference {
      values = ["E-mail", "Chat do DoaFácil"]
    }
  }

  stack {
    db.get donation {
      field_name = "id"
      field_value = $input.donation_id
      output = ["id", "owner_id", "status"]
    } as $existing
  
    precondition ($existing != null && $existing.owner_id == $auth.id) {
      error_type = "notfound"
      error = "Doação não encontrada."
    }
  
    precondition ($existing.status != "concluída") {
      error_type = "inputerror"
      error = "Uma doação concluída não pode ser editada."
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
  
    db.edit donation {
      field_name = "id"
      field_value = $input.donation_id
      data = {
        category_id       : $input.category_id
        title             : $input.title
        description       : $input.description
        condition         : $input.condition
        delivery_method   : $input.delivery_method
        contact_preference: $input.contact_preference
        updated_at        : "now"
      }
    
      output = [
        "id"
        "updated_at"
        "category_id"
        "title"
        "description"
        "condition"
        "delivery_method"
        "contact_preference"
        "status"
      ]
    } as $donation
  }

  response = $donation
  guid = "cKz2EVIWflfxKjayz2764YvT1FM"
}