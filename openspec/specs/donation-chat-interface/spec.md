# donation-chat-interface Specification

## Purpose
Interface web em que quem doa e quem tem interesse em uma doação leem e trocam mensagens privadas, consumindo os endpoints do chat sem expor dados pessoais e respeitando os limites do backend e da plataforma.

## Requirements

### Requirement: Acesso autenticado à página de mensagens
A aplicação MUST oferecer a página `/chat` somente a pessoas com sessão válida. Sem sessão, ou quando o backend rejeitar o token, MUST levar a pessoa a `/login` sem chamar os endpoints de leitura do chat.

#### Scenario: Pessoa sem login abre /chat
- **WHEN** uma pessoa sem sessão válida abre `/chat`
- **THEN** a aplicação MUST redirecionar para `/login`
- **AND** MUST NOT chamar os endpoints de conversas ou mensagens

#### Scenario: Token rejeitado durante o uso
- **WHEN** um endpoint do chat responde HTTP 401
- **THEN** a aplicação MUST limpar a sessão transitória e redirecionar para `/login`

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

### Requirement: Conversa aberta e histórico
Ao abrir uma conversa, a página MUST mostrar no cabeçalho o primeiro nome da outra pessoa e o título da doação, e carregar as mensagens mais recentes. As anteriores ficam sob demanda, em “Carregar anteriores”. As mensagens MUST aparecer em ordem de envio, as da própria pessoa à direita e as da outra à esquerda, agrupadas por dia (“Hoje”, “Ontem” ou dd/mm/aaaa) no fuso de Brasília.

#### Scenario: Abrir conversa pela lista
- **WHEN** a pessoa seleciona uma conversa na lista
- **THEN** a página MUST destacar o item, mostrar o cabeçalho da conversa e carregar as mensagens mais recentes em ordem de envio, com uma única consulta

#### Scenario: Carregar mensagens anteriores
- **WHEN** há mensagens anteriores às exibidas e a pessoa aciona “Carregar anteriores”
- **THEN** a página MUST buscar a página anterior à mensagem mais antiga exibida e inseri-la no topo, sem duplicar mensagens nem perder a posição de leitura
- **AND** quando não houver mais mensagens anteriores, MUST esconder “Carregar anteriores”

#### Scenario: Abrir conversa pelo endereço
- **WHEN** a pessoa abre `/chat?conversa=<id>` com o identificador de uma conversa da qual participa
- **THEN** a página MUST abrir essa conversa diretamente

#### Scenario: Erro de limite ao carregar a conversa
- **WHEN** a consulta da conversa ou da lista recebe HTTP 429
- **THEN** a página MUST mostrar o texto correspondente (do chat ou da plataforma, como no envio) e a opção de tentar de novo

#### Scenario: Conversa inexistente ou de outra pessoa
- **WHEN** o identificador da conversa no endereço é inválido ou o backend responde 404
- **THEN** a página MUST mostrar “Conversa não encontrada.” e manter a lista disponível

#### Scenario: Horário de envio
- **WHEN** a conversa mostra uma mensagem
- **THEN** a página MUST mostrar embaixo da bolha, do mesmo lado dela, o horário de envio no formato HH:MM no fuso de Brasília (UTC−3), pela mesma regra dos rótulos de dia
- **AND** o horário MUST aparecer em fonte pequena, na cor `#6b6b6b`

#### Scenario: Autoria das mensagens
- **WHEN** o histórico contém mensagens das duas pessoas
- **THEN** cada mensagem MUST ficar do lado de quem a enviou conforme a indicação de autoria do backend, e não pela comparação de nomes

#### Scenario: Conversa sem mensagens
- **WHEN** a conversa aberta ainda não tem mensagens
- **THEN** a página MUST mostrar um aviso neutro convidando a escrever a primeira mensagem

### Requirement: Envio de mensagem
A página MUST permitir enviar uma mensagem pelo campo “Digite aqui...”, com o botão “Enviar” ou a tecla Enter. A interface MUST impedir o envio de texto vazio e de texto acima de 1000 caracteres, e MUST traduzir as recusas do backend em mensagens amigáveis, sem apagar o texto digitado.

