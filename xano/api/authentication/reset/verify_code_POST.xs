query "reset/verify_code" verb=POST {
  api_group = "Authentication"

  input {
    email email filters=trim|lower
    text code filters=trim
  }

  stack {
    var $response_data {
      value = {success: false}
    }

    db.query user {
      where = $db.user.email == $input.email
      return = {type: "single"}
      output = ["id"]
    } as $user

    security.random_bytes {
      length = 32
    } as $token_bytes

    var $reset_token {
      value = $token_bytes|bin2hex
    }

    var $reset_token_hash {
      value = $reset_token|sha256
    }

    conditional {
      if ($user != null) {
        db.transaction {
          stack {
            db.query password_reset_code {
              where = $db.password_reset_code.user_id == $user.id
              return = {type: "single"}
            } as $reset_state

            conditional {
              if ($reset_state != null && $reset_state.code_used == false && $reset_state.code_expires_at > now && $reset_state.attempts < 5) {
                security.check_password {
                  text_password = $input.code
                  hash_password = $reset_state.code_hash
                } as $code_matches

                conditional {
                  if ($code_matches) {
                    db.edit password_reset_code {
                      field_name = "id"
                      field_value = $reset_state.id
                      data = {
                        code_used: true,
                        reset_token_hash: $reset_token_hash,
                        reset_token_expires_at: now|add_secs_to_timestamp:(600|to_int),
                        reset_token_used: false
                      }
                    } as $verified_reset_state

                    function.run "Quick Start/log_event" {
                      input = {user_id: $user.id, action: "password_reset_verified"}
                    } as $verify_event

                    var.update $response_data {
                      value = {success: true, reset_token: $reset_token}
                    }
                  }
                  else {
                    var $next_attempts {
                      value = $reset_state.attempts + 1
                    }

                    db.edit password_reset_code {
                      field_name = "id"
                      field_value = $reset_state.id
                      data = {
                        attempts: $next_attempts,
                        code_used: ($next_attempts >= 5)
                      }
                    } as $failed_reset_state
                  }
                }
              }
            }
          }
        }
      }
    }
  }

  response = $response_data
  guid = "9V0qiz1UR06UiZyL1DCtVXirdjc"
}
