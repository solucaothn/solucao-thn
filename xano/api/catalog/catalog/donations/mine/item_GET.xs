query "catalog/donations/mine/item" verb=GET {
  api_group = "Catalog"
  auth = "user"

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
        "title"
        "description"
        "category_id"
        "condition"
        "delivery_method"
        "contact_preference"
        "status"
      ]
    } as $donation
  
    precondition ($donation != null && $donation.owner_id == $auth.id) {
      error_type = "notfound"
      error = "Doação não encontrada."
    }
  }

  response = {
    id                : $donation.id
    title             : $donation.title
    description       : $donation.description
    category_id       : $donation.category_id
    condition         : $donation.condition
    delivery_method   : $donation.delivery_method
    contact_preference: $donation.contact_preference
    status            : $donation.status
  }

  guid = "WE3sf0aQvN3zW2KwxaIY-5NEI1o"
}