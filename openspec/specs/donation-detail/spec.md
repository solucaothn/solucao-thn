# donation-detail Specification

## Purpose
Permite consultar publicamente uma doação disponível e conhecer seus detalhes, suas fotos e a identificação pública mínima de quem doa.

## Requirements

### Requirement: Consulta pública de detalhe de doação disponível
O sistema MUST permitir consultar uma doação por identificador sem autenticação e MUST expor somente doações com status “disponível”.

#### Scenario: Consultar doação disponível
- **WHEN** uma pessoa consulta o detalhe de uma doação disponível sem sessão
- **THEN** o sistema MUST retornar os dados públicos necessários para o detalhe

#### Scenario: Doação inexistente ou indisponível
- **WHEN** o identificador não corresponde a uma doação ou a doação não está disponível
- **THEN** o sistema MUST responder com o mesmo erro HTTP 404 de doação não encontrada, sem revelar se ela existe ou qual é seu status
- **AND** a página MUST apresentar “Doação não encontrada” no estilo visual do site

### Requirement: Resposta pública limitada e sem dados privados
A resposta do detalhe MUST conter somente os dados da doação aprovados para exibição e MUST NOT expor dados privados de quem doa.

#### Scenario: Dados retornados para o detalhe
- **WHEN** uma consulta pública retorna uma doação disponível
- **THEN** a resposta MUST incluir identificador, título, descrição, condição, nome da categoria, modalidade de entrega, preferência de contato, cidade e UF, fotos ordenadas e primeiro nome de quem doa
- **AND** o primeiro nome MUST ser o único dado nominal de quem doa
- **AND** cidade e UF usadas no cartão de quem doa MUST corresponder à localização da doação

#### Scenario: Campos privados excluídos
- **WHEN** a resposta do detalhe é construída
- **THEN** ela MUST NOT conter e-mail, sobrenome, `owner_id`, endereço, bairro ou CEP de quem doa
- **AND** MUST NOT incluir dados adicionais da conta que não sejam necessários à página

### Requirement: Galeria ordenada da doação
O detalhe MUST apresentar a foto de capa seguida das fotos adicionais da doação em ordem crescente de posição e MUST NOT repetir uma imagem na galeria.

#### Scenario: Doação com capa e fotos adicionais
- **WHEN** a doação possui foto de capa e registros em `donation_photo`
- **THEN** a galeria MUST apresentar a capa primeiro e as fotos adicionais na ordem de posição

#### Scenario: Capa também registrada como foto adicional
- **WHEN** a mesma imagem armazenada como capa também aparece entre os registros de `donation_photo`
- **THEN** a galeria MUST apresentar essa imagem uma única vez, na posição da capa
- **AND** MUST manter as demais fotos adicionais na ordem de posição

#### Scenario: Doação sem fotos retornadas
- **WHEN** a doação não possui foto de capa nem fotos adicionais
- **THEN** a página MUST apresentar a imagem genérica de doação já utilizada nos cartões da home

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

### Requirement: Estados e navegação do detalhe
A página MUST carregar o detalhe pela rota `/doacao/<id>`, validar o identificador antes da consulta e apresentar estados compreensíveis de carregamento e erro, respeitando movimento reduzido.

#### Scenario: Identificador de rota inválido
- **WHEN** o segmento `<id>` não representa um número inteiro positivo, como em `/doacao/abc`, `/doacao/0` ou `/doacao/-1`
- **THEN** a página MUST apresentar “Doação não encontrada”
- **AND** MUST NOT chamar o endpoint do Xano

#### Scenario: Carregamento da doação
- **WHEN** a página inicia a consulta do detalhe
- **THEN** ela MUST apresentar um estado de carregamento sem mostrar conteúdo fictício

#### Scenario: Falha de rede ou resposta inválida
- **WHEN** a consulta falha ou retorna dados inválidos
- **THEN** a página MUST apresentar uma mensagem de erro visualmente consistente com o site
- **AND** MUST NOT apresentar sucesso ou dados de outra doação

#### Scenario: Identificador válido sem correspondência
- **WHEN** o identificador é um número inteiro positivo, mas não corresponde a uma doação disponível, como em `/doacao/999999`
- **THEN** a página MUST consultar o Xano e apresentar “Doação não encontrada” quando o endpoint responder que não há doação disponível

#### Scenario: Entrada na página e movimento reduzido
- **WHEN** a página de detalhe é exibida
- **THEN** o conteúdo principal MUST usar a animação de entrada `page-fade-enter`
- **AND** a animação MUST ser desativada quando `prefers-reduced-motion` estiver ativo
- **AND** o cabeçalho e os dados carregados do Xano MUST NOT ser animados

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
