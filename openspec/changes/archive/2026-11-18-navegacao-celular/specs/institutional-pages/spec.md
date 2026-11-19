## MODIFIED Requirements

### Requirement: Estrutura comum das páginas institucionais
Cada página institucional SHALL ter o cabeçalho com o logotipo centralizado levando à home e os controles do site à direita (spec `site-navigation`), o link “Voltar ao início”, um único título de nível 1 seguido de títulos em ordem, o rodapé público da home e o botão flutuante do chat.

#### Scenario: Abrir uma página institucional
- **WHEN** uma pessoa abre `/duvidas`, `/seguranca`, `/termos`, `/privacidade`, `/quem-somos` ou `/contato`
- **THEN** a página MUST mostrar o cabeçalho com o logotipo (link para `/`), “Voltar ao início” (link para `/`), o conteúdo e o rodapé público da home
- **AND** MUST ter exatamente um título de nível 1, e os títulos seguintes MUST NOT pular níveis
- **AND** o conteúdo principal MUST ter a animação `page-fade-enter`, desligada com `prefers-reduced-motion`

#### Scenario: Página em 360 px
- **WHEN** qualquer página institucional é exibida com 360 px de largura
- **THEN** a página MUST NOT ter rolagem horizontal, os textos longos MUST quebrar linha e os controles MUST ter área de toque de pelo menos 44 px

#### Scenario: Controles do site no cabeçalho
- **WHEN** uma página institucional é exibida
- **THEN** o cabeçalho MUST mostrar à direita do logotipo, no desktop, “Entrar” ou o menu da conta e “Quero Doar”, e, abaixo de 992 px, o botão ☰
- **AND** o logotipo MUST continuar centralizado
