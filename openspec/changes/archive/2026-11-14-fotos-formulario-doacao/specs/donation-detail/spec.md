## ADDED Requirements

### Requirement: Aviso de doação recém-publicada
Logo depois de publicar uma doação pelo cadastro, a página de detalhe dessa doação MUST mostrar o aviso “Doação publicada!” com um link para “Minhas doações”. O aviso MUST aparecer somente nessa chegada, e não em outras visitas ao detalhe.

#### Scenario: Chegada depois de publicar
- **WHEN** o cadastro conclui a publicação e abre `/doacao/<id>` da doação criada
- **THEN** a página MUST mostrar, acima do conteúdo da doação, o aviso “Doação publicada!”, anunciado ao leitor de tela, com o link “Minhas doações”, que leva a `/minhas-doacoes`
- **AND** o aviso e o link MUST ter contraste mínimo AA e o link MUST ter área de toque de pelo menos 44 px
- **AND** o aviso MUST caber em 360 px sem rolagem horizontal

#### Scenario: Outras visitas ao detalhe
- **WHEN** qualquer pessoa abre o detalhe de uma doação sem ter acabado de publicá-la, inclusive ao recarregar a página depois da chegada
- **THEN** a página MUST NOT mostrar o aviso de publicação

#### Scenario: Aviso só para a doação publicada
- **WHEN** a pessoa, depois de chegar ao detalhe com o aviso, abre o detalhe de outra doação
- **THEN** o aviso MUST NOT aparecer nessa outra doação
