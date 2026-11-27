## MODIFIED Requirements

### Requirement: Apresentação da home pública
A home SHALL apresentar o cabeçalho, a frase de destaque, as estatísticas “Doações em circulação!” e “Pessoas alcançadas”, a seção “Doações mais recentes” e a ilustração aprovada no rodapé conforme a referência `docs/design/16-landing-nova.png`. Abaixo de 992 px, os links do menu e “Quero Doar” SHALL ficar no painel do menu do celular (spec `site-navigation`).

#### Scenario: Abrir a home sem autenticação
- **WHEN** uma pessoa acessa a página inicial sem sessão
- **THEN** a página apresenta o logotipo, os links Explorar Doações, Como funciona e Categorias, os botões Entrar e Quero Doar, a frase de destaque, as estatísticas (“Pessoas alcançadas” só quando maior que zero) e a seção de doações recentes
- **AND** apresenta a ilustração aprovada ocupando toda a largura no rodapé da página, mantendo sua proporção

#### Scenario: Links do menu do cabeçalho
- **WHEN** uma pessoa aciona um item do menu do cabeçalho
- **THEN** “Explorar Doações” MUST levar a `/explorar`, e “Como funciona” MUST levar à seção “Doar no DoaFácil é simples e seguro” da home, pela âncora `/#como-funciona`
- **AND** “Categorias” MUST abrir a gaveta de categorias (spec `donation-categories`), em vez de navegar
- **AND** os itens MUST ser acessíveis pelo teclado, com foco visível

#### Scenario: Cabeçalho em 360 px
- **WHEN** a home é exibida com 360 px de largura, com ou sem sessão
- **THEN** o cabeçalho MUST caber sem rolagem horizontal da página, com os controles de pelo menos 44 px de área de toque

#### Scenario: Cabeçalho abaixo de 992 px
- **WHEN** a home é exibida com menos de 992 px de largura
- **THEN** a barra do cabeçalho MUST mostrar o logotipo, “Entrar” ou o menu da conta e o botão ☰
- **AND** os links Explorar Doações, Como funciona e Categorias e o “Quero Doar” MUST estar no painel do menu
- **AND** a partir de 992 px, o cabeçalho MUST continuar como no cenário “Abrir a home sem autenticação”, sem o botão ☰

### Requirement: Estatística “Pessoas alcançadas”
A home SHALL apresentar, abaixo de “Doações em circulação!”, a estatística “Pessoas alcançadas” com a quantidade de doações concluídas retornada pelo serviço público de contagem, sem valor fictício.

#### Scenario: Quantidade retornada pelo backend
- **WHEN** o serviço de contagem retorna a quantidade de doações concluídas
- **THEN** a home exibe esse valor junto ao rótulo “Pessoas alcançadas” quando ele é maior que zero

#### Scenario: Nenhuma doação concluída
- **WHEN** o serviço de contagem retorna zero doações concluídas
- **THEN** a home MUST NOT mostrar a estatística “Pessoas alcançadas” enquanto o número for 0
- **AND** “Doações em circulação!” MUST continuar aparecendo
- **AND** durante o carregamento e em caso de falha, a estatística MUST continuar mostrando “Carregando...” ou a mensagem de erro

#### Scenario: Falha ou valor inválido
- **WHEN** o serviço de contagem falha ou não traz uma quantidade válida de doações concluídas
- **THEN** a home informa que o número não pôde ser carregado e não apresenta um valor fictício
- **AND** a estatística “Doações em circulação!” continua sendo exibida quando a sua quantidade for válida
