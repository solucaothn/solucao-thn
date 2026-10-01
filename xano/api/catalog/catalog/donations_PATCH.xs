query "catalog/donations" verb=PATCH {
  api_group = "Catalog"
  auth = "user"

  input {
    int donation_id
    int category_id
    text title filters=trim|min:1
    text description? filters=trim
  }

  stack {
    db.get donation {
      field_name = "id"
      field_value = $input.donation_id
      output = ["id", "owner_id", "category_id", "title", "description", "status"]
    } as $existing
  
    precondition ($existing != null) {
      error_type = "notfound"
      error = "Doação não encontrada."
    }
  
    precondition ($existing.owner_id == $auth.id) {
      error_type = "accessdenied"
      error = "Você não pode editar esta doação."
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
        category_id: $input.category_id
        title      : $input.title
        description: $input.description
        updated_at : "now"
      }
    
      output = [
        "id"
        "created_at"
        "updated_at"
        "category_id"
        "title"
        "description"
        "status"
      ]
    } as $donation
  }

  response = $donation
  guid = "cKz2EVIWflfxKjayz2764YvT1FM"
}