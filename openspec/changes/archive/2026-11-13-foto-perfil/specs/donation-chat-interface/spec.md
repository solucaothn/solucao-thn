## MODIFIED Requirements

### Requirement: Lista de conversas
A página `/chat` MUST listar as conversas da pessoa autenticada, da mais recente para a mais antiga. Cada item MUST mostrar o primeiro nome da outra pessoa, o título da doação e a foto de perfil dela (redonda, com `object-fit: cover` e texto alternativo com o primeiro nome) ou, sem foto, um círculo verde com a inicial desse nome, sem sobrenome, e-mail ou indicador “Online”. Conversas com mensagens não lidas MUST mostrar o número delas num círculo verde.

#### Scenario: Pessoa com conversas
- **WHEN** a pessoa autenticada abre `/chat` e participa de conversas
- **THEN** a lista MUST mostrar cada conversa com o primeiro nome da outra pessoa, o título da doação e a foto dela ou, sem foto, o círculo com a inicial, no mesmo tamanho
- **AND** MUST NOT mostrar sobrenome, e-mail ou status de presença

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

## ADDED Requirements

### Requirement: Foto da outra pessoa no cabeçalho da conversa
O cabeçalho da conversa aberta MUST mostrar, antes do primeiro nome da outra pessoa, a foto de perfil dela, redonda, com `object-fit: cover` e texto alternativo com o primeiro nome, ou, sem foto, um círculo verde com a inicial. A foto vem na resposta da leitura das mensagens, sem requisição a mais.

#### Scenario: Conversa com pessoa que tem foto
- **WHEN** a pessoa abre uma conversa e a outra pessoa tem foto de perfil
- **THEN** o cabeçalho MUST mostrar a foto, no mesmo tamanho do círculo da lista
- **AND** MUST NOT fazer requisição além da leitura das mensagens

#### Scenario: Conversa com pessoa sem foto
- **WHEN** a outra pessoa não tem foto
- **THEN** o cabeçalho MUST mostrar o círculo verde com a inicial

#### Scenario: Celular
- **WHEN** a conversa é exibida numa largura de 360 px
- **THEN** a foto, o nome e o título da doação MUST caber no cabeçalho, junto com “Voltar às conversas”, sem rolagem horizontal
