## MODIFIED Requirements

### Requirement: Apresentação da home pública
A home SHALL apresentar o cabeçalho, a frase de destaque, as estatísticas “Doações em circulação!” e “Pessoas alcançadas”, a seção “Doações mais recentes” e a ilustração aprovada no rodapé conforme a referência `docs/design/16-landing-nova.png`. Abaixo de 992 px, os links do menu e “Quero Doar” SHALL ficar no painel do menu do celular (spec `site-navigation`).

#### Scenario: Abrir a home sem autenticação
- **WHEN** uma pessoa acessa a página inicial sem sessão
- **THEN** a página apresenta o logotipo, os links Explorar Doações, Como funciona e Categorias, os botões Entrar e Quero Doar, a frase de destaque, as duas estatísticas e a seção de doações recentes
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

### Requirement: Menu da conta no cabeçalho
Com sessão, o cabeçalho da home SHALL apresentar um menu da conta com a foto de perfil (ou, sem foto, a inicial) e o primeiro nome da pessoa, no lugar dos controles “Minhas doações”, “Olá, nome” e “Sair”, mantendo o botão “Quero Doar”. Abaixo de 992 px, o “Quero Doar” SHALL ficar no painel do menu do celular.

#### Scenario: Abrir o menu
- **WHEN** uma pessoa com sessão aciona o menu da conta, pelo mouse ou pelo teclado
- **THEN** o menu MUST mostrar “Minhas doações” (`/minhas-doacoes`), “Editar perfil” (`/perfil/editar`) e “Sair”
- **AND** “Sair” MUST encerrar a sessão como o botão atual
- **AND** o gatilho MUST ter rótulo acessível com o nome da conta e área de toque de pelo menos 44 px

#### Scenario: Nome longo
- **WHEN** o primeiro nome não cabe no espaço do cabeçalho
- **THEN** o nome MUST ser cortado com reticências, sem quebrar a linha do cabeçalho

#### Scenario: Sem sessão
- **WHEN** não há sessão
- **THEN** o cabeçalho MUST mostrar “Entrar” e “Quero Doar”, sem o menu da conta
- **AND** abaixo de 992 px, o “Quero Doar” MUST estar no painel do menu, e a barra MUST mostrar “Entrar” e o botão ☰

#### Scenario: Foto de perfil no círculo
- **WHEN** a pessoa com sessão tem foto de perfil
- **THEN** o círculo do menu MUST mostrar a foto, redonda e com `object-fit: cover`, com texto alternativo vazio (o nome já está no rótulo do botão)
- **AND** sem foto, o círculo MUST mostrar a inicial do nome ou, sem nome ainda, o ícone de pessoa
- **AND** a foto MUST vir do `GET auth/profile` numa só requisição, feita no carregamento da conta e só na primeira vez para cada sessão; uma falha nessa requisição MUST manter a inicial, sem afetar a página
- **AND** ao trocar ou remover a foto em Editar perfil, o círculo MUST refletir a mudança sem nova requisição
