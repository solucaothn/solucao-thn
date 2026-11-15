## MODIFIED Requirements

### Requirement: Apresentação da home pública
A home SHALL apresentar o cabeçalho, a frase de destaque, as estatísticas “Doações em circulação!” e “Pessoas alcançadas”, a seção “Doações mais recentes” e a ilustração aprovada no rodapé conforme a referência `docs/design/16-landing-nova.png`.

#### Scenario: Abrir a home sem autenticação
- **WHEN** uma pessoa acessa a página inicial sem sessão
- **THEN** a página apresenta o logotipo, os links Explorar Doações, Como funciona e Categorias, os botões Entrar e Quero Doar, a frase de destaque, as duas estatísticas e a seção de doações recentes
- **AND** apresenta a ilustração aprovada ocupando toda a largura no rodapé da página, mantendo sua proporção

#### Scenario: Links do menu do cabeçalho
- **WHEN** uma pessoa aciona um item do menu do cabeçalho
- **THEN** “Explorar Doações” MUST levar a `/explorar` e “Como funciona” a `/como-funciona`
- **AND** “Categorias” MUST abrir a gaveta de categorias (spec `donation-categories`), em vez de navegar
- **AND** os itens MUST ser acessíveis pelo teclado, com foco visível

#### Scenario: Cabeçalho em 360 px
- **WHEN** a home é exibida com 360 px de largura, com ou sem sessão
- **THEN** o cabeçalho MUST caber sem rolagem horizontal da página, com os controles de pelo menos 44 px de área de toque
