query "catalog/donations/count" verb=GET {
  api_group = "Catalog"

  input {
  }

  stack {
    db.query donation {
      where = $db.donation.status == "disponível"
      return = {type: "count"}
    } as $count

    // Doações concluídas: a estatística “Pessoas alcançadas” da home
    // (change landing-nova). Só a contagem, sem dados das doações.
    db.query donation {
      where = $db.donation.status == "concluída"
      return = {type: "count"}
    } as $completed
  }

  response = {count: $count, completed: $completed}
  guid = "YEXKnQBYZADVz16JATEzR0T7mPs"
}