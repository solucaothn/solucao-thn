query "catalog/donations" verb=POST {
  api_group = "Catalog"
  auth = "user"

  input {
    int category_id
    text title filters=trim|min:1
    text description? filters=trim
  }

  stack {
    db.get category {
      field_name = "id"
      field_value = $input.category_id
      output = ["id", "name"]
    } as $category
  
    precondition ($category != null) {
      error_type = "inputerror"
      error = "Categoria inválida."
    }
  
    db.add donation {
      data = {
        owner_id   : $auth.id
        category_id: $input.category_id
        title      : $input.title
        description: $input.description
        status     : "disponível"
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
  guid = "D1NlrAz3wKXXGwxtND7wXIT4TAc"
}