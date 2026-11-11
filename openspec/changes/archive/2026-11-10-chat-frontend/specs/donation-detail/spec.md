## MODIFIED Requirements

### Requirement: Fluxo de contato do doador
O sistema MUST permitir iniciar contato com quem doa somente de acordo com a preferência de contato e a autenticação da pessoa interessada, sem expor o e-mail na página. O botão “Chat” MUST iniciar ou reabrir a conversa pelo endpoint do chat e levar a pessoa a `/chat`, sem revelar por que uma doação não aceita conversa.

#### Scenario: Pessoa sem login solicita outros meios de comunicação
- **WHEN** uma pessoa sem sessão válida clica em “Outros meios de comunicação”
- **THEN** o sistema MUST redirecionar para `/login`
- **AND** MUST NOT chamar o endpoint autenticado de e-mail

#### Scenario: Pessoa logada solicita contato por e-mail
- **WHEN** uma pessoa autenticada clica em “Outros meios de comunicação” em uma doação disponível cuja preferência é “E-mail” e que pertence a outra pessoa
- **THEN** o sistema MUST chamar o endpoint autenticado de e-mail com o token da sessão
- **AND** MUST abrir `mailto:` com o e-mail codificado e um assunto simples que inclua o título da doação
- **AND** MUST remover o e-mail do estado após iniciar o redirecionamento

#### Scenario: Pessoa dona da doação solicita outros meios de comunicação
- **WHEN** a pessoa autenticada que cadastrou a doação clica em “Outros meios de comunicação” na própria doação
- **THEN** o frontend MUST chamar o endpoint autenticado de e-mail, pois a resposta pública do detalhe não contém `owner_id`
- **AND** quando o backend confirmar que a doação existe, está disponível e pertence à pessoa autenticada, MUST responder com HTTP 403 e uma mensagem própria, sem devolver o e-mail
- **AND** o frontend MUST traduzir essa resposta para “Esta é a sua doação.”
- **AND** o frontend MUST NOT receber nem guardar `owner_id`

#### Scenario: Preferência de contato por chat
- **WHEN** uma pessoa autenticada clica em “Outros meios de comunicação” em uma doação cuja preferência é “Chat do DoaFácil”
- **THEN** a página MUST mostrar “Quem doa prefere contato pelo chat.”
- **AND** MUST NOT chamar o endpoint autenticado de e-mail

#### Scenario: Botão Chat
- **WHEN** uma pessoa autenticada clica em “Chat” no topo do detalhe de uma doação que aceita conversa
- **THEN** a página MUST chamar o endpoint de iniciar conversa com o token da sessão e o identificador da doação
- **AND** MUST navegar para `/chat?conversa=<id>` com o identificador devolvido, abrindo essa conversa
- **AND** se a conversa já existir, MUST abrir a mesma conversa, sem criar outra

#### Scenario: Botão Chat sem login
- **WHEN** uma pessoa sem sessão válida clica em “Chat”
- **THEN** o sistema MUST redirecionar para `/login`
- **AND** MUST NOT chamar o endpoint de iniciar conversa

#### Scenario: Botão Chat em doação que não aceita conversa
- **WHEN** o endpoint de iniciar conversa responde HTTP 404, seja porque a preferência é “E-mail”, porque a doação é da própria pessoa ou porque ela não está mais disponível
- **THEN** a página MUST mostrar a mensagem neutra “Não é possível conversar sobre esta doação pelo chat.”
- **AND** MUST NOT navegar para outra rota nem revelar qual condição impediu a conversa

#### Scenario: Falha ao iniciar conversa
- **WHEN** ocorre falha de rede ou o endpoint de iniciar conversa responde com erro diferente de 401 e 404
- **THEN** a página MUST mostrar uma mensagem de erro simples e manter o restante da página funcional
- **AND** quando a resposta for HTTP 401, MUST limpar a sessão transitória e redirecionar para `/login`

#### Scenario: Endpoint sem e-mail disponível
- **WHEN** o endpoint autenticado é chamado sem sessão válida
- **THEN** MUST responder com HTTP 401

#### Scenario: Doação inexistente, indisponível ou com preferência por chat
- **WHEN** o endpoint autenticado recebe uma solicitação para uma doação inexistente, indisponível ou cuja preferência é “Chat do DoaFácil”
- **THEN** MUST responder com o mesmo erro HTTP 404 genérico

#### Scenario: Pessoa autenticada consulta a própria doação
- **WHEN** o endpoint autenticado confirma que a doação existe e está disponível, e que pertence à pessoa autenticada
- **THEN** MUST responder com HTTP 403 e uma mensagem própria
- **AND** MUST NOT devolver o e-mail do doador

#### Scenario: Pessoa autenticada consulta doação elegível de outra pessoa
- **WHEN** o endpoint autenticado confirma que a doação existe, está disponível, pertence a outra pessoa e a preferência é “E-mail”
- **THEN** MUST retornar somente o e-mail de quem doa

#### Scenario: Registro de acesso ao e-mail
- **WHEN** o endpoint autenticado de e-mail recebe uma chamada
- **THEN** o sistema MUST registrar um evento pela função de log existente usando somente `user_id`, ação e data
- **AND** MUST NOT incluir e-mail, nome, título da doação ou token no evento

#### Scenario: Erro ao solicitar contato
- **WHEN** ocorre falha de rede ou o endpoint responde com erro HTTP 401 ou 404
- **THEN** a interface MUST apresentar uma mensagem de erro simples no mesmo estilo visual do site
- **AND** MUST manter o restante da página funcional

#### Scenario: Resposta 403 para doação própria
- **WHEN** o endpoint responde com HTTP 403 porque a doação pertence à pessoa autenticada
- **THEN** a interface MUST mostrar “Esta é a sua doação.”
- **AND** MUST NOT exibir o e-mail
