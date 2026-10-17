query "reset/request_code" verb=POST {
  api_group = "Authentication"

  input {
    email email filters=trim|lower
  }

  stack {
    var $response_data {
      value = {success: true}
    }

    db.query user {
      where = $db.user.email == $input.email
      return = {type: "single"}
      output = ["id", "email"]
    } as $user

    conditional {
      if ($user != null) {
        security.random_number {
          min = 100000
          max = 999999
        } as $code_number

        var $code {
          value = $code_number|to_text
        }

        var $hour_ago {
          value = now|add_secs_to_timestamp:(-3600|to_int)
        }

        var $cooldown_border {
          value = now|add_secs_to_timestamp:(-30|to_int)
        }

        var $send_allowed {
          value = false
        }

        db.transaction {
          stack {
            db.query password_reset_code {
              where = $db.password_reset_code.user_id == $user.id
              return = {type: "single"}
            } as $reset_state

            conditional {
              if ($reset_state == null) {
                db.add password_reset_code {
                  data = {
                    user_id: $user.id,
                    code_hash: $code,
                    code_expires_at: now|add_secs_to_timestamp:(600|to_int),
                    attempts: 0,
                    code_used: false,
                    reset_token_hash: null,
                    reset_token_expires_at: null,
                    reset_token_used: true,
                    last_sent_at: now,
                    sent_at_2: null,
                    sent_at_3: null,
                    sent_at_4: null,
                    sent_at_5: null
                  }
                } as $created_reset_state

                function.run "Quick Start/log_event" {
                  input = {user_id: $user.id, action: "password_reset_requested"}
                } as $request_event

                var.update $send_allowed {
                  value = true
                }
              }
              else {
                var $recent_sends {
                  value = 0
                }

                conditional {
                  if ($reset_state.last_sent_at != null && $reset_state.last_sent_at > $hour_ago) {
                    var.update $recent_sends {
                      value = $recent_sends + 1
                    }
                  }
                }

                conditional {
                  if ($reset_state.sent_at_2 != null && $reset_state.sent_at_2 > $hour_ago) {
                    var.update $recent_sends {
                      value = $recent_sends + 1
                    }
                  }
                }

                conditional {
                  if ($reset_state.sent_at_3 != null && $reset_state.sent_at_3 > $hour_ago) {
                    var.update $recent_sends {
                      value = $recent_sends + 1
                    }
                  }
                }

                conditional {
                  if ($reset_state.sent_at_4 != null && $reset_state.sent_at_4 > $hour_ago) {
                    var.update $recent_sends {
                      value = $recent_sends + 1
                    }
                  }
                }

                conditional {
                  if ($reset_state.sent_at_5 != null && $reset_state.sent_at_5 > $hour_ago) {
                    var.update $recent_sends {
                      value = $recent_sends + 1
                    }
                  }
                }

                conditional {
                  if (($reset_state.last_sent_at == null || $reset_state.last_sent_at <= $cooldown_border) && $recent_sends < 5) {
                    db.edit password_reset_code {
                      field_name = "id"
                      field_value = $reset_state.id
                      data = {
                        code_hash: $code,
                        code_expires_at: now|add_secs_to_timestamp:(600|to_int),
                        attempts: 0,
                        code_used: false,
                        reset_token_hash: null,
                        reset_token_expires_at: null,
                        reset_token_used: true,
                        sent_at_5: $reset_state.sent_at_4,
                        sent_at_4: $reset_state.sent_at_3,
                        sent_at_3: $reset_state.sent_at_2,
                        sent_at_2: $reset_state.last_sent_at,
                        last_sent_at: now
                      }
                    } as $updated_reset_state

                    function.run "Quick Start/log_event" {
                      input = {user_id: $user.id, action: "password_reset_requested"}
                    } as $request_event

                    var.update $send_allowed {
                      value = true
                    }
                  }
                }
              }
            }
          }
        }

        conditional {
          if ($send_allowed) {
            var $send_succeeded {
              value = false
            }

            try_catch {
              try {
                function.run "Password Recovery/send_recovery_code" {
                  input = {recipient: $user.email, code: $code}
                } as $delivery

                var.update $send_succeeded {
                  value = true
                }
              }
              catch {
                var $failure_logged {
                  value = false
                }

                try_catch {
                  try {
                    function.run "Quick Start/log_event" {
                      input = {user_id: $user.id, action: "password_reset_delivery_failed"}
                    } as $delivery_failure_event

                    var.update $failure_logged {
                      value = true
                    }
                  }
                  catch {
                    var.update $failure_logged {
                      value = false
                    }
                  }
                }

                var.update $send_succeeded {
                  value = false
                }
              }
            }

            conditional {
              if ($send_succeeded == false) {
                try_catch {
                  try {
                    db.query password_reset_code {
                      where = $db.password_reset_code.user_id == $user.id
                      return = {type: "single"}
                    } as $failed_delivery_state

                    conditional {
                      if ($failed_delivery_state != null) {
                        db.edit password_reset_code {
                          field_name = "id"
                          field_value = $failed_delivery_state.id
                          data = {code_used: true}
                        } as $invalidated_code
                      }
                    }
                  }
                  catch {
                    var $invalidation_failed {
                      value = true
                    }
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
}