#### Scenario: Envio aceito
- **WHEN** a pessoa digita um texto válido e aciona “Enviar” ou Enter
- **THEN** a página MUST enviar a mensagem, mostrá-la no fim da conversa e limpar o campo

#### Scenario: Texto vazio
- **WHEN** a pessoa aciona o envio com o campo vazio ou só com espaços
- **THEN** a página MUST NOT chamar o endpoint de envio

#### Scenario: Recusa por tamanho
- **WHEN** o backend responde HTTP 400 ao envio
- **THEN** a página MUST mostrar “A mensagem precisa ter entre 1 e 1000 caracteres.” e manter o texto no campo

#### Scenario: Limite de envio do chat atingido
- **WHEN** o backend responde HTTP 429 ao envio com a mensagem do chat “Limite de mensagens atingido”
- **THEN** a página MUST mostrar “Você enviou muitas mensagens em pouco tempo. Aguarde um minuto.” e manter o texto no campo

#### Scenario: Limite da plataforma atingido no envio
- **WHEN** o backend responde HTTP 429 ao envio com o código `ERROR_CODE_TOO_MANY_REQUESTS` e outra mensagem
- **THEN** a página MUST mostrar “O site está com muitos acessos agora. Tente de novo em instantes.” e manter o texto no campo

#### Scenario: Envio recusado com 404
- **WHEN** o backend responde HTTP 404 ao envio
- **THEN** a página MUST mostrar “Não foi possível enviar. Esta conversa não está mais disponível para novas mensagens.” sem revelar o motivo

#### Scenario: Envio em andamento
- **WHEN** um envio está em andamento
- **THEN** o botão “Enviar” MUST ficar desativado até a resposta, evitando envio duplicado

### Requirement: Texto das mensagens sempre literal
O texto das mensagens, os nomes e os títulos das doações MUST ser apresentados como texto simples. Nenhum conteúdo vindo do chat pode ser interpretado como HTML ou executado.

#### Scenario: Mensagem com marcação HTML
- **WHEN** uma mensagem contém `<b>oi</b> & <script>x</script>`
- **THEN** a página MUST mostrar exatamente esses caracteres, sem negrito e sem executar script

### Requirement: Conversa somente leitura em doação concluída
Quando a doação da conversa aberta estiver concluída, a página MUST manter o histórico legível e MUST desativar o campo e o botão de envio, com o aviso “Esta doação foi concluída. A conversa fica disponível somente para leitura.” Doação disponível ou reservada MUST permitir envio.

#### Scenario: Abrir conversa de doação concluída
- **WHEN** a pessoa abre uma conversa cuja doação está concluída
- **THEN** o histórico MUST aparecer normalmente
- **AND** o campo e o botão “Enviar” MUST ficar desativados, com o aviso de somente leitura

#### Scenario: Doação reservada
- **WHEN** a pessoa abre uma conversa cuja doação está reservada
- **THEN** o campo e o botão “Enviar” MUST continuar ativos

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

### Requirement: Layout em telas estreitas
Em telas estreitas, a página MUST mostrar a lista ou a conversa, uma de cada vez, com um controle para voltar à lista, sem rolagem horizontal.

#### Scenario: Abrir conversa no celular
- **WHEN** a pessoa, numa largura de 360 px, seleciona uma conversa
- **THEN** a conversa MUST ocupar a largura da tela, com um controle “Voltar às conversas”

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

### Requirement: Animação de entrada da página de mensagens
O conteúdo principal de `/chat` MUST usar a animação de entrada `page-fade-enter`, desligada com `prefers-reduced-motion`. O cabeçalho e os dados carregados do Xano MUST NOT ser animados à parte.

#### Scenario: Abrir a página
- **WHEN** a pessoa abre `/chat`
- **THEN** o conteúdo principal MUST entrar com `page-fade-enter`
- **AND** com `prefers-reduced-motion` ativo, MUST aparecer sem animação
