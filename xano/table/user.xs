// Stores user information and allows the user to authenticate  against
table user {
  auth = true

  schema {
    int id
    timestamp created_at?=now
    text name filters=trim
    email? email filters=trim|lower
    password? password filters=min:8|minAlpha:1|minDigit:1
    text city filters=trim
    text state filters=trim
  
    // Texto público “Sobre” do perfil (opcional, até 300 caracteres,
    // validado no PATCH auth/profile).
    text? about? filters=trim
  
    // Foto de perfil pública (opcional), enviada por POST auth/profile/photo.
    image? photo?
  
    // The role of the user within their company (e.g., 'admin', 'member').
    enum role? {
      values = ["admin", "member"]
    }
  
    object password_reset? {
      schema {
        password token?
        timestamp? expiration?
        bool used?
      }
    }

    // E-mail confirmado pelo código do cadastro: gravado como verdadeiro só
    // pelo auth/signup_verify (e, uma vez, pela marcação inicial das contas
    // confirmadas). Nenhum endpoint aceita este campo do cliente. Linhas
    // antigas podem ler nulo: as respostas usam `== true`.
    bool email_verified?=false
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree", field: [{name: "created_at", op: "desc"}]}
    {type: "btree|unique", field: [{name: "email", op: "asc"}]}
  ]

  tags = ["xano:quick-start"]
  guid = "CpxeWpeZb9Sct0BEtmo8Ch8YU_I"
}