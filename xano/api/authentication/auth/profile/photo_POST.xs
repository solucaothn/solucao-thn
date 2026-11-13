// Envia a foto de perfil da própria pessoa (a pessoa vem sempre do token).
// Aceita JPG, PNG, GIF ou WEBP (pelo mime do arquivo guardado) de até 5 MB;
// substitui a foto anterior e apaga o arquivo antigo do armazenamento.
query "auth/profile/photo" verb=POST {
  api_group = "Authentication"
  auth = "user"

  input {
    // Precisa ser `file?`: só assim o Xano preenche o .path do upload.
    file? photo
  }

  stack {
    precondition ($input.photo != null) {
      error_type = "inputerror"
      error = "Escolha uma foto."
    }
  
    db.get user {
      field_name = "id"
      field_value = $auth.id
      output = ["id", "photo"]
    } as $current
  
    // Guarda com storage.create_image, com os mesmos parâmetros do
    // publish_POST.xs (o plano gratuito do Xano não tem create_attachment).
    // O create_image recusa arquivos que não são imagem com erro (500); o
    // try_catch transforma isso no 400 de formato. Nenhuma propriedade da
    // entrada é conferida antes de guardar.
    var $stored_photo {
      value = null
    }
  
    var $stored_ok {
      value = true
    }
  
    try_catch {
      try {
        storage.create_image {
          value = $input.photo
          access = "public"
          filename = $input.photo.name
        } as $created_photo
      
        var.update $stored_photo {
          value = $created_photo
        }
      }
    
      catch {
        var.update $stored_ok {
          value = false
        }
      }
    }
  
    precondition ($stored_ok && $stored_photo != null) {
      error_type = "inputerror"
      error = "Envie uma imagem JPG, PNG, GIF ou WEBP."
    }
  
    // Depois de guardar: tipo pelo .mime e tamanho pelo .size do objeto
    // guardado (propriedades que a doc confirma). Fora das regras, o arquivo
    // novo é apagado e a resposta é 400.
    var $valid_type {
      value = $stored_photo.mime == "image/jpeg" || $stored_photo.mime == "image/png" || $stored_photo.mime == "image/gif" || $stored_photo.mime == "image/webp"
    }
  
    var $valid_size {
      value = $stored_photo.size <= 5242880
    }
  
    conditional {
      if ($valid_type == false || $valid_size == false) {
        storage.delete_file {
          pathname = $stored_photo.path
        }
      }
    }
  
    precondition ($valid_type) {
      error_type = "inputerror"
      error = "Envie uma imagem JPG, PNG, GIF ou WEBP."
    }
  
    precondition ($valid_size) {
      error_type = "inputerror"
      error = "A foto pode ter no máximo 5 MB."
    }
  
    conditional {
      if ($env.PUBLIC_BASE_URL == null || $env.PUBLIC_BASE_URL == "") {
        throw {
          name = "ConfigurationError"
          value = "PUBLIC_BASE_URL não está configurada."
        }
      }
    }
  
    db.edit user {
      field_name = "id"
      field_value = $auth.id
      data = {photo: $stored_photo}
      output = ["id"]
    } as $updated
  
    // Arquivo da foto anterior apagado do armazenamento.
    conditional {
      if ($current != null && $current.photo != null) {
        storage.delete_file {
          pathname = $current.photo.path
        }
      }
    }
  }

  response = {photo: $env.PUBLIC_BASE_URL ~ $stored_photo.path}
  guid = "zg2NVqsaRsxoYbwROPSIVL8HUCg"
}