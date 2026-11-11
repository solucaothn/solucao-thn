## ADDED Requirements

### Requirement: Total de mensagens não lidas
O sistema MUST oferecer um endpoint autenticado e leve que devolve somente o total de mensagens não lidas da pessoa autenticada, somando todas as conversas de que ela participa. Contam como não lidas apenas mensagens enviadas pela outra pessoa e posteriores à última mensagem que a pessoa leu naquela conversa.

#### Scenario: Total com mensagens não lidas
- **WHEN** uma pessoa autenticada consulta o total e tem mensagens não lidas em uma ou mais conversas
- **THEN** o endpoint MUST responder HTTP 200 com `unread_total` igual à soma das não lidas de todas as suas conversas
- **AND** a resposta MUST NOT conter mensagens, nomes, títulos ou identificadores de conversa

#### Scenario: Sem mensagens não lidas ou sem conversas
- **WHEN** a pessoa autenticada leu todas as mensagens ou não participa de nenhuma conversa
- **THEN** o endpoint MUST responder `unread_total` igual a 0

#### Scenario: Mensagens da própria pessoa não contam
- **WHEN** a pessoa enviou mensagens que a outra pessoa ainda não leu
- **THEN** essas mensagens MUST NOT entrar no total de quem as enviou

#### Scenario: Total sem sessão válida
- **WHEN** uma pessoa sem sessão válida consulta o total
- **THEN** o endpoint MUST responder HTTP 401 sem retornar dados

## MODIFIED Requirements

### Requirement: Leitura autorizada e paginada
O sistema MUST permitir a leitura de mensagens somente às duas pessoas participantes. Sem cursor, MUST retornar as mensagens mais recentes; com `before_message_id`, as anteriores a ele; com `after_message_id`, as posteriores. A resposta MUST vir em ordem cronológica, com o título e o status da doação e a indicação de autoria de cada mensagem. A leitura MUST marcar a conversa como lida para quem lê, até a mensagem mais nova devolvida.

#### Scenario: Ler mensagens como participante
- **WHEN** uma pessoa participante consulta as mensagens com `conversation_id` e limite de página, sem cursor
- **THEN** o sistema MUST retornar as últimas mensagens daquela conversa, até o limite, em ordem crescente de identificador
- **AND** um limite omitido MUST usar 50 mensagens e um limite solicitado MUST ser limitado ao máximo de 100
- **AND** a resposta MUST indicar com `has_older` se existem mensagens anteriores à primeira retornada

#### Scenario: Carregar mensagens anteriores
- **WHEN** uma pessoa participante consulta com `before_message_id`
- **THEN** o sistema MUST retornar as mensagens imediatamente anteriores a esse identificador, até o limite, em ordem crescente de identificador
- **AND** MUST indicar com `has_older` se ainda existem mensagens anteriores

#### Scenario: Buscar mensagens novas
- **WHEN** uma pessoa participante consulta com `after_message_id`
- **THEN** o sistema MUST retornar somente mensagens posteriores a esse identificador, até o limite, em ordem crescente de identificador
- **AND** MUST indicar com `has_newer` se existem mais mensagens posteriores além das retornadas

#### Scenario: Dois cursores ao mesmo tempo
- **WHEN** a consulta informa `before_message_id` e `after_message_id` juntos
- **THEN** o endpoint MUST rejeitar a solicitação com HTTP 400

#### Scenario: Dados da doação e autoria na leitura
- **WHEN** uma pessoa participante consulta as mensagens
- **THEN** a resposta MUST incluir `donation_title` e `donation_status` da doação da conversa
- **AND** cada mensagem MUST incluir `sent_by_me`, verdadeiro somente quando a pessoa autenticada a enviou, sem expor identificadores de usuário

#### Scenario: Ler conversa concluída
- **WHEN** uma pessoa participante consulta mensagens de conversa cuja doação está concluída
- **THEN** o sistema MUST permitir a leitura do histórico sem permitir novos envios
- **AND** `donation_status` MUST ser “concluída”

#### Scenario: Leitura por pessoa não participante
- **WHEN** uma pessoa não participante consulta mensagens de conversa
- **THEN** o endpoint MUST responder com o mesmo erro HTTP 404 genérico usado para conversa inexistente
- **AND** MUST NOT retornar mensagens ou dados dos participantes

#### Scenario: Ausência de dados privados nas mensagens
- **WHEN** a resposta contém mensagens
- **THEN** a identificação nominal de cada remetente MUST conter somente o primeiro nome
- **AND** a resposta MUST NOT conter e-mail ou sobrenome

#### Scenario: Leitura marca a conversa como lida
- **WHEN** uma pessoa participante lê mensagens da conversa, em qualquer modo, e a mensagem mais nova devolvida é posterior à última que ela já tinha lido
- **THEN** o sistema MUST registrar essa mensagem como a última lida por essa pessoa naquela conversa
- **AND** MUST NOT alterar o registro de leitura da outra pessoa

#### Scenario: Leitura não volta atrás
- **WHEN** a pessoa carrega mensagens anteriores ou a consulta não devolve mensagens novas
- **THEN** o registro de leitura dessa pessoa MUST permanecer igual ou avançar, nunca recuar

#### Scenario: Sem confirmação de leitura para a outra pessoa
- **WHEN** qualquer endpoint do chat responde a uma pessoa participante
- **THEN** a resposta MUST NOT revelar até qual mensagem a outra pessoa leu

#### Scenario: Marcar como lida não gera evento
- **WHEN** a leitura atualiza o registro de leitura
- **THEN** o sistema MUST NOT registrar evento de log

### Requirement: Listagem das conversas da pessoa
O sistema MUST listar somente conversas das quais a pessoa autenticada participa, ordenadas da atividade mais recente para a mais antiga, com paginação limitada. Cada item MUST incluir o título e o status atual da doação e o número de mensagens não lidas pela pessoa autenticada.

#### Scenario: Listar conversas da pessoa autenticada
- **WHEN** uma pessoa autenticada consulta suas conversas
- **THEN** o sistema MUST retornar somente conversas em que `$auth.id` é a pessoa dona ou interessada
- **AND** cada item MUST identificar a outra pessoa somente pelo primeiro nome e não conter e-mail ou sobrenome
- **AND** cada item MUST incluir `donation_title` e `donation_status`
- **AND** um limite omitido MUST usar 20 conversas e um limite solicitado MUST ser limitado ao máximo de 50
- **AND** a resposta MUST permitir continuar a paginação

#### Scenario: Pessoa sem conversas
- **WHEN** uma pessoa autenticada não participa de nenhuma conversa
- **THEN** o endpoint MUST retornar uma lista vazia

#### Scenario: Listar sem sessão válida
- **WHEN** uma pessoa sem sessão válida consulta suas conversas
- **THEN** o endpoint MUST responder HTTP 401 sem retornar dados de outras pessoas

#### Scenario: Contador de não lidas por conversa
- **WHEN** uma pessoa autenticada consulta suas conversas
- **THEN** cada item MUST incluir `unread_count`, igual ao número de mensagens enviadas pela outra pessoa e posteriores à última mensagem que a pessoa autenticada leu naquela conversa
- **AND** as mensagens enviadas pela própria pessoa MUST NOT contar
- **AND** uma conversa totalmente lida MUST ter `unread_count` igual a 0
