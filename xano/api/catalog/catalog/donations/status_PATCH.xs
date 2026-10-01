query "catalog/donations/status" verb=PATCH {
  api_group = "Catalog"
  auth = "user"

  input {
    int donation_id
    enum status {
      values = ["disponível", "reservada", "concluída"]
    }
  }

  stack {
    db.get donation {
      field_name = "id"
      field_value = $input.donation_id
      output = ["id", "owner_id", "status"]
    } as $existing
  
    precondition ($existing != null) {
      error_type = "notfound"
      error = "Doação não encontrada."
    }
  
    precondition ($existing.owner_id == $auth.id) {
      error_type = "accessdenied"
      error = "Você não pode alterar esta doação."
    }
  
    conditional {
      if ($existing.status == "concluída" && $input.status != "concluída") {
        throw {
          name = "inputerror"
          value = "Uma doação concluída não pode voltar para outro status."
        }
      }
    }
  
    conditional {
      if ($existing.status == "reservada" && $input.status == "disponível") {
        throw {
          name = "inputerror"
          value = "Uma doação reservada não pode voltar para disponível."
        }
      }
    }
  
    db.edit donation {
      field_name = "id"
      field_value = $input.donation_id
      data = {status: $input.status, updated_at: "now"}
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
  guid = "Z4rhkXd0PP2EqG7WLhrikQQa_II"
}