## MODIFIED Requirements

### Requirement: Elegibilidade para iniciar conversa
O endpoint de início ou obtenção de conversa MUST exigir sessão válida e derivar a pessoa interessada de `$auth.id`; uma conversa nova só pode ser criada para doação disponível, pertencente a outra pessoa e com preferência “Chat do DoaFácil”. A resposta MUST incluir o título e o status atual da doação.

#### Scenario: Iniciar conversa elegível
- **WHEN** uma pessoa autenticada que não é dona solicita conversa para uma doação disponível com preferência “Chat do DoaFácil”
- **THEN** o sistema MUST criar ou retornar a conversa da combinação e identificar somente a outra pessoa pelo primeiro nome
- **AND** MUST NOT retornar e-mail ou sobrenome de nenhuma pessoa
- **AND** MUST retornar `donation_title` e `donation_status` da doação da conversa

#### Scenario: Solicitação sem sessão válida
- **WHEN** uma pessoa sem sessão válida solicita iniciar ou obter conversa
- **THEN** o endpoint MUST responder HTTP 401 sem retornar dados da conversa

#### Scenario: Doação ou conversa não elegível
- **WHEN** a doação não existe, não está disponível para criar conversa, pertence à pessoa solicitante ou tem preferência diferente de “Chat do DoaFácil”
- **THEN** o endpoint MUST responder com o mesmo erro HTTP 404 genérico
- **AND** MUST NOT revelar qual condição impediu a solicitação

#### Scenario: Participante obtém conversa já existente
- **WHEN** uma pessoa participante solicita uma conversa existente cuja doação passou a reservada ou concluída
- **THEN** o sistema MUST retornar a mesma conversa sem criar uma nova
- **AND** as permissões de envio e leitura MUST continuar obedecendo ao status atual da doação
- **AND** `donation_status` MUST refletir o status atual

### Requirement: Envio de mensagens em texto simples
O sistema MUST permitir que somente participantes enviem mensagens de texto simples não vazias, com no máximo 1000 caracteres, em conversas cuja doação esteja disponível ou reservada. Conteúdo de mensagem MUST NOT ser interpretado como HTML. A mensagem gravada MUST ser devolvida marcada como enviada pela própria pessoa.

#### Scenario: Enviar mensagem válida
- **WHEN** uma pessoa participante envia texto não vazio com até 1000 caracteres em conversa de doação disponível ou reservada
- **THEN** o sistema MUST gravar a mensagem com autoria derivada de `$auth.id`
- **AND** MUST retornar a mensagem e o primeiro nome de quem enviou, sem e-mail ou sobrenome
- **AND** MUST retornar `sent_by_me` verdadeiro, sem expor identificadores de usuário

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
O sistema MUST permitir a leitura de mensagens somente às duas pessoas participantes. Sem cursor, MUST retornar as mensagens mais recentes; com `before_message_id`, as anteriores a ele; com `after_message_id`, as posteriores. A resposta MUST vir em ordem cronológica, com o título e o status da doação e a indicação de autoria de cada mensagem.

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

### Requirement: Listagem das conversas da pessoa
O sistema MUST listar somente conversas das quais a pessoa autenticada participa, ordenadas da atividade mais recente para a mais antiga, com paginação limitada. Cada item MUST incluir o título e o status atual da doação.

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
