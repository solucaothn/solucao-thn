query "auth/profile" verb=PATCH {
  api_group = "Authentication"
  auth = "user"

  input {
    text name filters=trim|min:1
    text city filters=trim|min:1
    enum state {
      values = [
        "AC"
        "AL"
        "AP"
        "AM"
        "BA"
        "CE"
        "DF"
        "ES"
        "GO"
        "MA"
        "MT"
        "MS"
        "MG"
        "PA"
        "PB"
        "PR"
        "PE"
        "PI"
        "RJ"
        "RN"
        "RS"
        "RO"
        "RR"
        "SC"
        "SP"
        "SE"
        "TO"
      ]
    }
  
    // Sempre gravado: com texto, grava (trim, até 300 caracteres); vazio,
    // nulo ou omitido grava "" e apaga o Sobre. O Xano trata "" de uma
    // entrada opcional como omitida, por isso o `?? ""` no db.edit.
    text? about? filters=trim|max:300
  }

  stack {
    db.edit user {
      field_name = "id"
      field_value = $auth.id
      data = {
        name : $input.name
        city : $input.city
        state: $input.state
        about: $input.about ?? ""
      }
    
      output = ["id", "created_at", "name", "email", "city", "state", "about"]
    } as $user
  }

  response = $user
  guid = "5sLnTADXTk-9mMY50gCQsuwcbFA"
}