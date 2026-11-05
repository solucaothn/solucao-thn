query "auth/signup_verify" verb=POST {
  api_group = "Authentication"

  input {
    text email? filters=trim|lower {
      sensitive = true
    }
    text code? filters=trim {
      sensitive = true
    }
    text password? {
      sensitive = true
    }
  }

  stack {
    var $response_data {
      value = {success: false}
    }

    var $email_valid {
      value = false
    }

    var $code_format_valid {
      value = false
    }

    var $password_length_valid {
      value = false
    }

    var $password_letter_valid {
      value = false
    }

    var $password_digit_valid {
      value = false
    }

    var $password_valid {
      value = false
    }

    conditional {
      if ($input.email != null) {
        var.update $email_valid {
          value = ($input.email|strlen) >= 5
        }
      }
    }

    conditional {
      if ($input.code != null) {
        var.update $code_format_valid {
          value = ($input.code|strlen) == 6
        }
      }
    }

    conditional {
      if ($input.password != null) {
        conditional {
          if ("/^.{8,}$/"|regex_matches:$input.password) {
            var.update $password_length_valid {
              value = true
            }
          }
        }

        conditional {
          if ("/[A-Za-z]/"|regex_matches:$input.password) {
            var.update $password_letter_valid {
              value = true
            }
          }
        }

        conditional {
          if ("/[0-9]/"|regex_matches:$input.password) {
            var.update $password_digit_valid {
              value = true
            }
          }
        }

        conditional {
          if ($password_length_valid && $password_letter_valid && $password_digit_valid) {
            var.update $password_valid {
              value = true
            }
          }
        }
      }
    }

    conditional {
      if ($email_valid && $code_format_valid && $password_valid) {
        try_catch {
          try {
            db.transaction {
              stack {
                db.query signup_pending {
                  where = $db.signup_pending.email == $input.email
                  return = {type: "single"}
                } as $pending

                conditional {
                  if ($pending != null && $pending.pending_expires_at <= now) {
                    db.del signup_pending {
                      field_name = "id"
                      field_value = $pending.id
                    }

                    var.update $pending {
                      value = null
                    }
                  }
                }

                conditional {
                  if ($pending != null && $pending.code_used == false && $pending.attempts < 5 && $pending.code_expires_at > now) {
                    security.check_password {
                      text_password = $input.code
                      hash_password = $pending.code_hash
                    } as $code_matches

                    conditional {
                      if ($code_matches) {
                        db.query user {
                          where = $db.user.email == $input.email
                          return = {type: "single"}
                          output = ["id"]
                        } as $existing_user

                        conditional {
                          if ($existing_user == null) {
                            db.add user {
                              data = {
                                created_at: "now"
                                name      : $pending.name
                                email     : $pending.email|to_lower
                                password  : $input.password
                                city      : $pending.city
                                state     : $pending.state
                                role      : "member"
                              }
                            } as $created_user

                            db.del signup_pending {
                              field_name = "id"
                              field_value = $pending.id
                            }

                            function.run "Quick Start/log_event" {
                              input = {
                                user_id: $created_user.id
                                action : "signup_confirmed"
                              }
                            } as $signup_event

                            var.update $response_data {
                              value = {success: true}
                            }
                          }
                        }
                      }

                      else {
                        var $next_attempt {
                          value = $pending.attempts + 1
                        }

                        db.edit signup_pending {
                          field_name = "id"
                          field_value = $pending.id
                          data = {
                            attempts : $next_attempt
                            code_used: $next_attempt >= 5
                          }
                        } as $updated_attempts
                      }
                    }
                  }
                }
              }
            }
          }

          catch {
            var.update $response_data {
              value = {success: false}
            }
          }
        }
      }
    }
  }

  response = $response_data
  guid = "rYf6elUYYEsefZdmZxnEYjJS004"
}
