## Purpose

Disponibilizar um catálogo de doações que permita a usuários autenticados
publicar e manter seus itens, organizá-los por categoria e acompanhar o status
do ciclo de doação com autorização aplicada no backend.

## ADDED Requirements

### Requirement: Cadastro de doação pelo proprietário
O sistema SHALL permitir que um usuário autenticado cadastre uma doação com os campos obrigatórios do item e uma categoria válida, associando o registro ao usuário autenticado e iniciando-o como disponível.

#### Scenario: Cadastro válido
- **WHEN** um usuário autenticado informa os dados obrigatórios e seleciona uma categoria existente
- **THEN** o sistema cria a doação associada ao usuário autenticado com status `disponível`

#### Scenario: Cadastro sem autenticação
- **WHEN** um visitante não autenticado tenta cadastrar uma doação
- **THEN** o backend rejeita a operação e não persiste nenhum registro

#### Scenario: Categoria inexistente
- **WHEN** um usuário tenta cadastrar uma doação com categoria inexistente ou inválida
- **THEN** o backend rejeita a operação e informa que a categoria não é válida

### Requirement: Edição e exclusão pelo proprietário
O sistema SHALL permitir que somente o dono autenticado edite ou exclua sua doação, mantendo os dados e o status consistentes com as regras do catálogo.

#### Scenario: Proprietário edita a própria doação
- **WHEN** o dono autenticado altera os dados ou a categoria de uma doação própria
- **THEN** o backend valida os campos, persiste as alterações e retorna a doação atualizada

#### Scenario: Usuário tenta editar doação de terceiro
- **WHEN** um usuário autenticado tenta alterar uma doação que não lhe pertence
- **THEN** o backend rejeita a operação com erro de autorização e não altera o registro

#### Scenario: Proprietário exclui a própria doação
- **WHEN** o dono autenticado solicita a exclusão de uma doação própria
- **THEN** o backend remove a doação e confirma a operação

#### Scenario: Usuário tenta excluir doação de terceiro
- **WHEN** um usuário autenticado tenta excluir uma doação que não lhe pertence
- **THEN** o backend rejeita a operação com erro de autorização e preserva o registro

### Requirement: Categorias disponíveis no backend
O sistema SHALL manter categorias persistidas no backend e SHALL disponibilizá-las para seleção nas doações. Nesta change, criação, edição e exclusão de categorias ocorrerão diretamente no workspace Xano por um operador humano, fora da API pública do catálogo.

#### Scenario: Operador mantém categorias no Xano
- **WHEN** um operador humano autorizado mantém categorias diretamente nas ferramentas do workspace Xano
- **THEN** as categorias persistidas ficam disponíveis para consulta e associação às doações

#### Scenario: API não oferece gestão de categoria
- **WHEN** um cliente tenta criar, editar ou excluir categoria por um endpoint do catálogo
- **THEN** a operação não está disponível nesta change e nenhuma categoria é alterada

#### Scenario: Categoria usada por doação
- **WHEN** o operador tenta excluir diretamente no Xano uma categoria associada a uma doação
- **THEN** o backend rejeita a exclusão ou exige uma política explícita que preserve a integridade das doações

### Requirement: Status do ciclo da doação
O sistema SHALL controlar o status de cada doação usando somente `disponível`, `reservada` ou `concluída`, rejeitando valores fora do conjunto permitido.

#### Scenario: Doação inicia disponível
- **WHEN** uma nova doação é cadastrada
- **THEN** seu status inicial é `disponível`

#### Scenario: Atualização para status válido
- **WHEN** o proprietário autenticado solicita um status permitido para sua doação
- **THEN** o backend valida a transição e persiste o novo status

#### Scenario: Status inválido
- **WHEN** uma requisição informa um status fora do conjunto permitido
- **THEN** o backend rejeita a alteração e mantém o status anterior

### Requirement: Listagem básica de doações
O sistema SHALL disponibilizar uma listagem básica de doações persistidas, retornando somente campos previstos para o catálogo e permitindo identificar sua categoria e status.

#### Scenario: Usuário consulta o catálogo
- **WHEN** um visitante ou usuário autenticado solicita a listagem básica
- **THEN** o sistema retorna doações do catálogo com dados do item, categoria e status, sem expor dados privados do proprietário

#### Scenario: Listagem sem resultados
- **WHEN** não existem doações que atendam à consulta básica
- **THEN** o sistema retorna uma lista vazia com resposta bem-formada

#### Scenario: Exclusão da listagem
- **WHEN** uma doação é excluída pelo proprietário
- **THEN** ela deixa de aparecer nas listagens subsequentes

### Requirement: Autorização centralizada no Xano
O sistema SHALL validar no backend a autenticação e a propriedade da doação em cada operação sensível, sem tratar o estado do Reflex como prova de permissão.

#### Scenario: Cliente manipula identificador do dono
- **WHEN** uma requisição tenta informar outro proprietário no payload ou na URL
- **THEN** o backend ignora ou rejeita o identificador informado e usa a identidade autenticada para decidir a autorização

#### Scenario: Token inválido em operação protegida
- **WHEN** uma requisição protegida usa token expirado, inválido ou ausente
- **THEN** o backend rejeita a operação e não expõe nem altera dados protegidos
