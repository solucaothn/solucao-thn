## MODIFIED Requirements

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

## ADDED Requirements

### Requirement: Foto da outra pessoa na leitura das mensagens
A leitura das mensagens MUST incluir a URL pública da foto de perfil da outra pessoa participante, ou nula quando ela não tem foto, sem e-mail, sobrenome ou identificador de usuário. A foto da própria pessoa não é devolvida.

#### Scenario: Ler mensagens com a foto da outra pessoa
- **WHEN** uma pessoa participante consulta as mensagens de uma conversa, em qualquer modo
- **THEN** a resposta MUST incluir `other_user_photo`, com a URL pública da foto de perfil da outra pessoa ou nula
- **AND** MUST NOT incluir a foto, o e-mail ou o identificador de usuário da própria pessoa

#### Scenario: Foto removida
- **WHEN** a outra pessoa remove a foto de perfil
- **THEN** a próxima leitura MUST trazer `other_user_photo` nula
