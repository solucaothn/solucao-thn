## ADDED Requirements

### Requirement: Edição das próprias mensagens
O sistema MUST permitir que a pessoa autenticada edite somente as mensagens que ela enviou, até 15 minutos depois do envio, em conversa cuja doação esteja disponível ou reservada. O texto novo segue as regras do envio: texto simples, não vazio e com no máximo 1000 caracteres. A mensagem editada MUST passar a indicar quando foi editada.

#### Scenario: Editar mensagem própria dentro do prazo
- **WHEN** a pessoa que enviou a mensagem informa um texto novo válido até 15 minutos depois do envio, com a doação disponível ou reservada
- **THEN** o sistema MUST gravar o texto novo e o horário da edição em `edited_at`
- **AND** MUST responder HTTP 200 com a mensagem no mesmo formato da leitura, com `sent_by_me` verdadeiro e sem identificadores de usuário
- **AND** MUST manter o identificador, a autoria e o horário de envio da mensagem

#### Scenario: Mensagem de outra pessoa ou inexistente
- **WHEN** a pessoa tenta editar uma mensagem que não existe, que foi enviada pela outra pessoa ou que pertence a conversa da qual ela não participa
- **THEN** o endpoint MUST responder com o mesmo erro HTTP 404 genérico usado para conversa inexistente
- **AND** MUST NOT alterar a mensagem nem revelar qual condição impediu a edição

#### Scenario: Edição em doação concluída
- **WHEN** a pessoa tenta editar uma mensagem própria de conversa cuja doação está concluída
- **THEN** o endpoint MUST responder com o mesmo erro HTTP 404 genérico usado no envio após a conclusão
- **AND** MUST NOT alterar a mensagem

#### Scenario: Edição fora do prazo
- **WHEN** a pessoa tenta editar uma mensagem própria enviada há mais de 15 minutos
- **THEN** o endpoint MUST responder HTTP 400
- **AND** MUST NOT alterar a mensagem

#### Scenario: Texto novo vazio ou acima do limite
- **WHEN** o texto novo, depois de tirar os espaços das pontas, é vazio ou tem mais de 1000 caracteres
- **THEN** o endpoint MUST responder HTTP 400
- **AND** MUST NOT alterar a mensagem

#### Scenario: Texto novo igual ao atual
- **WHEN** o texto novo é igual ao texto atual da mensagem
- **THEN** o sistema MUST responder HTTP 200 com a mensagem sem alterá-la
- **AND** MUST NOT mudar `edited_at` nem registrar evento

#### Scenario: Conteúdo editado com marcação HTML
- **WHEN** o texto novo contém marcação HTML
- **THEN** o sistema MUST tratá-lo como texto simples, como no envio

#### Scenario: Edição sem sessão válida
- **WHEN** uma pessoa sem sessão válida tenta editar uma mensagem
- **THEN** o endpoint MUST responder HTTP 401 sem alterar dados

## MODIFIED Requirements

### Requirement: Envio de mensagens em texto simples
O sistema MUST permitir que somente participantes enviem mensagens de texto simples não vazias, com no máximo 1000 caracteres, em conversas cuja doação esteja disponível ou reservada. Conteúdo de mensagem MUST NOT ser interpretado como HTML. A mensagem gravada MUST ser devolvida marcada como enviada pela própria pessoa.

#### Scenario: Enviar mensagem válida
- **WHEN** uma pessoa participante envia texto não vazio com até 1000 caracteres em conversa de doação disponível ou reservada
- **THEN** o sistema MUST gravar a mensagem com autoria derivada de `$auth.id`
- **AND** MUST retornar a mensagem e o primeiro nome de quem enviou, sem e-mail ou sobrenome
- **AND** MUST retornar `sent_by_me` verdadeiro, sem expor identificadores de usuário
- **AND** MUST retornar `edited_at` vazio, pois a mensagem ainda não foi editada

#### Scenario: Texto vazio ou acima do limite
- **WHEN** uma pessoa envia texto vazio ou com mais de 1000 caracteres
- **THEN** o endpoint MUST rejeitar a solicitação com HTTP 400
- **AND** MUST NOT gravar nem registrar como enviado o conteúdo rejeitado

#### Scenario: Tentativa de enviar conteúdo marcado como HTML
- **WHEN** a mensagem contém marcação HTML
- **THEN** o sistema MUST tratá-la e apresentá-la como texto simples
- **AND** MUST NOT executar nem interpretar elementos, atributos ou scripts HTML

