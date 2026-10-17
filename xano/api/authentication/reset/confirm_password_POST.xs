query "reset/confirm_password" verb=POST {
  api_group = "Authentication"

  input {
    text reset_token filters=trim
    text password
    text password_confirmation
  }

  stack {
    var $response_data {
      value = {success: false}
    }

    var $password_length {
      value = $input.password|strlen
    }

    var $has_password_letter {
      value = "/[A-Za-z]/"|regex_matches:$input.password
    }

    var $has_password_digit {
      value = "/[0-9]/"|regex_matches:$input.password
    }

    var $reset_token_hash {
      value = $input.reset_token|sha256
    }

    conditional {
      if ($password_length >= 8 && $has_password_letter && $has_password_digit && $input.password == $input.password_confirmation) {
        db.transaction {
          stack {
            db.query password_reset_code {
              where = $db.password_reset_code.reset_token_hash == $reset_token_hash && $db.password_reset_code.reset_token_used == false && $db.password_reset_code.reset_token_expires_at > now
              return = {type: "single"}
            } as $reset_state

            conditional {
              if ($reset_state != null) {
                db.edit user {
                  field_name = "id"
                  field_value = $reset_state.user_id
                  data = {password: $input.password}
                } as $updated_user

                db.edit password_reset_code {
                  field_name = "id"
                  field_value = $reset_state.id
                  data = {
                    code_used: true,
                    reset_token_used: true
                  }
                } as $completed_reset_state

                function.run "Quick Start/log_event" {
                  input = {user_id: $reset_state.user_id, action: "password_reset_completed"}
                } as $completion_event

                var.update $response_data {
                  value = {success: true}
                }
              }
            }
          }
        }
      }
    }
  }

  response = $response_data
  guid = "e49ij53KjX2bw1Lap6uubkFGfYM"
}
