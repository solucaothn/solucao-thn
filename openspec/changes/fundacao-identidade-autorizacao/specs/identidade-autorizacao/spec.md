## Purpose

Permitir que usuários criem contas, autentiquem-se com credenciais básicas e gerenciem apenas seus próprios dados, com regras de autorização executadas no backend e não dependentes da interface.

## ADDED Requirements

### Requirement: Cadastro de usuário com localização
O sistema SHALL permitir que uma pessoa crie uma conta com nome, e-mail, senha e localização associada, validando a unicidade do e-mail e os dados obrigatórios antes de persistir o usuário.

#### Scenario: Cadastro válido com dados completos
- **WHEN** um visitante fornece nome, e-mail único, senha válida e localização obrigatória
- **THEN** o sistema cria o usuário e registra a localização associada à conta

#### Scenario: E-mail duplicado
- **WHEN** um visitante tenta cadastrar um e-mail já existente no sistema
- **THEN** o sistema rejeita a criação e informa que o e-mail já está em uso

#### Scenario: Dados obrigatórios ausentes
- **WHEN** um visitante tenta cadastrar sem nome, e-mail, senha ou localização
- **THEN** o sistema rejeita a operação e informa quais campos são obrigatórios

### Requirement: Autenticação básica do usuário
O sistema SHALL autenticar o usuário usando e-mail e senha, emitindo ou retornando uma sessão ou token válido somente para o usuário autenticado, e rejeitando credenciais inválidas sem revelar detalhes sensíveis da conta.

#### Scenario: Login com credenciais válidas
- **WHEN** um usuário informa e-mail e senha corretos
- **THEN** o sistema autentica a conta e concede acesso à sessão ou token válido

#### Scenario: Login com senha incorreta
- **WHEN** um usuário informa e-mail correto e senha incorreta
- **THEN** o sistema rejeita o login e exige nova tentativa sem expor informações da conta

#### Scenario: Login com usuário inexistente
- **WHEN** um usuário tenta entrar com um e-mail não cadastrado
- **THEN** o sistema rejeita o login de forma segura e sem revelar se o e-mail existe ou não

### Requirement: Acesso e edição do perfil próprio
O sistema SHALL permitir que um usuário autenticado leia e edite apenas seu próprio perfil, incluindo dados pessoais e localização, e SHALL impedir qualquer acesso ou modificação em perfis de outros usuários.

#### Scenario: Usuário consulta seu próprio perfil
- **WHEN** um usuário autenticado solicita seus dados de perfil
- **THEN** o sistema retorna somente as informações do próprio usuário

#### Scenario: Usuário tenta acessar outro perfil
- **WHEN** um usuário autenticado solicita os dados de outro usuário
- **THEN** o sistema nega o acesso e não expõe informações do perfil alheio

#### Scenario: Usuário edita seu próprio perfil
- **WHEN** um usuário autenticado atualiza seus próprios dados cadastrais ou localização
- **THEN** o sistema grava as alterações e retorna o perfil atualizado

#### Scenario: Usuário tenta editar perfil de outra pessoa
- **WHEN** um usuário autenticado tenta alterar os dados de outro usuário
- **THEN** o sistema rejeita a operação com falha de autorização no backend

### Requirement: Autorização reforçada no backend
O sistema SHALL aplicar regras de autorização no backend para todos os acessos e alterações sensíveis, de modo que o frontend nunca seja a única validação da permissão.

#### Scenario: Requisição autenticada com permissão válida
- **WHEN** um usuário autenticado solicita um recurso próprio
- **THEN** o backend valida a sessão e permite a operação

#### Scenario: Requisição com usuário sem permissão
- **WHEN** um usuário tenta acessar ou alterar um recurso que não pertence a ele
- **THEN** o backend bloqueia a ação e responde com erro de autorização

#### Scenario: Frontend sem validação de segurança
- **WHEN** a interface tenta contornar a regra de posse por meio de dados do cliente
- **THEN** o backend continua rejeitando a operação porque a autorização é validada no servidor