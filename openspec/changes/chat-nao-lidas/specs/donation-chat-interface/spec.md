## MODIFIED Requirements

### Requirement: Lista de conversas
A página `/chat` MUST listar as conversas da pessoa autenticada, da mais recente para a mais antiga. Cada item MUST mostrar o primeiro nome da outra pessoa, o título da doação e um círculo verde com a inicial desse nome, sem foto, sobrenome, e-mail ou indicador “Online”. Conversas com mensagens não lidas MUST mostrar o número delas num círculo verde.

#### Scenario: Pessoa com conversas
- **WHEN** a pessoa autenticada abre `/chat` e participa de conversas
- **THEN** a lista MUST mostrar cada conversa com o primeiro nome da outra pessoa, o título da doação e o círculo com a inicial
- **AND** MUST NOT mostrar foto de perfil, sobrenome, e-mail ou status de presença

#### Scenario: Pessoa sem conversas
- **WHEN** a pessoa autenticada não participa de nenhuma conversa
- **THEN** a página MUST mostrar o aviso “Você ainda não tem conversas.”

#### Scenario: Mais conversas do que a primeira página
- **WHEN** a resposta indica que há mais conversas
- **THEN** a lista MUST oferecer “Carregar mais conversas”, que busca a página seguinte sem repetir itens

#### Scenario: Falha ao carregar a lista
- **WHEN** a consulta de conversas falha por rede ou erro do serviço diferente de 401
- **THEN** a página MUST mostrar uma mensagem de erro simples e a opção de tentar de novo, sem apagar o que já estava na tela

#### Scenario: Contador de não lidas no item
- **WHEN** uma conversa da lista tem `unread_count` maior que zero
- **THEN** o item MUST mostrar o número num círculo verde, com texto de contraste AA
- **AND** acima de 99 MUST mostrar “99+”
- **AND** o contador MUST ter um rótulo acessível, por exemplo “3 mensagens não lidas”

#### Scenario: Conversa sem não lidas
- **WHEN** o `unread_count` da conversa é zero
- **THEN** o item MUST NOT mostrar contador

#### Scenario: Contador some ao abrir a conversa
- **WHEN** a pessoa abre uma conversa que tinha mensagens não lidas
- **THEN** o contador dessa conversa MUST sumir sem esperar a próxima atualização da lista
- **AND** enquanto a conversa estiver aberta, a lista MUST NOT mostrar contador para ela, mesmo que uma atualização da lista chegue antes da leitura das mensagens novas

### Requirement: Atualização automática limitada
Com uma conversa aberta e a aba visível, a página MUST buscar mensagens novas em intervalos de no mínimo 15 segundos, pedindo só as posteriores à última recebida. Com a aba visível, a lista de conversas MUST ser atualizada em intervalos de no mínimo 30 segundos, com ou sem conversa aberta. Com a aba oculta, MUST NOT fazer consultas automáticas. Não há atualização em tempo real.

#### Scenario: Conversa aberta e aba visível
- **WHEN** a conversa está aberta e a aba está visível
- **THEN** a página MUST consultar mensagens novas no máximo uma vez a cada 15 segundos e acrescentá-las sem duplicar as existentes

#### Scenario: Atualização da lista
- **WHEN** a pessoa está em `/chat` com a aba visível
- **THEN** a página MUST consultar a primeira página da lista no máximo uma vez a cada 30 segundos, atualizando contadores, ordem e conversas novas
- **AND** MUST manter as conversas de páginas já carregadas com “Carregar mais conversas”, sem duplicá-las

#### Scenario: Aba oculta
- **WHEN** a aba fica oculta
- **THEN** a página MUST NOT fazer consultas automáticas até a aba voltar a ficar visível

#### Scenario: Consulta automática recebe 429
- **WHEN** uma consulta automática recebe HTTP 429, do chat ou da plataforma
- **THEN** a página MUST pausar as consultas automáticas por pelo menos 60 segundos, sem mostrar erro bloqueante
- **AND** a pausa MUST valer para as mensagens e para a lista

#### Scenario: Sair da página
- **WHEN** a pessoa sai de `/chat`
- **THEN** as consultas automáticas MUST parar

### Requirement: Entrada no chat pelo cabeçalho da home
O cabeçalho logado da home MUST mostrar o link “Mensagens”, que leva a `/chat`, com o total de mensagens não lidas quando houver. O cabeçalho de visitante MUST NOT mostrar esse link.

#### Scenario: Pessoa logada na home
- **WHEN** a home está com o cabeçalho autenticado
- **THEN** o cabeçalho MUST mostrar “Mensagens” junto de “Olá, <primeiro nome>” e “Sair”, levando a `/chat`

#### Scenario: Visitante na home
- **WHEN** a home está com o cabeçalho de visitante
- **THEN** o cabeçalho MUST NOT mostrar “Mensagens”

#### Scenario: Total de não lidas no link
- **WHEN** a home carrega com uma pessoa logada e o total de não lidas é maior que zero
- **THEN** o link “Mensagens” MUST mostrar o total num círculo verde, com “99+” acima de 99 e rótulo acessível
- **AND** o total MUST ser consultado uma única vez a cada carregamento da home, sem atualização automática

#### Scenario: Total zero ou indisponível
- **WHEN** o total é zero, a consulta falha ou a pessoa não está logada
- **THEN** o link MUST NOT mostrar contador
- **AND** a home MUST continuar funcionando, sem mensagem de erro
