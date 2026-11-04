function "Signup/send_confirmation_code" {
  input {
    email recipient {
      sensitive = true
    }
    text code {
      sensitive = true
    }
  }

  stack {
    var $message {
      value = "Seu código de confirmação de cadastro é " ~ $input.code ~ ". Ele é válido por 10 minutos."
    }

    var $payload {
      value = {
        personalizations: [
          {
            to: [{email: $input.recipient}]
          }
        ]
        from            : {email: $env.SENDGRID_FROM_EMAIL}
        subject         : "Confirmação de cadastro no DoaFácil"
        content         : [
          {
            type : "text/plain"
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
        "Content-Type: application/json"
        "Authorization: Bearer " ~ $env.SENDGRID_API_KEY
      ]

      timeout = 30
    } as $sendgrid_response

    precondition ($sendgrid_response.response.status >= 200 && $sendgrid_response.response.status < 300) {
      error = "Não foi possível enviar o código de confirmação."
    }
  }

  response = {success: true}
  guid = "sf386kwzgUOrpR3Q33FqJKFHU_0"
}
