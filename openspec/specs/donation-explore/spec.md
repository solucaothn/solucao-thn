# donation-explore Specification

## Purpose
Define a página Explorar doações (`/explorar`), que recebe os filtros de busca vindos da home. Nesta primeira versão, a página é provisória e só confirma os filtros recebidos; a listagem de resultados vem numa change seguinte.

## Requirements

### Requirement: Listagem de doações em Explorar
A página pública `/explorar` SHALL listar as doações disponíveis, da mais nova para a mais antiga, aplicando os filtros `q`, `categoria` e `uf` da URL, com os mesmos cartões da home (foto, NOVO, título, condição e “Acessar”).

#### Scenario: Sem filtros
- **WHEN** uma pessoa abre `/explorar` sem parâmetros
- **THEN** a página MUST mostrar o título “Adicionadas recentemente” e as primeiras 12 doações disponíveis

#### Scenario: Com filtros
- **WHEN** uma pessoa abre `/explorar` com qualquer combinação de `q`, `categoria` e `uf`
- **THEN** a página MUST mostrar só as doações disponíveis que atendem a todos os filtros escolhidos
- **AND** o título MUST refletir os filtros: “Categoria “<nome>”” com a categoria, “Resultados para “<texto>”” com o texto (os dois, quando houver ambos), e a UF ao lado (“em SP”)

#### Scenario: Parâmetros inválidos
- **WHEN** `categoria` não é um inteiro positivo, ou `uf` não é uma das 27 siglas
- **THEN** a página MUST ignorar esse parâmetro e tratá-lo como não escolhido

#### Scenario: Categoria desconhecida
- **WHEN** `categoria` é um número que não corresponde a uma categoria do backend
- **THEN** a página MUST mostrar o estado vazio, sem doações de outras categorias

### Requirement: Carregar mais doações
A listagem de `/explorar` SHALL mostrar 12 doações por vez e oferecer o botão “Carregar mais”, que acrescenta as próximas 12 abaixo das já exibidas, mantendo os mesmos filtros.

#### Scenario: Há mais resultados
- **WHEN** o total de resultados é maior que o número de cartões exibidos
- **THEN** a página MUST mostrar “Carregar mais”, e acioná-lo MUST acrescentar a próxima página sem remover as anteriores nem duplicar cartões

#### Scenario: Fim da lista
- **WHEN** todos os resultados já foram exibidos
- **THEN** o botão “Carregar mais” MUST NOT aparecer

#### Scenario: Carregando a próxima página
- **WHEN** a próxima página está sendo carregada
- **THEN** o botão MUST ficar desativado e informar o carregamento, e um segundo clique MUST NOT disparar outra requisição

### Requirement: Estado vazio e falha em Explorar
A página `/explorar` SHALL informar quando não há resultados e quando a busca falha, sem cartões fictícios.

#### Scenario: Nenhum resultado
- **WHEN** a busca não encontra doações
- **THEN** a página MUST mostrar “Nenhuma doação encontrada” e, havendo filtros, o link “Limpar filtros” para `/explorar`

#### Scenario: Falha da busca
- **WHEN** o serviço de busca falha
- **THEN** a página MUST informar que as doações não puderam ser carregadas, com um botão para tentar de novo
- **AND** numa falha ao carregar mais, os cartões já exibidos MUST continuar na tela

### Requirement: Cabeçalho e navegação de Explorar
A página `/explorar` SHALL ter o cabeçalho do Figma (logotipo, busca com campo de texto, seletor de UF e botão de buscar, “Quero Doar” e “Entrar” ou o menu da conta), o link “Voltar ao início” e o botão flutuante do chat.

#### Scenario: Buscar a partir de Explorar
- **WHEN** a pessoa altera o texto ou a UF no cabeçalho e busca, pelo botão ou com Enter
- **THEN** a página MUST abrir `/explorar` com os novos `q` e `uf`, mantendo a `categoria` atual quando houver

#### Scenario: Remover a categoria
- **WHEN** há uma categoria aplicada
- **THEN** a página MUST mostrar a categoria como um filtro removível, e removê-la MUST abrir `/explorar` sem `categoria`, mantendo `q` e `uf`

#### Scenario: Campos refletem a URL
- **WHEN** a página abre com `q` e `uf`
- **THEN** o campo de texto e o seletor de UF do cabeçalho MUST mostrar esses valores

#### Scenario: Animação e acessibilidade
- **WHEN** a página é exibida
- **THEN** o conteúdo principal MUST ter a animação de entrada `page-fade-enter`, desligada com `prefers-reduced-motion`, e os cartões carregados do backend MUST NOT animar
- **AND** o campo, o seletor, os botões e os links MUST ter rótulo acessível, foco visível e área de toque de pelo menos 44 px

### Requirement: Explorar em telas estreitas
A página `/explorar` SHALL caber em 360 px sem rolagem horizontal.

#### Scenario: Visualização em 360 px
- **WHEN** a página é exibida com 360 px de largura
- **THEN** a grade MUST mostrar uma coluna de cartões, e o cabeçalho MUST empilhar a busca abaixo do logotipo sem cortar controles
- **AND** a página MUST NOT ter rolagem horizontal
