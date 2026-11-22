# site-shell Specification

## Purpose
Define a identidade do site nas abas do navegador e o que aparece num endereço inexistente: o título de cada página, o favicon do DoaFácil e a página “não encontrada” em português.

## Requirements

### Requirement: Títulos das abas
Cada página SHALL ter, na aba do navegador, o título no formato “<Título> | DoaFácil”, em português. Nenhuma página MUST mostrar o título padrão do Reflex (como “Doafacil | Index”).

#### Scenario: Página com título próprio
- **WHEN** uma pessoa abre qualquer página do site, inclusive a home, as telas de autenticação, o cadastro de doação, o detalhe, o perfil de quem doa, o chat, Minhas doações, a edição de doação, o Editar perfil e a página não encontrada
- **THEN** a aba MUST mostrar “<Título> | DoaFácil”, com um título que descreve a página

### Requirement: Favicon do DoaFácil
O site SHALL usar como favicon o símbolo do logotipo do DoaFácil, em `.ico` e em PNG de 32 px, e SHALL oferecer o ícone de 180 px para atalhos no celular.

#### Scenario: Ícone na aba e no atalho
- **WHEN** uma pessoa abre o site ou adiciona um atalho à tela inicial do celular
- **THEN** a aba MUST mostrar o símbolo do DoaFácil, e o atalho MUST usar o ícone de 180 px
- **AND** nenhum ícone padrão do Reflex MUST aparecer

### Requirement: Página não encontrada
Um endereço que não existe no site SHALL mostrar uma página própria em português, com o cabeçalho comum do site, o título “Página não encontrada”, uma frase curta e os links “Voltar ao início” (`/`) e “Explorar doações” (`/explorar`).

#### Scenario: Endereço inexistente
- **WHEN** uma pessoa abre um endereço que não é uma página do site
- **THEN** a página MUST mostrar o cabeçalho comum, “Página não encontrada”, a frase e os dois links, sem textos em inglês
- **AND** o conteúdo MUST usar `page-fade-enter`, desligada com `prefers-reduced-motion`

#### Scenario: Página não encontrada em 360 px
- **WHEN** a página é exibida com 360 px de largura
- **THEN** ela MUST caber sem rolagem horizontal, com os links de pelo menos 44 px de área de toque
