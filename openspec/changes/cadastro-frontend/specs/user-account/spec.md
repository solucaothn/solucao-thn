# Spec Delta

## ADDED Requirements

### Requirement: Interface pública de cadastro
A aplicação SHALL oferecer uma tela responsiva para criação de conta, alinhada visualmente à tela de login e ao contrato de cadastro existente.

#### Scenario: Exibir formulário de cadastro
- **WHEN** uma pessoa acessa `/cadastro`
- **THEN** a tela apresenta o cabeçalho branco com logotipo centralizado, fundo creme e cartão branco, com o título “Criar sua conta”
- **AND** apresenta, nesta ordem, os campos obrigatórios Nome, E-mail, Cidade, Estado, Senha e Confirmar senha
- **AND** Estado permite selecionar uma das 27 siglas de unidades federativas do Brasil
- **AND** apresenta o botão verde “Criar” e não apresenta campo Telefone

#### Scenario: Validar dados antes do envio
- **WHEN** a pessoa envia campos obrigatórios vazios, e-mail inválido, senha com menos de oito caracteres ou sem letra ou dígito, ou confirmação diferente da senha
- **THEN** o envio é impedido e a tela apresenta mensagem de validação em português que identifica o problema
- **AND** quando um campo obrigatório está vazio, a mensagem própria do site aparece no cartão em vez da validação nativa do navegador

#### Scenario: Enviar cadastro válido
- **WHEN** a pessoa envia Nome, E-mail, Cidade, Estado e uma senha válida com confirmação correspondente
- **THEN** a interface envia ao serviço de cadastro somente `name`, `email`, `password`, `city` e `state`
- **AND** não envia o valor de Confirmar senha
- **AND** apresenta carregamento e impede envios concorrentes até a resposta

#### Scenario: E-mail já cadastrado
- **WHEN** o serviço de cadastro retorna sua indicação distinguível de e-mail já existente
- **THEN** a tela apresenta “Este e-mail já está cadastrado”
- **AND** para qualquer outra rejeição, apresenta mensagem genérica sem expor detalhes internos do serviço

#### Scenario: Falha de rede no cadastro
- **WHEN** a requisição de cadastro falha por conexão ou configuração
- **THEN** a tela apresenta mensagem própria de conexão em português, distinta da mensagem de e-mail já cadastrado

#### Scenario: Cadastro realizado com sucesso
- **WHEN** o serviço retorna `authToken` e `user_id`
- **THEN** a aplicação mantém o token somente no mesmo estado Reflex transitório usado pelo login
- **AND** redireciona a pessoa para a home em `/`

#### Scenario: Alternar visibilidade das senhas
- **WHEN** a pessoa aciona o botão de olho em Senha ou Confirmar senha
- **THEN** apenas o campo correspondente alterna entre oculto e visível, começando oculto
- **AND** cada botão alterna ícone e rótulo acessível entre “Mostrar senha” e “Ocultar senha”
- **AND** os controles são do tipo botão e não enviam o formulário
- **AND** os valores de senha não são persistidos no estado da aplicação nem registrados em logs

#### Scenario: Preservar legibilidade no preenchimento automático
- **WHEN** o navegador preenche automaticamente um campo de login ou cadastro
- **THEN** o campo mantém fundo branco e texto escuro nos estados normal, hover e foco

### Requirement: Navegação entre login e cadastro
A aplicação SHALL permitir que a pessoa navegue entre as telas públicas de login e cadastro e retorne à origem definida para cada tela.

#### Scenario: Abrir cadastro a partir do login
- **WHEN** a pessoa aciona “Criar conta” no login
- **THEN** a aplicação navega para `/cadastro`

#### Scenario: Voltar do cadastro ao login
- **WHEN** a pessoa aciona “← Voltar” na tela de cadastro
- **THEN** a aplicação navega para `/login`

#### Scenario: Voltar do login à home
- **WHEN** a pessoa aciona “← Voltar” na tela de login
- **THEN** a aplicação navega para `/`
