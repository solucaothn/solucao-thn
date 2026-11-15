## ADDED Requirements

### Requirement: Busca pública de doações disponíveis
O sistema SHALL permitir, sem autenticação, buscar doações disponíveis com filtros opcionais de texto, categoria e UF, em páginas de 12, da mais nova para a mais antiga, retornando só os dados dos cartões e os totais da paginação.

#### Scenario: Busca sem filtros
- **WHEN** uma pessoa consulta a busca sem filtros e sem token
- **THEN** o sistema retorna a primeira página das doações com status disponível, ordenadas da mais nova para a mais antiga
- **AND** a resposta contém, para cada doação, somente id, data de criação, título, URL pública da foto (ou nulo) e condição, além de `page`, `per_page`, `total` e `page_total`

#### Scenario: Filtros combinados
- **WHEN** a consulta informa qualquer combinação de texto, categoria e UF
- **THEN** o sistema retorna só as doações disponíveis da categoria e da UF informadas cujo título ou descrição contém o texto, sem diferenciar maiúsculas de minúsculas
- **AND** os totais refletem só as doações filtradas

#### Scenario: Nenhuma doação de outros status
- **WHEN** existem doações reservadas ou concluídas que atendem aos filtros
- **THEN** elas MUST NOT aparecer nos resultados nem nos totais

#### Scenario: Página fora do intervalo
- **WHEN** a consulta pede uma página maior que o total de páginas
- **THEN** o sistema retorna a lista vazia com os totais corretos

#### Scenario: Entrada inválida
- **WHEN** a página é menor que 1 ou a UF não tem duas letras
- **THEN** o sistema rejeita a consulta com erro de entrada, sem retornar doações

#### Scenario: Sem dados pessoais
- **WHEN** o sistema responde à busca
- **THEN** a resposta MUST NOT conter dono, nome, e-mail, cidade, descrição ou outros dados pessoais
