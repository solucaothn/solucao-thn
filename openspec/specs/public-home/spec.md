# public-home Specification

## Purpose

Define a apresentação da página inicial pública do DoaFácil e como seus elementos exibem a contagem e as doações disponíveis obtidas do backend.

## Requirements

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

### Requirement: Exibição da contagem em circulação
A home SHALL apresentar na estatística “Doações em circulação” a quantidade retornada pelo serviço público de contagem de doações disponíveis.

#### Scenario: Contagem retornada pelo backend
- **WHEN** o serviço retorna uma quantidade de doações disponíveis
- **THEN** a home exibe esse valor junto ao rótulo “Doações em circulação”

#### Scenario: Falha ao carregar a contagem
- **WHEN** o serviço de contagem falha
- **THEN** a home informa que a contagem não pôde ser carregada e não apresenta um valor fictício como se fosse a contagem real

#### Scenario: URL base do Xano não configurada
- **WHEN** `XANO_API_URL` está ausente ou não contém uma URL HTTP(S) válida
- **THEN** a home informa que não foi possível conectar ao Xano para cada seção afetada
- **AND** não apresenta uma contagem ou uma lista de doações fictícias

### Requirement: Cartões de doações recentes
A home SHALL exibir os dados retornados para cada doação recente com título, condição, botão “Acessar” e uma imagem.

#### Scenario: Doação com foto e condição
- **WHEN** uma doação recente possui foto e condição
- **THEN** o cartão exibe a foto, o título e a condição com o rótulo “Condição”
- **AND** exibe o botão “Acessar” que navega para `/doacao/<id>` daquela doação

#### Scenario: Doação sem foto
- **WHEN** uma doação recente não possui foto
- **THEN** o cartão exibe uma imagem genérica no lugar da foto

#### Scenario: Doação sem condição
- **WHEN** uma doação recente não possui condição
- **THEN** o cartão exibe “Condição não informada”

#### Scenario: Marcação de doação nova
- **WHEN** a data de criação da doação está dentro dos últimos sete dias
- **THEN** o cartão exibe a etiqueta “NOVO”

#### Scenario: Doação fora do período de novidade
- **WHEN** a data de criação da doação tem mais de sete dias
- **THEN** o cartão não exibe a etiqueta “NOVO”

#### Scenario: Nenhuma doação recente
- **WHEN** o serviço retorna uma lista vazia
- **THEN** a home mantém os demais elementos e informa que ainda não há doações disponíveis para exibição

#### Scenario: Falha ao carregar as doações recentes
- **WHEN** o serviço de listagem falha
- **THEN** a home informa que as doações recentes não puderam ser carregadas e não apresenta cartões fictícios

#### Scenario: Item inválido em uma lista de doações recentes
- **WHEN** a resposta contém um ou mais itens inválidos e ao menos um item válido
- **THEN** a home ignora somente os itens inválidos e exibe os cartões válidos

#### Scenario: Nenhum item válido na resposta
- **WHEN** a resposta contém itens, mas nenhum deles é válido
- **THEN** a home informa que as doações recentes não puderam ser carregadas

#### Scenario: Cartões recentes em carrossel
- **WHEN** existem uma ou mais doações recentes válidas
- **THEN** os cartões são exibidos em uma única linha horizontal, sem quebra
- **AND** cada cartão é quadrado, com lado flexível entre cerca de 220px e 260px, dividindo a largura do carrossel entre quatro cartões
- **AND** há espaçamento aproximado de 1.25rem entre cartões
- **AND** o carrossel permite rolagem horizontal com scroll-snap no eixo X e alinhamento inicial
- **AND** são exibidos no máximo quatro cartões
- **AND** a linha das estatísticas e do carrossel usa a mesma largura máxima e as mesmas margens laterais do conteúdo do cabeçalho
- **AND** numa janela de 1512px, os quatro cartões cabem ao lado das estatísticas, sem rolagem do carrossel; quando não cabem com o lado mínimo, o carrossel rola
- **AND** em telas estreitas o carrossel ocupa a largura disponível e continua rolável horizontalmente
- **AND** em telas largas a contagem reserva 11rem sem encolher, fica centralizada na altura dos cartões, o rótulo pode quebrar em linhas e o carrossel ocupa apenas o espaço restante sem sobreposição
- **AND** em telas estreitas a contagem ocupa toda a largura acima do título e do carrossel
- **AND** a rolagem horizontal fica restrita ao carrossel, sem rolagem horizontal da página

#### Scenario: Contagem e mensagem de erro sem sobreposição
- **WHEN** a contagem falha
- **THEN** a mensagem de erro e o rótulo “Doações em circulação!” permanecem visíveis em áreas distintas, sem sobreposição

### Requirement: Estatística “Pessoas alcançadas”
A home SHALL apresentar, abaixo de “Doações em circulação!”, a estatística “Pessoas alcançadas” com a quantidade de doações concluídas retornada pelo serviço público de contagem, sem valor fictício.

#### Scenario: Quantidade retornada pelo backend
- **WHEN** o serviço de contagem retorna a quantidade de doações concluídas
- **THEN** a home exibe esse valor junto ao rótulo “Pessoas alcançadas”

#### Scenario: Falha ou valor inválido
- **WHEN** o serviço de contagem falha ou não traz uma quantidade válida de doações concluídas
- **THEN** a home informa que o número não pôde ser carregado e não apresenta um valor fictício
- **AND** a estatística “Doações em circulação!” continua sendo exibida quando a sua quantidade for válida

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

### Requirement: Link “Ver mais...” das doações recentes
A seção “Doações mais recentes:” SHALL apresentar o link “Ver mais...”, que leva a `/explorar`.

#### Scenario: Ver mais doações
- **WHEN** uma pessoa aciona “Ver mais...”
- **THEN** a página `/explorar` MUST ser aberta, sem filtros

#### Scenario: Sem doações ou com erro
- **WHEN** a lista de doações recentes está vazia ou falhou
- **THEN** o link “Ver mais...” MUST continuar visível e funcional

### Requirement: Tentar de novo nas falhas da home
Quando a contagem ou as doações recentes da home não puderem ser carregadas, a home SHALL mostrar, junto de cada mensagem de erro, o botão “Tentar de novo”, que busca outra vez os dados da home sem recarregar o site.

#### Scenario: Falha da contagem
- **WHEN** o serviço de contagem falha
- **THEN** a home MUST mostrar a mensagem de erro da contagem e o botão “Tentar de novo”, com área de toque de pelo menos 44 px, foco visível e contraste mínimo AA

#### Scenario: Falha das doações recentes
- **WHEN** o serviço de doações recentes falha
- **THEN** a home MUST mostrar a mensagem de erro das recentes e o botão “Tentar de novo”, com as mesmas regras de toque, foco e contraste

#### Scenario: Nova tentativa
- **WHEN** a pessoa aciona “Tentar de novo”
- **THEN** a home MUST mostrar o carregamento e buscar a contagem e as recentes outra vez, mostrando os dados ou a mensagem de erro conforme o resultado

#### Scenario: Lista vazia não é falha
- **WHEN** o serviço retorna uma lista vazia de recentes
- **THEN** a home MUST mostrar que ainda não há doações, sem o botão “Tentar de novo”
