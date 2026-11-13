# donation-chat Specification

## Purpose
Oferece conversas privadas entre quem doa e cada pessoa interessada em uma doação, com mensagens protegidas por autenticação, autorização e limites no backend.

## Requirements

### Requirement: Conversa privada por doação e pessoa interessada
O sistema MUST manter no máximo uma conversa para cada combinação de doação e pessoa interessada, distinta da pessoa dona da doação. Somente essas duas pessoas podem acessar a conversa e suas mensagens.

#### Scenario: Uma conversa por pessoa interessada
- **WHEN** duas pessoas interessadas diferentes iniciam conversa sobre a mesma doação
- **THEN** o sistema MUST manter uma conversa independente para cada pessoa interessada
- **AND** MUST associar cada conversa à pessoa dona da doação e à pessoa interessada autenticada

#### Scenario: Repetição da abertura da mesma conversa
- **WHEN** uma pessoa participante solicita novamente a conversa existente para a mesma doação
- **THEN** o sistema MUST retornar a mesma conversa sem criar outra

#### Scenario: Criações concorrentes para a mesma combinação
- **WHEN** solicitações concorrentes tentam criar conversa para a mesma doação e pessoa interessada
- **THEN** o sistema MUST manter uma única conversa e retornar essa conversa às solicitações elegíveis

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

### Requirement: Listagem das conversas da pessoa
O sistema MUST listar somente conversas das quais a pessoa autenticada participa, ordenadas da atividade mais recente para a mais antiga, com paginação limitada. Cada item MUST incluir o título e o status atual da doação e o número de mensagens não lidas pela pessoa autenticada.

#### Scenario: Listar conversas da pessoa autenticada
- **WHEN** uma pessoa autenticada consulta suas conversas
- **THEN** o sistema MUST retornar somente conversas em que `$auth.id` é a pessoa dona ou interessada
- **AND** cada item MUST identificar a outra pessoa somente pelo primeiro nome e pela URL pública da foto de perfil (`other_user_photo`, nula quando não há foto), e não conter e-mail, sobrenome ou identificador de usuário
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

### Requirement: Limites de envio
O sistema MUST limitar a dez mensagens por pessoa autenticada em qualquer janela móvel de 60 segundos, considerando todas as conversas dessa pessoa. O limite é de melhor esforço: a contagem das mensagens recentes ocorre antes da gravação, sem isolamento serializável, e sob envios concorrentes o limite pode ser excedido por uma ou duas mensagens.

#### Scenario: Envio dentro do limite
- **WHEN** uma pessoa envia até dez mensagens em qualquer janela móvel de 60 segundos
- **THEN** o sistema MUST aceitar cada mensagem que também cumpra os demais requisitos

#### Scenario: Exceder o limite de mensagens
- **WHEN** uma pessoa tenta enviar outra mensagem após atingir dez mensagens em uma janela móvel de 60 segundos
- **THEN** o endpoint MUST responder HTTP 429
- **AND** MUST NOT gravar nem registrar como enviada a mensagem recusada

#### Scenario: Limite compartilhado entre conversas
- **WHEN** uma pessoa envia mensagens em conversas diferentes dentro da mesma janela móvel de 60 segundos
- **THEN** o sistema MUST contabilizar os envios conjuntamente para essa pessoa

#### Scenario: Envios concorrentes perto do limite
- **WHEN** uma pessoa envia mensagens simultâneas quando já está perto de dez mensagens na janela móvel de 60 segundos
- **THEN** o sistema MAY aceitar até duas mensagens além do limite
- **AND** MUST recusar com HTTP 429 os envios feitos depois que a contagem registrada atingir dez

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

### Requirement: Remoção junto com a doação
O sistema MUST remover as conversas e mensagens associadas quando a pessoa dona excluir uma doação, na mesma operação, sem deixar registros órfãos.

#### Scenario: Excluir doação com conversas
- **WHEN** a pessoa dona exclui uma doação que possui conversas e mensagens
- **THEN** o sistema MUST remover as mensagens e conversas associadas junto com a doação
- **AND** a operação MUST concluir integralmente ou não deixar uma exclusão parcial

#### Scenario: Consultar conversa após exclusão da doação
- **WHEN** uma pessoa consulta uma conversa depois que a doação foi excluída
- **THEN** o endpoint MUST responder com o mesmo erro HTTP 404 genérico usado para conversa inexistente
- **AND** MUST NOT retornar mensagens ou dados de participantes

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

### Requirement: Foto da outra pessoa na leitura das mensagens
A leitura das mensagens MUST incluir a URL pública da foto de perfil da outra pessoa participante, ou nula quando ela não tem foto, sem e-mail, sobrenome ou identificador de usuário. A foto da própria pessoa não é devolvida.

#### Scenario: Ler mensagens com a foto da outra pessoa
- **WHEN** uma pessoa participante consulta as mensagens de uma conversa, em qualquer modo
- **THEN** a resposta MUST incluir `other_user_photo`, com a URL pública da foto de perfil da outra pessoa ou nula
- **AND** MUST NOT incluir a foto, o e-mail ou o identificador de usuário da própria pessoa

#### Scenario: Foto removida
- **WHEN** a outra pessoa remove a foto de perfil
- **THEN** a próxima leitura MUST trazer `other_user_photo` nula
