function "Password Recovery/send_recovery_code" {
  input {
    email recipient
    text code
  }

  stack {
    var $message {
      value = "Seu código de recuperação de senha é " ~ $input.code ~ ". Ele é válido por 10 minutos."
    }

    var $payload {
      value = {
        personalizations: [
          {
            to: [{email: $input.recipient}]
          }
        ],
        from: {email: $env.SENDGRID_FROM_EMAIL},
        subject: "Recuperação de senha do DoaFácil",
        content: [
          {
            type: "text/plain",
            value: $message
          }
        ]
      }
    }

    api.request {
      url = "https://api.sendgrid.com/v3/mail/send"
      method = "POST"
      params = $payload
      headers = [
        "Content-Type: application/json",
        "Authorization: Bearer " ~ $env.SENDGRID_API_KEY
      ]
      timeout = 30
    } as $sendgrid_response

    precondition ($sendgrid_response.response.status >= 200 && $sendgrid_response.response.status < 300) {
      error_type = "standard"
      error = "Não foi possível enviar a mensagem de recuperação."
    }
  }

  response = {success: true}
}
