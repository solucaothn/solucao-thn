query "catalog/donations" verb=DELETE {
  api_group = "Catalog"
  auth = "user"

  input {
    int donation_id
  }

  stack {
    db.get donation {
      field_name = "id"
      field_value = $input.donation_id
      output = ["id", "owner_id"]
    } as $existing
  
    precondition ($existing != null) {
      error_type = "notfound"
      error = "Doação não encontrada."
    }
  
    precondition ($existing.owner_id == $auth.id) {
      error_type = "accessdenied"
      error = "Você não pode excluir esta doação."
    }
  
    db.del donation {
      field_name = "id"
      field_value = $input.donation_id
    }
  }

  response = {deleted: true, donation_id: $input.donation_id}
  guid = "cx1nJnH1koCQANBMO9sVI5LrViw"
}