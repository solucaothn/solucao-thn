# donation-categories Specification

## Purpose
Define como as pessoas navegam pelas categorias de doação: a gaveta aberta pelo menu da home e a página `/categorias`, ambas levando à página Explorar filtrada pela categoria escolhida.

## Requirements

### Requirement: Lista de categorias
O site SHALL apresentar as categorias retornadas pelo backend, com as mesmas exclusões do cadastro de doação, cada uma com ícone e nome, levando a `/explorar?categoria=<id>`.

#### Scenario: Categorias do backend
- **WHEN** o backend retorna as categorias
- **THEN** a lista MUST mostrar cada categoria válida, sem as excluídas do cadastro, com um ícone correspondente ao nome (ou um ícone genérico) e uma seta decorativa
- **AND** acionar uma categoria, pelo mouse ou pelo teclado, MUST abrir `/explorar?categoria=<id>` daquela categoria

#### Scenario: Falha ao carregar
- **WHEN** o backend não retorna as categorias
- **THEN** a lista MUST informar que as categorias não puderam ser carregadas e oferecer o link “Explorar doações” para `/explorar`, sem categorias fictícias

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
