# Delta da especificação

## Purpose

Oferece conversas privadas entre quem doa e cada pessoa interessada em uma doação, com mensagens protegidas por autenticação, autorização e limites no backend.

## ADDED Requirements

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
O endpoint de início ou obtenção de conversa MUST exigir sessão válida e derivar a pessoa interessada de `$auth.id`; uma conversa nova só pode ser criada para doação disponível, pertencente a outra pessoa e com preferência “Chat do DoaFácil”.

#### Scenario: Iniciar conversa elegível
- **WHEN** uma pessoa autenticada que não é dona solicita conversa para uma doação disponível com preferência “Chat do DoaFácil”
- **THEN** o sistema MUST criar ou retornar a conversa da combinação e identificar somente a outra pessoa pelo primeiro nome
- **AND** MUST NOT retornar e-mail ou sobrenome de nenhuma pessoa

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

### Requirement: Envio de mensagens em texto simples
O sistema MUST permitir que somente participantes enviem mensagens de texto simples não vazias, com no máximo 1000 caracteres, em conversas cuja doação esteja disponível ou reservada. Conteúdo de mensagem MUST NOT ser interpretado como HTML.

#### Scenario: Enviar mensagem válida
- **WHEN** uma pessoa participante envia texto não vazio com até 1000 caracteres em conversa de doação disponível ou reservada
- **THEN** o sistema MUST gravar a mensagem com autoria derivada de `$auth.id`
- **AND** MUST retornar a mensagem e o primeiro nome de quem enviou, sem e-mail ou sobrenome

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
- **AND** MUST NOT gravar mensagem nem revelar o status da doação

### Requirement: Leitura autorizada e paginada
O sistema MUST permitir a leitura de mensagens somente às duas pessoas participantes e MUST retornar mensagens em ordem crescente de identificador, usando cursor opcional e limite paginado.

#### Scenario: Ler mensagens como participante
- **WHEN** uma pessoa participante consulta as mensagens com `conversation_id`, `after_message_id` opcional e limite de página
- **THEN** o sistema MUST retornar somente mensagens daquela conversa posteriores ao cursor, em ordem crescente de identificador
- **AND** um limite omitido MUST usar 50 mensagens e um limite solicitado MUST ser limitado ao máximo de 100
- **AND** a resposta MUST indicar se há mais mensagens e permitir continuar a paginação

#### Scenario: Ler conversa concluída
- **WHEN** uma pessoa participante consulta mensagens de conversa cuja doação está concluída
- **THEN** o sistema MUST permitir a leitura do histórico sem permitir novos envios

#### Scenario: Leitura por pessoa não participante
- **WHEN** uma pessoa não participante consulta mensagens de conversa
- **THEN** o endpoint MUST responder com o mesmo erro HTTP 404 genérico usado para conversa inexistente
- **AND** MUST NOT retornar mensagens ou dados dos participantes

#### Scenario: Ausência de dados privados nas mensagens
- **WHEN** a resposta contém mensagens
- **THEN** a identificação nominal de cada remetente MUST conter somente o primeiro nome
- **AND** a resposta MUST NOT conter e-mail ou sobrenome

### Requirement: Listagem das conversas da pessoa
O sistema MUST listar somente conversas das quais a pessoa autenticada participa, ordenadas da atividade mais recente para a mais antiga, com paginação limitada.

#### Scenario: Listar conversas da pessoa autenticada
- **WHEN** uma pessoa autenticada consulta suas conversas
- **THEN** o sistema MUST retornar somente conversas em que `$auth.id` é a pessoa dona ou interessada
- **AND** cada item MUST identificar a outra pessoa somente pelo primeiro nome e não conter e-mail ou sobrenome
- **AND** um limite omitido MUST usar 20 conversas e um limite solicitado MUST ser limitado ao máximo de 50
- **AND** a resposta MUST permitir continuar a paginação

#### Scenario: Pessoa sem conversas
- **WHEN** uma pessoa autenticada não participa de nenhuma conversa
- **THEN** o endpoint MUST retornar uma lista vazia

#### Scenario: Listar sem sessão válida
- **WHEN** uma pessoa sem sessão válida consulta suas conversas
- **THEN** o endpoint MUST responder HTTP 401 sem retornar dados de outras pessoas

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
O sistema MUST registrar pela função existente somente os eventos `chat_started` e `chat_message_sent`, contendo o identificador do usuário ator, a ação e a data, sem registrar conteúdo da conversa ou outros dados pessoais.

#### Scenario: Registrar início de conversa criada
- **WHEN** uma conversa nova é criada com sucesso
- **THEN** o sistema MUST registrar `chat_started` para a pessoa interessada autenticada
- **AND** MUST NOT registrar evento adicional ao apenas retornar uma conversa existente

#### Scenario: Registrar mensagem enviada
- **WHEN** uma mensagem é gravada com sucesso
- **THEN** o sistema MUST registrar `chat_message_sent` para a pessoa remetente autenticada

#### Scenario: Não registrar conteúdo ou leitura
- **WHEN** o sistema registra eventos de chat ou realiza consultas de mensagens e conversas
- **THEN** os eventos MUST NOT conter texto da mensagem, título da doação, identificador da conversa, e-mail, nome, sobrenome ou token
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
