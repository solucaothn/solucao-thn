# donation-categories Specification

## Purpose
Define como as pessoas navegam pelas categorias de doação: a gaveta aberta pelo menu da home e a página `/categorias`, ambas levando à página Explorar filtrada pela categoria escolhida.

## Requirements

### Requirement: Lista de categorias
O site SHALL apresentar as categorias retornadas pelo backend, com as mesmas exclusões do cadastro de doação, cada uma com ícone e nome, levando a `/explorar?categoria=<id>`. As categorias SHALL ser buscadas no backend uma vez e reaproveitadas pela gaveta, pela página `/categorias`, pela busca da home, pela Explorar, pelo cadastro de doação e pela edição de doação; uma nova busca SHALL acontecer só depois de uma falha ou quando a cópia guardada expirar.

#### Scenario: Categorias do backend
- **WHEN** o backend retorna as categorias
- **THEN** a lista MUST mostrar cada categoria válida, sem as excluídas do cadastro, com um ícone correspondente ao nome (ou um ícone genérico) e uma seta decorativa
- **AND** acionar uma categoria, pelo mouse ou pelo teclado, MUST abrir `/explorar?categoria=<id>` daquela categoria

#### Scenario: Falha ao carregar
- **WHEN** o backend não retorna as categorias
- **THEN** a lista MUST informar que as categorias não puderam ser carregadas e oferecer o link “Explorar doações” para `/explorar`, sem categorias fictícias
- **AND** a lista MUST oferecer o botão “Tentar de novo”, que busca as categorias outra vez

#### Scenario: Navegar entre páginas que usam categorias
- **WHEN** a pessoa abre, uma depois da outra, a home, a gaveta, `/categorias`, a Explorar filtrada e o cadastro de doação
- **THEN** as categorias MUST ser buscadas no backend uma única vez, e as outras páginas MUST reaproveitar a mesma lista

#### Scenario: Falha não fica guardada
- **WHEN** uma busca de categorias falha
- **THEN** nada MUST ficar guardado, e a próxima página ou o “Tentar de novo” MUST buscar de novo

### Requirement: Gaveta de categorias na home
O item “Categorias” do menu da home SHALL abrir uma gaveta lateral à esquerda com o título “Categorias”, a lista de categorias e um botão de fechar.

#### Scenario: Abrir e fechar a gaveta
- **WHEN** a pessoa aciona “Categorias” no menu da home
- **THEN** a gaveta MUST abrir com o foco dentro dela, e MUST fechar pelo botão “Fechar”, com Esc ou com um clique fora, devolvendo o foco ao item do menu

#### Scenario: Escolher uma categoria na gaveta
- **WHEN** a pessoa escolhe uma categoria na gaveta
- **THEN** a gaveta MUST fechar e a página `/explorar?categoria=<id>` MUST abrir

### Requirement: Página de categorias
O site SHALL ter a página pública `/categorias`, com o título “Categorias” e a mesma lista da gaveta, alcançável também por um link na página Explorar.

#### Scenario: Abrir a página
- **WHEN** uma pessoa abre `/categorias`
- **THEN** a página MUST mostrar o título, a lista de categorias e o link “Voltar ao início”
- **AND** o conteúdo principal MUST ter a animação `page-fade-enter`, desligada com `prefers-reduced-motion`

#### Scenario: Página em 360 px
- **WHEN** a página `/categorias` ou a gaveta é exibida com 360 px de largura
- **THEN** a lista MUST caber sem rolagem horizontal, com cada categoria com área de toque de pelo menos 44 px
