# Spec Delta

## ADDED Requirements

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
