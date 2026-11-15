// Busca pública de doações disponíveis (change explorar-categorias).
// Filtros opcionais: q (título ou descrição, sem diferenciar maiúsculas),
// category_id e state (UF, comparada em maiúsculas). 12 por página, da mais
// nova para a mais antiga. Responde só os dados dos cartões e os totais.
query "catalog/donations/search" verb=GET {
  api_group = "Catalog"

  input {
    text q? filters=trim
    int category_id?
    text state? filters=trim|upper
    int page?=1
  }

  stack {
    precondition ($input.page >= 1) {
      error_type = "inputerror"
      error = "Página inválida."
    }

    // UF vazia vale como não informada; informada, precisa ter 2 letras.
    var $state {
      value = null
    }

    conditional {
      if ($input.state != null && $input.state != "") {
        precondition (($input.state|strlen) == 2) {
          error_type = "inputerror"
          error = "UF inválida."
        }

        var.update $state {
          value = $input.state
        }
      }
    }

    // Texto em minúsculas; vazio vale como não informado.
    var $search {
      value = ""
    }

    conditional {
      if ($input.q != null) {
        var.update $search {
          value = $input.q|to_lower
        }
      }
    }

    var $total {
      value = 0
    }

    var $donations {
      value = []
    }

    conditional {
      if ($search == "") {
        db.query donation {
          where = $db.donation.status == "disponível" && $db.donation.category_id ==? $input.category_id && ($db.donation.state|to_upper) ==? $state
          return = {type: "count"}
        } as $count_all

        db.query donation {
          where = $db.donation.status == "disponível" && $db.donation.category_id ==? $input.category_id && ($db.donation.state|to_upper) ==? $state
          sort = {created_at: "desc"}
          return = {
            type  : "list"
            paging: {page: $input.page, per_page: 12, metadata: false}
          }

          output = ["id", "created_at", "title", "photo", "condition"]
        } as $page_all

        var.update $total {
          value = $count_all
        }

        var.update $donations {
          value = $page_all
        }
      }

      else {
        db.query donation {
          where = $db.donation.status == "disponível" && $db.donation.category_id ==? $input.category_id && ($db.donation.state|to_upper) ==? $state && ((($db.donation.title|to_lower) includes $search) || (($db.donation.description|to_lower) includes $search))
          return = {type: "count"}
        } as $count_text

        db.query donation {
          where = $db.donation.status == "disponível" && $db.donation.category_id ==? $input.category_id && ($db.donation.state|to_upper) ==? $state && ((($db.donation.title|to_lower) includes $search) || (($db.donation.description|to_lower) includes $search))
          sort = {created_at: "desc"}
          return = {
            type  : "list"
            paging: {page: $input.page, per_page: 12, metadata: false}
          }

          output = ["id", "created_at", "title", "photo", "condition"]
        } as $page_text

        var.update $total {
          value = $count_text
        }

        var.update $donations {
          value = $page_text
        }
      }
    }

    var $page_total {
      value = $total
        |to_decimal
        |divide:12
        |ceil
        |to_int
    }

    // Cartões: a foto vira a URL pública, como no catalog/donations/recent.
    var $items {
      value = []
    }

    foreach ($donations) {
      each as $donation {
        var $photo_url {
          value = null
        }

        conditional {
          if ($donation.photo != null) {
            conditional {
              if ($env.PUBLIC_BASE_URL == null || $env.PUBLIC_BASE_URL == "") {
                throw {
                  name = "ConfigurationError"
                  value = "PUBLIC_BASE_URL não está configurada."
                }
              }
            }

            var.update $photo_url {
              value = $env.PUBLIC_BASE_URL ~ $donation.photo.path
            }
          }
        }

        var.update $items {
          value = $items
            |push:```
              {
                id: $donation.id,
                created_at: $donation.created_at,
                title: $donation.title,
                photo: $photo_url,
                condition: $donation.condition
              }
              ```
        }
      }
    }
  }

  response = {
    items     : $items
    page      : $input.page
    per_page  : 12
    total     : $total
    page_total: $page_total
  }
  guid = "2DCqtyp6LImUEr6uRXgaf3nzbpM"
}