#### Scenario: Envio por pessoa que não participa
- **WHEN** uma pessoa não participante tenta enviar mensagem para uma conversa
- **THEN** o endpoint MUST responder com o mesmo erro HTTP 404 genérico usado para conversa inexistente
- **AND** MUST NOT gravar a mensagem

#### Scenario: Envio após conclusão da doação
- **WHEN** uma pessoa participante tenta enviar mensagem em conversa cuja doação está concluída
- **THEN** o endpoint MUST responder com o mesmo erro HTTP 404 genérico usado para conversa inexistente
- **AND** MUST NOT gravar mensagem nem revelar o status da doação na resposta do envio

### Requirement: Leitura autorizada e paginada
O sistema MUST permitir a leitura de mensagens somente às duas pessoas participantes. Sem cursor, MUST retornar as mensagens mais recentes; com `before_message_id`, as anteriores a ele; com `after_message_id`, as posteriores. A resposta MUST vir em ordem cronológica, com o título e o status da doação, a indicação de autoria e de edição de cada mensagem e até onde a outra pessoa leu. A leitura MUST marcar a conversa como lida para quem lê, até a mensagem mais nova devolvida.

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
- **THEN** a resposta MUST NOT revelar a leitura da outra pessoa além do `other_last_read_message_id` da leitura de mensagens
- **AND** a lista de conversas, o total de não lidas, o envio e a edição MUST NOT revelar até onde a outra pessoa leu

#### Scenario: Confirmação de leitura para quem consulta
- **WHEN** uma pessoa participante consulta as mensagens, em qualquer modo
- **THEN** a resposta MUST incluir `other_last_read_message_id`, o identificador da última mensagem que a **outra** pessoa leu naquela conversa, ou 0 se ela ainda não leu nenhuma
- **AND** MUST NOT incluir outros dados de leitura além desse identificador, como horário da leitura

#### Scenario: Marcar como lida não gera evento
- **WHEN** a leitura atualiza o registro de leitura
- **THEN** o sistema MUST NOT registrar evento de log

#### Scenario: Indicação de edição nas mensagens
- **WHEN** a resposta contém mensagens
- **THEN** cada mensagem MUST incluir `edited_at`, com o horário da última edição, ou vazio se ela nunca foi editada
- **AND** o texto de cada mensagem MUST ser o texto atual, já com a última edição

#### Scenario: Edições desde a consulta anterior
- **WHEN** uma pessoa participante consulta com `after_message_id` e `edited_since`
- **THEN** a resposta MUST incluir `edited_messages`, com as mensagens da conversa de identificador até `after_message_id` editadas a partir de `edited_since`, no mesmo formato das demais mensagens
- **AND** sem `edited_since`, `edited_messages` MUST vir vazia

#### Scenario: Horário do servidor na leitura
- **WHEN** uma pessoa participante consulta as mensagens, em qualquer modo
- **THEN** a resposta MUST incluir `server_time`, o horário do servidor no início da consulta, para ser usado como `edited_since` na consulta seguinte

### Requirement: Registro de eventos sem dados pessoais
O sistema MUST registrar pela função existente somente os eventos `chat_started`, `chat_message_sent` e `chat_message_edited`, contendo o identificador do usuário ator, a ação e a data, sem registrar conteúdo da conversa ou outros dados pessoais.

#### Scenario: Registrar início de conversa criada
- **WHEN** uma conversa nova é criada com sucesso
- **THEN** o sistema MUST registrar `chat_started` para a pessoa interessada autenticada
- **AND** MUST NOT registrar evento adicional ao apenas retornar uma conversa existente

#### Scenario: Registrar mensagem enviada
- **WHEN** uma mensagem é gravada com sucesso
- **THEN** o sistema MUST registrar `chat_message_sent` para a pessoa remetente autenticada

#### Scenario: Registrar mensagem editada
- **WHEN** uma edição altera o texto de uma mensagem
- **THEN** o sistema MUST registrar `chat_message_edited` para a pessoa autenticada, só com `user_id` e a ação
- **AND** edições recusadas ou sem mudança de texto MUST NOT gerar evento

#### Scenario: Não registrar conteúdo ou leitura
- **WHEN** o sistema registra eventos de chat ou realiza consultas de mensagens e conversas
- **THEN** os eventos MUST NOT conter texto da mensagem, texto anterior à edição, título da doação, identificador da conversa ou da mensagem, e-mail, nome, sobrenome ou token
- **AND** consultas de leitura MUST NOT gerar eventos
