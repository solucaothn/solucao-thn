## Purpose

Define a página Explorar doações (`/explorar`), que recebe os filtros de busca vindos da home. Nesta primeira versão, a página é provisória e só confirma os filtros recebidos; a listagem de resultados vem numa change seguinte.

## ADDED Requirements

### Requirement: Página provisória de Explorar doações
O site SHALL ter a página pública `/explorar`, que aceita os parâmetros `q`, `categoria` e `uf` e, enquanto a busca não estiver pronta, informa que a página está em construção e mostra os filtros recebidos, sem resultados fictícios.

#### Scenario: Abrir com filtros
- **WHEN** uma pessoa abre `/explorar` com um ou mais dos parâmetros `q`, `categoria` e `uf`
- **THEN** a página MUST apresentar o título “Explorar doações”, o aviso de que a busca ainda está em construção e um resumo dos filtros recebidos: o texto buscado, o nome da categoria (ou “Todas as categorias” quando o id não corresponde a uma categoria do backend) e a UF
- **AND** MUST NOT apresentar lista de doações nem quantidade de resultados

#### Scenario: Abrir sem filtros
- **WHEN** uma pessoa abre `/explorar` sem parâmetros
- **THEN** a página MUST apresentar o título e o aviso, informando que nenhum filtro foi escolhido

#### Scenario: Parâmetros inválidos
- **WHEN** `categoria` não é um número inteiro positivo, ou `uf` não é uma das 27 siglas
- **THEN** a página MUST ignorar esse parâmetro e tratá-lo como não escolhido

#### Scenario: Caminhos de saída
- **WHEN** a página é exibida
- **THEN** ela MUST oferecer um link para voltar à home e um para as doações recentes (`/#doacoes-recentes`)
- **AND** o conteúdo principal MUST ter a animação de entrada `page-fade-enter`, desligada com `prefers-reduced-motion`
- **AND** a página MUST caber em 360 px sem rolagem horizontal
