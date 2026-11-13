## MODIFIED Requirements

### Requirement: Entrada no chat pelo cabeçalho da home
A entrada no chat da home MUST ser um botão flutuante “Mensagens” no canto inferior direito, com o total de mensagens não lidas quando houver. Com login, o botão MUST levar a `/chat`; sem login, MUST levar a `/login`. O cabeçalho da home MUST NOT mostrar o link “Mensagens”, nem para quem está logado nem para visitantes.

#### Scenario: Pessoa logada na home
- **WHEN** a home está com o cabeçalho autenticado
- **THEN** a página MUST mostrar o botão flutuante “Mensagens”, levando a `/chat`
- **AND** o cabeçalho MUST mostrar só “Minhas doações”, “Olá, <primeiro nome>” e “Sair”, sem “Mensagens”

#### Scenario: Visitante na home
- **WHEN** a home está com o cabeçalho de visitante
- **THEN** o cabeçalho MUST NOT mostrar “Mensagens”
- **AND** o botão flutuante MUST aparecer sem contador e levar a `/login`
- **AND** nenhuma consulta ao Xano MUST ser feita para o botão

#### Scenario: Total de não lidas no link
- **WHEN** a home carrega com uma pessoa logada e o total de não lidas é maior que zero
- **THEN** o botão MUST mostrar o total num círculo vermelho no canto, com número branco em contraste AA e “99+” acima de 99
- **AND** o rótulo acessível do botão MUST ser “Mensagens, N não lidas” (“Mensagens, 1 não lida” com uma)
- **AND** o total MUST ser consultado uma única vez a cada carregamento da home, sem atualização automática

#### Scenario: Total zero ou indisponível
- **WHEN** o total é zero, a consulta falha ou a pessoa não está logada
- **THEN** o botão MUST NOT mostrar contador e o rótulo MUST ser “Mensagens”
- **AND** a home MUST continuar funcionando, sem mensagem de erro

#### Scenario: Aparência do botão
- **WHEN** o botão flutuante aparece
- **THEN** ele MUST ser um círculo verde `#007A42` de cerca de 56 px, com o ícone de mensagem branco e sombra leve
- **AND** MUST ficar fixo a 24 px das bordas inferior e direita no computador, e a 16 px no celular

#### Scenario: Páginas sem o botão
- **WHEN** a pessoa está no detalhe da doação (`/doacao/<id>`), que já tem o botão “Chat” da própria doação, ou em `/chat`, `/login`, `/cadastro`, `/verificar-email`, `/recuperar-senha`, `/nova-senha`, `/cadastro-doacao`, `/minhas-doacoes` ou `/minhas-doacoes/<id>/editar`
- **THEN** o botão flutuante MUST NOT aparecer
- **AND** o detalhe da doação MUST NOT consultar o total de não lidas

#### Scenario: Celular sem cobrir ações
- **WHEN** a home é vista numa largura de 360 px
- **THEN** o fim da página MUST ter espaço livre pelo menos da altura do botão com as margens, para que nenhum botão de ação fique coberto quando a página está rolada até o fim
- **AND** MUST NOT haver rolagem horizontal

#### Scenario: Movimento reduzido
- **WHEN** a pessoa passa o mouse sobre o botão ou o foca pelo teclado
- **THEN** o botão MUST mostrar um realce e um contorno de foco visível
- **AND** com `prefers-reduced-motion` ativo, o realce MUST NOT ter transição nem deslocamento
