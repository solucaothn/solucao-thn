query "catalog/categories" verb=GET {
  api_group = "Catalog"

  input {
  }

  stack {
    db.query category {
      return = {type: "list"}
      output = ["id", "name"]
    } as $categories
  }

  response = $categories
  guid = "DlAbl5vc3qkk9iwW3Qz4jr5y0YQ"
}