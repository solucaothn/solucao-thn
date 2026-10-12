# user-account Specification

## Purpose

Define o comportamento de cadastro, autenticação, sessão e manutenção do perfil de uma pessoa usuária do DoaFácil.

## Requirements

### Requirement: Cadastro de conta
O sistema SHALL permitir o cadastro de uma conta com nome, e-mail, senha, cidade e estado, rejeitando e-mails já cadastrados.

#### Scenario: Cadastro válido
- **WHEN** uma pessoa envia dados válidos e um e-mail ainda não utilizado
- **THEN** o sistema cria a conta, emite um token de autenticação e retorna o identificador da conta

#### Scenario: E-mail já cadastrado
- **WHEN** uma pessoa tenta cadastrar um e-mail já associado a uma conta, independentemente de diferenças entre maiúsculas e minúsculas
- **THEN** o sistema rejeita o cadastro e não cria outra conta

#### Scenario: Senha fora dos requisitos
- **WHEN** uma pessoa envia uma senha com menos de oito caracteres, sem letra ou sem dígito
- **THEN** o sistema rejeita o cadastro

### Requirement: Autenticação e emissão de sessão
O sistema SHALL autenticar uma conta por e-mail e senha e emitir um token válido por 24 horas quando as credenciais forem válidas.

#### Scenario: Login válido
- **WHEN** uma pessoa envia as credenciais corretas de uma conta existente
- **THEN** o sistema retorna um token de autenticação e o identificador da conta

#### Scenario: Credenciais inválidas
- **WHEN** o e-mail não corresponde a uma conta ou a senha está incorreta
- **THEN** o sistema rejeita o login com uma resposta de credenciais inválidas

### Requirement: Consulta da sessão autenticada
O sistema SHALL exigir uma sessão válida para consultar os dados da conta autenticada e SHALL rejeitar sessões ausentes, inválidas ou expiradas.

#### Scenario: Consulta com token válido
- **WHEN** uma pessoa consulta sua sessão com um token válido
- **THEN** o sistema retorna o identificador, a data de criação, o nome, o e-mail e o papel associados à própria conta

#### Scenario: Consulta sem sessão válida
- **WHEN** uma pessoa consulta a sessão sem token válido
- **THEN** o sistema rejeita a solicitação sem retornar dados da conta

### Requirement: Consulta e atualização do perfil
O sistema SHALL permitir que uma pessoa autenticada consulte e atualize apenas o próprio perfil, incluindo nome, cidade e estado.

#### Scenario: Consultar perfil
- **WHEN** uma pessoa autenticada solicita seu perfil
- **THEN** o sistema retorna o identificador, a data de criação, o nome, o e-mail, a cidade e o estado da própria conta

#### Scenario: Atualizar perfil
- **WHEN** uma pessoa autenticada envia nome, cidade e estado válidos para atualização
- **THEN** o sistema atualiza esses campos da própria conta e retorna identificador, data de criação, nome, e-mail, cidade e estado atualizados

#### Scenario: Perfil com campo obrigatório inválido
- **WHEN** uma pessoa autenticada envia nome, cidade ou estado vazio
- **THEN** o sistema rejeita a atualização e mantém os valores existentes

### Requirement: Interface pública de login
A aplicação SHALL oferecer uma página pública de login responsiva, coerente com a identidade visual da home e com autenticação somente por e-mail.

#### Scenario: Acessar a página de login
- **WHEN** uma pessoa acessa `/login` ou aciona “Entrar” no cabeçalho da home
- **THEN** a aplicação apresenta cabeçalho branco com logotipo colorido centralizado, fundo creme e cartão branco centralizado
- **AND** o cartão apresenta “Bem-vindo”, “Entre com seu e-mail e senha”, os campos “E-mail” e “Senha”, o link “Esqueci minha senha” alinhado à direita abaixo da senha e o botão verde “Entrar”
- **AND** a página apresenta abaixo do cartão o botão em forma de pílula “Criar conta”
- **AND** não solicita CPF
- **AND** “Esqueci minha senha” e “Criar conta” não navegam nem iniciam outros fluxos

#### Scenario: Alternar a visibilidade da senha
- **WHEN** a pessoa aciona o botão de olho no campo “Senha”
- **THEN** a senha alterna entre oculta e visível, iniciando oculta
- **AND** o ícone e o rótulo acessível alternam entre olho / “Mostrar senha” e olho riscado / “Ocultar senha”
- **AND** o controle é do tipo botão e não envia o formulário

### Requirement: Autenticação da pessoa usuária pela interface
A interface de login SHALL autenticar por e-mail e senha usando o endpoint `auth/login` do grupo Authentication configurado no ambiente do processo da aplicação.

#### Scenario: URL de autenticação configurada
- **WHEN** o processo da aplicação possui `XANO_AUTH_API_URL` com uma URL HTTP(S) válida para o grupo Authentication
- **THEN** a interface envia e-mail e senha ao endpoint `auth/login` sem exigir autenticação prévia
- **AND** não envia nem solicita CPF

#### Scenario: Login bem-sucedido
- **WHEN** o endpoint retorna sucesso com `authToken` e `user_id`
- **THEN** a aplicação guarda o token somente no estado Reflex, sem persistência adicional
- **AND** redireciona a pessoa para a home em `/`

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
