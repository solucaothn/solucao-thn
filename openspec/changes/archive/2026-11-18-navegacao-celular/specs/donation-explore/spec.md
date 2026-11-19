## MODIFIED Requirements

### Requirement: Cabeçalho e navegação de Explorar
A página `/explorar` SHALL ter o cabeçalho do Figma (logotipo, busca com campo de texto, seletor de UF e botão de buscar, “Quero Doar” e “Entrar” ou o menu da conta), o link “Voltar ao início” e o botão flutuante do chat. Abaixo de 992 px, o “Quero Doar” SHALL ficar no painel do menu do celular, aberto pelo botão ☰ do cabeçalho (spec `site-navigation`).

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

#### Scenario: Cabeçalho de Explorar abaixo de 992 px
- **WHEN** `/explorar` ou `/categorias` é exibida com menos de 992 px de largura
- **THEN** a primeira linha do cabeçalho MUST mostrar o logotipo, “Entrar” ou o menu da conta e o botão ☰, com a busca na linha de baixo
- **AND** o “Quero Doar” MUST estar no painel do menu
