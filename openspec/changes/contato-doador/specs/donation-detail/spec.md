# Spec Delta

## Purpose

Permite ajustar o topo do detalhe da doação para oferecer contato com quem doa sem expor dados privados nem alterar a resposta pública já definida.

## MODIFIED Requirements

### Requirement: Conteúdo do detalhe da doação
A página de detalhe MUST apresentar os dados existentes e aprovados da doação em uma única página, sem exibir campos ou ações fora do escopo.

#### Scenario: Exibir detalhes disponíveis
- **WHEN** uma pessoa abre uma doação disponível
- **THEN** a página MUST apresentar a galeria, o título, a condição com o rótulo “Condição”, a descrição, o nome da categoria, a cidade/UF, a modalidade de entrega, a preferência de contato como texto e o cartão de quem doa com somente primeiro nome e cidade/UF
- **AND** MUST apresentar no topo do cartão os botões “Outros meios de comunicação” e “Chat” em conformidade com o layout aprovado no Figma
- **AND** MUST NOT apresentar botões de acesso ao perfil do doador

#### Scenario: Não apresentar dados ou recursos indisponíveis
- **WHEN** a página exibe os detalhes da doação
- **THEN** MUST permanecerem ocultos Cor, Material, Tipo, bairro, CEP, avaliações, histórico de doações, presença online, indicadores de conta ou e-mail verificados, foto de perfil e qualquer botão ou link para o perfil do doador
- **AND** MUST NOT apresentar esses itens como “Em breve”

## ADDED Requirements

### Requirement: Fluxo de contato do doador
O sistema MUST permitir iniciar contato com quem doa somente de acordo com a preferência de contato e a autenticação da pessoa interessada, sem expor o e-mail na página.

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
- **WHEN** uma pessoa clica em “Chat” no topo do detalhe da doação
- **THEN** a página MUST mostrar “O chat ainda não está disponível.”
- **AND** MUST NOT navegar para outra rota

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
