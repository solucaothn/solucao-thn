# site-navigation Specification

## Purpose
Define como uma pessoa navega pelo site a partir do cabeçalho em qualquer largura de tela: o menu do celular (botão ☰ e painel lateral) e os controles do site no cabeçalho das páginas com o logotipo centralizado.

## Requirements

### Requirement: Botão do menu no celular
Abaixo de 992 px de largura, o cabeçalho das páginas com navegação SHALL mostrar um botão de menu (☰) que abre o painel de navegação. A partir de 992 px, o botão MUST NOT aparecer.

#### Scenario: Botão abaixo de 992 px
- **WHEN** uma página com navegação é exibida com menos de 992 px de largura
- **THEN** o cabeçalho MUST mostrar o botão ☰ com o rótulo acessível “Abrir menu”, foco visível e área de toque de pelo menos 44 × 44 px

#### Scenario: Desktop sem o botão
- **WHEN** a mesma página é exibida com 992 px ou mais
- **THEN** o botão ☰ MUST NOT aparecer, e o cabeçalho MUST mostrar os controles do desktop

### Requirement: Painel de navegação
O botão ☰ SHALL abrir um painel lateral à esquerda, na altura toda da tela, com o título “Menu” e os destinos principais do site. O painel MUST seguir o padrão da gaveta de categorias: foco preso dentro dele e fechamento pelo botão “Fechar”, com Esc ou com um clique fora, devolvendo o foco ao botão ☰.

#### Scenario: Abrir e fechar
- **WHEN** a pessoa aciona o botão ☰
- **THEN** o painel MUST abrir com o foco dentro dele
- **AND** MUST fechar pelo botão “Fechar”, com Esc ou com um clique fora, devolvendo o foco ao botão ☰

#### Scenario: Itens para todos
- **WHEN** o painel está aberto
- **THEN** ele MUST mostrar, nesta ordem, “Explorar doações” (`/explorar`), “Como funciona” (`/#como-funciona`), “Categorias” (`/categorias`) e “Quero Doar” (`/cadastro-doacao`)
- **AND** escolher um item MUST fechar o painel e abrir o destino

#### Scenario: Itens com sessão
- **WHEN** o painel está aberto e há sessão
- **THEN** ele MUST mostrar a foto de perfil (ou a inicial) e o primeiro nome, e os itens “Minhas doações” (`/minhas-doacoes`), “Mensagens” (`/chat`), “Editar perfil” (`/perfil/editar`) e “Sair”
- **AND** “Sair” MUST encerrar a sessão como o “Sair” do menu da conta
- **AND** MUST NOT mostrar “Entrar”

#### Scenario: Itens sem sessão
- **WHEN** o painel está aberto e não há sessão
- **THEN** ele MUST mostrar “Entrar” (`/login`) e MUST NOT mostrar os itens da conta nem “Mensagens”

#### Scenario: Total de não lidas em Mensagens
- **WHEN** há sessão e o total de não lidas já carregado na sessão é maior que zero
- **THEN** “Mensagens” MUST mostrar o total no mesmo selo do botão flutuante, com “99+” acima de 99, e o rótulo acessível “Mensagens, N não lidas”
- **AND** abrir o painel MUST NOT fazer nenhuma consulta ao Xano

#### Scenario: Painel em 360 px
- **WHEN** o painel é aberto numa tela de 360 px
- **THEN** ele MUST ocupar no máximo a largura da tela, sem rolagem horizontal, com cada item de pelo menos 44 px de altura

### Requirement: Controles do site no cabeçalho centralizado
As páginas com o logotipo centralizado SHALL mostrar à direita, na linha do logotipo, os controles do site: no desktop, “Entrar” ou o menu da conta, e “Quero Doar”; abaixo de 992 px, só o botão ☰. Isso vale para o detalhe da doação, o perfil de quem doa, `/chat`, `/minhas-doacoes`, a edição de doação, `/perfil/editar`, `/cadastro-doacao` e as páginas institucionais. O link “Voltar” existente MUST continuar à esquerda.

#### Scenario: Página com “Voltar” no desktop
- **WHEN** uma dessas páginas é exibida com 992 px ou mais
- **THEN** a linha do logotipo MUST mostrar o “Voltar” à esquerda (quando a página tem), o logotipo no centro e, à direita, “Entrar” ou o menu da conta e “Quero Doar”

#### Scenario: Página em 360 px
- **WHEN** uma dessas páginas é exibida com 360 px de largura
- **THEN** a linha do logotipo MUST mostrar o “Voltar” (quando houver), o logotipo e o botão ☰, sem rolagem horizontal e com os controles de pelo menos 44 px de área de toque

#### Scenario: Largura toda e respiro das bordas
- **WHEN** uma dessas páginas, inclusive `/chat`, é exibida em qualquer largura
- **THEN** o cabeçalho MUST ocupar a largura toda da tela, com o “Voltar” no canto esquerdo e a conta e “Quero Doar” (ou o ☰) no canto direito, a 32 px das bordas a partir de 992 px e a 16 px abaixo disso
- **AND** o logotipo MUST ficar centralizado na tela, com a mesma altura e o mesmo padding vertical do cabeçalho da home, sem corte em cima e sem encostar no topo
- **AND** os cabeçalhos da home, de `/explorar` e de `/categorias` MUST continuar como estão

#### Scenario: Cadastro de doação
- **WHEN** a pessoa está em `/cadastro-doacao` no desktop
- **THEN** o cabeçalho MUST mostrar “Entrar” ou o menu da conta, sem “Quero Doar”
- **AND** a seta “Voltar ao início” MUST continuar abaixo do cabeçalho, na posição atual

#### Scenario: Telas de autenticação sem navegação
- **WHEN** a pessoa está em `/login`, `/cadastro`, `/recuperar-senha`, `/verificar-email` ou `/nova-senha`
- **THEN** o cabeçalho MUST continuar só com o logotipo, sem o botão ☰ e sem os controles da conta

#### Scenario: Nome da conta carregado
- **WHEN** uma dessas páginas é aberta diretamente pelo endereço, com sessão
- **THEN** o menu da conta e o painel MUST mostrar o primeiro nome e a foto da pessoa

### Requirement: Conta carregada uma vez por sessão
O nome e a foto da conta, usados pelo menu da conta e pelo painel, SHALL ser buscados no backend uma única vez por sessão e reaproveitados em todas as páginas. Uma nova busca SHALL acontecer só depois de um login, de um logout ou de um token rejeitado. A edição do perfil SHALL atualizar o nome e a foto mostrados sem nova busca.

#### Scenario: Navegar entre páginas
- **WHEN** uma pessoa com sessão abre várias páginas com o cabeçalho, uma depois da outra
- **THEN** o nome e a foto MUST ser buscados só na primeira, e as outras MUST NOT fazer pedido para isso

#### Scenario: Login, logout e token rejeitado
- **WHEN** a pessoa entra com outra sessão, sai, ou tem o token rejeitado pelo backend
- **THEN** a próxima página com o cabeçalho MUST buscar a conta de novo (ou mostrar o cabeçalho de visitante, sem pedido, quando não há sessão)

#### Scenario: Falha passageira
- **WHEN** a busca do nome falha por um erro passageiro
- **THEN** o cabeçalho MUST mostrar “Minha conta”, e a próxima página MUST tentar de novo

#### Scenario: Edição do perfil
- **WHEN** a pessoa salva um nome novo ou troca a foto em Editar perfil
- **THEN** o menu da conta e o painel MUST mostrar o nome e a foto novos sem nova busca no backend
