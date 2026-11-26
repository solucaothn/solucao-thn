## MODIFIED Requirements

### Requirement: Explorar em telas estreitas
As páginas `/explorar` e `/categorias` SHALL caber em 360 px sem rolagem horizontal, com a busca do cabeçalho utilizável.

#### Scenario: Visualização em 360 px
- **WHEN** a página é exibida com 360 px de largura
- **THEN** a grade MUST mostrar uma coluna de cartões, e o cabeçalho MUST empilhar a busca abaixo do logotipo sem cortar controles
- **AND** a página MUST NOT ter rolagem horizontal

#### Scenario: Digitar na busca do cabeçalho em 360 px
- **WHEN** `/explorar` ou `/categorias` é exibida com 360 px de largura
- **THEN** a busca do cabeçalho MUST ocupar a largura da linha abaixo do logotipo, com o campo de texto, o seletor de UF e o botão de buscar visíveis e dentro da tela
- **AND** o campo de texto MUST ter largura para mostrar o que a pessoa digita
- **AND** a página MUST NOT ter rolagem horizontal

#### Scenario: Busca do cabeçalho a partir de 992 px
- **WHEN** `/explorar` ou `/categorias` é exibida com 992 px de largura ou mais
- **THEN** a busca MUST ficar na mesma linha do logotipo e dos controles da conta, com no máximo 620 px de largura
