## MODIFIED Requirements

### Requirement: Autenticação da pessoa usuária pela interface
A interface de login SHALL autenticar por e-mail e senha usando o endpoint `auth/login` do grupo Authentication configurado no ambiente do processo da aplicação.

#### Scenario: URL de autenticação configurada
- **WHEN** o processo da aplicação possui `XANO_AUTH_API_URL` com uma URL HTTP(S) válida para o grupo Authentication
- **THEN** a interface envia e-mail e senha ao endpoint `auth/login` sem exigir autenticação prévia
- **AND** não envia nem solicita CPF

#### Scenario: Login bem-sucedido
- **WHEN** o endpoint retorna sucesso com `authToken` e `user_id`
- **THEN** a aplicação guarda o token somente no estado Reflex, sem persistência adicional
- **AND** redireciona a pessoa para o caminho interno de origem recebido em `next`, quando ele for seguro, ou para a home em `/`

#### Scenario: Credenciais rejeitadas
- **WHEN** o endpoint rejeita as credenciais
- **THEN** a interface exibe a mensagem genérica “E-mail ou senha incorretos”, sem indicar se o e-mail existe
- **AND** não guarda token de autenticação

#### Scenario: Falha de rede ou configuração do endpoint
- **WHEN** a requisição não pode ser concluída por falha de rede ou por URL de autenticação ausente ou inválida
- **THEN** a interface exibe uma mensagem própria de falha de conexão, distinta da mensagem de credenciais incorretas
- **AND** não guarda token de autenticação

#### Scenario: Requisição de login em andamento
- **WHEN** a requisição de autenticação está em andamento
- **THEN** o botão “Entrar” apresenta estado de carregamento e não permite envios concorrentes

## ADDED Requirements

### Requirement: Volta à página de origem depois do login
Toda ida ao login a partir de uma página do site SHALL levar o caminho dessa página no parâmetro `next`, e o login bem-sucedido SHALL voltar a ele. O `next` SHALL ser aceito só se for um caminho interno do site; qualquer outro valor MUST levar à home.

#### Scenario: Ação que exige sessão
- **WHEN** uma pessoa sem sessão aciona algo que exige login (por exemplo, “Chat” ou o contato no detalhe da doação, “Quero Doar”, Minhas doações, Mensagens ou Editar perfil)
- **THEN** a aplicação MUST abrir `/login?next=<caminho da página de origem>`
- **AND** depois do login bem-sucedido MUST abrir esse caminho

#### Scenario: Entrar pelo cabeçalho, pelo menu ou pelo botão de mensagens
- **WHEN** uma pessoa sem sessão aciona “Entrar” no cabeçalho ou no menu do celular, ou o botão flutuante de mensagens, numa página do site
- **THEN** o login MUST receber o caminho dessa página em `next` e voltar a ela depois de entrar

#### Scenario: Cadastro no meio do caminho
- **WHEN** a pessoa chega ao login com `next` e escolhe “Criar conta”
- **THEN** o `next` MUST seguir pelo cadastro e pela confirmação do e-mail até o login
- **AND** depois de entrar com a conta nova, a pessoa MUST voltar ao caminho de origem

#### Scenario: Endereço externo ou inválido em next
- **WHEN** o `next` não começa com uma única `/`, contém esquema, host, `//`, `\` ou caracteres de controle, aponta para uma tela de autenticação ou passa de 512 caracteres
- **THEN** a aplicação MUST ignorá-lo e levar à home depois do login, sem nunca abrir um endereço fora do site
