query "catalog/donations/contact-email" verb=GET {
  api_group = "Catalog"
  auth = "user"

  input {
    int donation_id
  }

  stack {
    function.run "Quick Start/log_event" {
      input = {
        user_id: $auth.id
        action : "donation_contact_email"
      }
    } as $event_log
  
    db.get donation {
      field_name = "id"
      field_value = $input.donation_id
      output = ["owner_id", "status", "contact_preference"]
    } as $donation
  
    precondition ($donation != null) {
      error_type = "notfound"
      error = "Doação não encontrada."
    }
  
    precondition ($donation.status == "disponível") {
      error_type = "notfound"
      error = "Doação não encontrada."
    }
  
    precondition ($donation.owner_id != $auth.id) {
      error_type = "accessdenied"
      error = "Esta é a sua doação."
    }
  
    precondition ($donation.contact_preference == "E-mail") {
      error_type = "notfound"
      error = "Doação não encontrada."
    }
  
    db.get user {
      field_name = "id"
      field_value = $donation.owner_id
      output = ["email"]
    } as $owner
  
    precondition ($owner != null && $owner.email != null) {
      error_type = "notfound"
      error = "Doação não encontrada."
    }
  }

  response = {
    email: $owner.email
  }
  guid = "Pafl9c535tv4_-PvNUsoZLyF33g"
}
