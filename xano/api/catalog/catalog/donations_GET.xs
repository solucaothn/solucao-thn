query "catalog/donations" verb=GET {
  api_group = "Catalog"

  input {
    text search? filters=trim
    int category_id?
  }

  stack {
    conditional {
      if ($input.category_id != null) {
        db.get category {
          field_name = "id"
          field_value = $input.category_id
          output = ["id"]
        } as $category
      
        precondition ($category != null) {
          error_type = "inputerror"
          error = "Categoria inválida."
        }
      }
    }
  
    conditional {
      if ($input.search != null && $input.search != "" && $input.category_id != null) {
        db.query donation {
          where = ($db.donation.category_id == $input.category_id && (($db.donation.title|contains:$input.search) || ($db.donation.description != null && ($db.donation.description|contains:$input.search))))
          sort = {created_at: "desc"}
          return = {type: "list"}
          output = [
            "id"
            "created_at"
            "updated_at"
            "category_id"
            "title"
            "description"
            "status"
          ]
        } as $donations
      }
    }
  
    conditional {
      if ($input.search != null && $input.search != "" && $input.category_id == null) {
        db.query donation {
          where = (($db.donation.title|contains:$input.search) || ($db.donation.description != null && ($db.donation.description|contains:$input.search)))
          sort = {created_at: "desc"}
          return = {type: "list"}
          output = [
            "id"
            "created_at"
            "updated_at"
            "category_id"
            "title"
            "description"
            "status"
          ]
        } as $donations
      }
    }
  
    conditional {
      if (($input.search == null || $input.search == "") && $input.category_id != null) {
        db.query donation {
          where = $db.donation.category_id == $input.category_id
          sort = {created_at: "desc"}
          return = {type: "list"}
          output = [
            "id"
            "created_at"
            "updated_at"
            "category_id"
            "title"
            "description"
            "status"
          ]
        } as $donations
      }
    }
  
    conditional {
      if (($input.search == null || $input.search == "") && $input.category_id == null) {
        db.query donation {
          sort = {created_at: "desc"}
          return = {type: "list"}
          output = [
            "id"
            "created_at"
            "updated_at"
            "category_id"
            "title"
            "description"
            "status"
          ]
        } as $donations
      }
    }
  }

  response = $donations
  guid = "7D0eEWAr9mWN8KAKZVB6eLZSP5o"
}