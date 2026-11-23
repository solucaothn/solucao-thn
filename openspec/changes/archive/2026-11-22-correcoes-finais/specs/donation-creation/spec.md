## MODIFIED Requirements

### Requirement: Detalhamento e categoria da doação
O sistema MUST permitir informar título do objeto, descrição, uma categoria existente e uma condição física entre “Ótimo”, “Bom” e “Regular”. O campo de título MUST apresentar o exemplo “Ex.: Carrinho de brinquedo”. O título, a categoria, a descrição e a condição MUST ser validados antes da publicação; a categoria MUST existir no Xano, e a lista exibida no wizard MUST mostrar todas as categorias válidas retornadas pelo serviço de catálogo, sem exclusões por nome.

#### Scenario: Seleção de categoria disponível
- **WHEN** o formulário carrega as categorias ou o doador seleciona uma categoria
- **THEN** as opções apresentadas MUST corresponder a todas as categorias válidas retornadas pelo serviço de catálogo, inclusive “Móveis”
- **AND** uma categoria inexistente MUST ser rejeitada pelo backend

#### Scenario: Categoria que deixou de existir
- **WHEN** o serviço de catálogo não retorna mais uma categoria, como “Alimentos”
- **THEN** ela MUST NOT aparecer nas opções, e o formulário MUST continuar funcionando com as demais
- **AND** itens da resposta sem id inteiro ou sem nome MUST ser ignorados, sem quebrar a lista

#### Scenario: Exemplo do nome do item
- **WHEN** o doador visualiza o campo “Nome do item” na primeira etapa
- **THEN** o campo MUST mostrar o placeholder “Ex.: Carrinho de brinquedo”

#### Scenario: Condição selecionada no detalhamento
- **WHEN** o doador informa a condição do objeto
- **THEN** essa informação MUST ser coletada na segunda etapa e persistida com um dos três valores permitidos

## ADDED Requirements

### Requirement: Limites e valores aceitos pelo endpoint de publicação
O endpoint de publicação MUST recusar, com HTTP 400 e sem criar doação, fotos ou arquivos: título com mais de 100 caracteres ou descrição com mais de 2000, depois de tirar os espaços das pontas; entrega diferente de “A combinar”; e preferência de contato diferente de “E-mail” e “Chat do DoaFácil”. São os mesmos limites e valores aceitos pela edição de doação.

#### Scenario: Título longo demais
- **WHEN** uma requisição autenticada envia um título com 101 caracteres
- **THEN** o backend MUST responder HTTP 400 por causa do título, antes de validar as fotos
- **AND** MUST NOT criar doação, linhas de fotos ou arquivos de imagem

#### Scenario: Título no limite
- **WHEN** uma requisição autenticada envia um título com exatamente 100 caracteres e os demais campos válidos
- **THEN** o título MUST ser aceito

#### Scenario: Descrição longa demais
- **WHEN** uma requisição autenticada envia uma descrição com 2001 caracteres
- **THEN** o backend MUST responder HTTP 400 sem criar doação

#### Scenario: Entrega ou contato fora das opções do site
- **WHEN** uma requisição autenticada envia a entrega “Retirada” ou “Entrega”, ou a preferência “WhatsApp”
- **THEN** o backend MUST responder HTTP 400 sem criar doação

#### Scenario: Publicação pelo site continua igual
- **WHEN** uma pessoa publica pelo cadastro em cinco etapas, com título de até 100 caracteres, descrição de até 2000, “A combinar” e “E-mail” ou “Chat do DoaFácil”
- **THEN** a publicação MUST ser aceita como antes
