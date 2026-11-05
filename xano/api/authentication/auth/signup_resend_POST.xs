query "auth/signup_resend" verb=POST {
  api_group = "Authentication"

  input {
    text email? filters=trim|lower {
      sensitive = true
    }
  }

  stack {
    var $response_data {
      value = {success: true}
    }

    var $send_allowed {
      value = false
    }

    var $pending_id {
      value = 0
    }

    var $hour_ago {
      value = now|add_secs_to_timestamp:(-3600|to_int)
    }

    var $cooldown_border {
      value = now|add_secs_to_timestamp:(-30|to_int)
    }

    security.random_number {
      min = 100000
      max = 999999
    } as $resend_code_number

    var $resend_code {
      value = $resend_code_number|to_text
    }

    db.query user {
      where = $db.user.email == $input.email
      return = {type: "single"}
      output = ["id"]
    } as $existing_user

    conditional {
      if ($input.email != null && ($input.email|strlen) >= 5 && $existing_user == null) {
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
                  if ($pending != null) {
                    var $recent_sends {
                      value = 0
                    }

                    conditional {
                      if ($pending.last_sent_at != null && $pending.last_sent_at > $hour_ago) {
                        var.update $recent_sends {
                          value = $recent_sends + 1
                        }
                      }
                    }

                    conditional {
                      if ($pending.sent_at_2 != null && $pending.sent_at_2 > $hour_ago) {
                        var.update $recent_sends {
                          value = $recent_sends + 1
                        }
                      }
                    }

                    conditional {
                      if ($pending.sent_at_3 != null && $pending.sent_at_3 > $hour_ago) {
                        var.update $recent_sends {
                          value = $recent_sends + 1
                        }
                      }
                    }

                    conditional {
                      if ($pending.sent_at_4 != null && $pending.sent_at_4 > $hour_ago) {
                        var.update $recent_sends {
                          value = $recent_sends + 1
                        }
                      }
                    }

                    conditional {
                      if ($pending.sent_at_5 != null && $pending.sent_at_5 > $hour_ago) {
                        var.update $recent_sends {
                          value = $recent_sends + 1
                        }
                      }
                    }

                    conditional {
                      if (($pending.last_sent_at == null || $pending.last_sent_at <= $cooldown_border) && $recent_sends < 5) {
                        db.edit signup_pending {
                          field_name = "id"
                          field_value = $pending.id
                          data = {
                            code_hash          : $resend_code
                            code_expires_at    : now|add_secs_to_timestamp:(600|to_int)
                            attempts            : 0
                            code_used           : false
                            pending_expires_at : now|add_secs_to_timestamp:(86400|to_int)
                            sent_at_5          : $pending.sent_at_4
                            sent_at_4          : $pending.sent_at_3
                            sent_at_3          : $pending.sent_at_2
                            sent_at_2          : $pending.last_sent_at
                            last_sent_at       : now
                          }
                        } as $updated_pending

                        var.update $pending_id {
                          value = $updated_pending.id
                        }

                        var.update $send_allowed {
                          value = true
                        }
                      }
                    }
                  }
                }
              }
            }
          }

          catch {
            var.update $send_allowed {
              value = false
            }
          }
        }
      }
    }

    conditional {
      if ($send_allowed) {
        try_catch {
          try {
            function.run "Signup/send_confirmation_code" {
              input = {recipient: $input.email, code: $resend_code}
            } as $delivery
          }

          catch {
            db.edit signup_pending {
              field_name = "id"
              field_value = $pending_id
              data = {code_used: true}
            } as $invalidated_code
          }
        }
      }
    }
  }

  response = $response_data
  guid = "iawZ1vS7mhCCscVlkV0FleP2FxQ"
}
