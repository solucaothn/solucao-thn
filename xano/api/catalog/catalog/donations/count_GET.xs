query "catalog/donations/count" verb=GET {
  api_group = "Catalog"

  input {
  }

  stack {
    db.query donation {
      where = $db.donation.status == "disponível"
      return = {type: "count"}
    } as $count
  }

  response = {count: $count}
}
