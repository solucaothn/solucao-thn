# user-account Specification

## Purpose

Define o comportamento de cadastro, autenticação, sessão e manutenção do perfil de uma pessoa usuária do DoaFácil.

## Requirements

### Requirement: Cadastro de conta
O sistema SHALL iniciar um cadastro pendente com nome, e-mail, senha, cidade e estado, sem criar conta ou sessão até que o código enviado ao e-mail seja validado.

#### Scenario: Cadastro válido
- **WHEN** uma pessoa envia dados válidos e um e-mail ainda não utilizado
- **THEN** o sistema cria uma pendência e envia um código de confirmação
- **AND** não cria a conta nem emite token de autenticação até a verificação bem-sucedida

#### Scenario: E-mail já cadastrado
- **WHEN** uma pessoa tenta cadastrar um e-mail já associado a uma conta, independentemente de diferenças entre maiúsculas e minúsculas
- **THEN** o sistema não cria pendência nem envia código
- **AND** responde com o mesmo status e corpo neutros usados para um início de cadastro aceito

#### Scenario: Senha fora dos requisitos
- **WHEN** uma pessoa envia uma senha com menos de oito caracteres, sem letra ou sem dígito
- **THEN** o sistema rejeita o início do cadastro sem criar pendência ou conta

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
- **AND** “Esqueci minha senha” leva para `/recuperar-senha`, enquanto “Criar conta” leva para `/cadastro`

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

### Requirement: Interface pública de cadastro
A aplicação SHALL oferecer uma tela responsiva para iniciar a criação de conta, alinhada visualmente à tela de login e ao contrato de cadastro com confirmação de e-mail.

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
- **WHEN** o serviço recebe uma tentativa para e-mail já associado a uma conta
- **THEN** a interface apresenta a mesma confirmação neutra de envio usada para um cadastro elegível
- **AND** não revela se o e-mail já está cadastrado

#### Scenario: Falha de rede no cadastro
- **WHEN** a requisição de cadastro falha por conexão ou configuração
- **THEN** a tela apresenta mensagem própria de conexão em português, sem indicar se o e-mail está cadastrado

#### Scenario: Cadastro realizado com sucesso
- **WHEN** o serviço aceita o início do cadastro
- **THEN** a aplicação mantém a senha somente no estado Reflex transitório enquanto aguarda a confirmação
- **AND** redireciona a pessoa para `/verificar-email` sem guardar token de autenticação ou criar sessão

#### Scenario: Alternar visibilidade das senhas
- **WHEN** a pessoa aciona o botão de olho em Senha ou Confirmar senha
- **THEN** apenas o campo correspondente alterna entre oculto e visível, começando oculto
- **AND** cada botão alterna ícone e rótulo acessível entre “Mostrar senha” e “Ocultar senha”
- **AND** os controles são do tipo botão e não enviam o formulário
- **AND** a senha pode permanecer somente no estado Reflex transitório durante a confirmação e é apagada ao concluir ou ao usar “Usar outro e-mail”
- **AND** a confirmação e todos os valores de senha nunca são registrados em logs

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

### Requirement: Identidade da sessão no cabeçalho da home
A home SHALL representar a sessão autenticada com o primeiro nome da pessoa e permitir que ela encerre a sessão sem adicionar persistência própria em armazenamento do navegador.

#### Scenario: Exibir pessoa autenticada
- **WHEN** a consulta autenticada da conta retorna um nome válido
- **THEN** o cabeçalho exibe “Olá, <primeiro nome>” e o botão “Sair” no lugar de “Entrar”
- **AND** mantém o botão “Quero Doar”

#### Scenario: Consulta da conta falha sem rejeitar o token
- **WHEN** a consulta falha por rede, configuração ou erro do serviço que não indique token inválido
- **THEN** a home permanece disponível e o cabeçalho exibe “Minha conta”
- **AND** o carregamento da contagem e das doações recentes continua independente

#### Scenario: Token rejeitado
- **WHEN** a consulta da conta indica que o token está ausente, inválido ou expirado
- **THEN** a aplicação limpa os dados transitórios da sessão e exibe o cabeçalho de visitante com “Entrar”
- **AND** mantém a home pública disponível

#### Scenario: Encerrar sessão
- **WHEN** a pessoa aciona “Sair”
- **THEN** a aplicação limpa o token e o nome do estado transitório
- **AND** permanece na home com o cabeçalho de visitante

#### Scenario: Manter sessão ao recarregar a mesma aba
- **WHEN** uma pessoa recarrega a home na mesma aba
- **THEN** o estado da sessão permanece disponível nessa aba e o cabeçalho continua autenticado
- **AND** o site não grava o token em armazenamento do navegador

#### Scenario: Não compartilhar sessão com outra aba ou reinício do servidor
- **WHEN** a pessoa abre uma aba nova ou o servidor Reflex é reiniciado
- **THEN** a sessão não está disponível nessa nova aba ou após o reinício e o cabeçalho apresenta “Entrar”
- **AND** o site não restaura a sessão por persistência própria em armazenamento do navegador

#### Scenario: Minimizar dados mantidos para exibição
- **WHEN** a consulta autenticada retorna os dados da conta
- **THEN** o estado de exibição mantém somente o primeiro nome
- **AND** o token e os demais dados da conta não são registrados em logs

### Requirement: Entrada animada nas telas de autenticação
A aplicação SHALL animar somente o cartão das telas públicas de login e cadastro ao abrir cada página.

#### Scenario: Animar o cartão ao abrir login ou cadastro
- **WHEN** uma pessoa abre `/login` ou `/cadastro` com preferência padrão de movimento
- **THEN** somente o cartão branco aparece uma vez com fade e subida de aproximadamente 12px, em cerca de 0,3 segundo com aceleração ease-out
- **AND** o cabeçalho, o fundo, o layout, o foco e o comportamento dos formulários permanecem inalterados

#### Scenario: Respeitar preferência por movimento reduzido
- **WHEN** o sistema operacional ou navegador indica `prefers-reduced-motion: reduce`
- **THEN** os cartões de login e cadastro aparecem sem animação

### Requirement: Entrada suave do conteúdo estático da home
A aplicação SHALL aplicar um fade de entrada ao conteúdo estático da home sem animar o cabeçalho, o rodapé ou dados carregados do Xano.

#### Scenario: Retornar do login para a home
- **WHEN** uma pessoa aciona “← Voltar” no login e a home é exibida
- **THEN** as seções estáticas da home aparecem com fade de opacidade por cerca de 0,3 segundo com aceleração ease-out
- **AND** a animação não altera o layout nem a contagem e o carrossel de doações

#### Scenario: Respeitar movimento reduzido na home
- **WHEN** o sistema operacional ou navegador indica `prefers-reduced-motion: reduce`
- **THEN** as seções estáticas da home aparecem sem animação

### Requirement: Cadastro pendente com código de confirmação
O sistema SHALL manter os dados de um cadastro antes de criar a conta, associados a um e-mail normalizado e único, e SHALL aplicar os limites de validade e reenvio definidos.

#### Scenario: Iniciar cadastro sem conta existente
- **WHEN** uma pessoa envia dados válidos para um e-mail sem conta
- **THEN** o sistema cria ou atualiza no máximo um cadastro pendente para o e-mail normalizado e envia um código de seis dígitos válido por 10 minutos
- **AND** a pendência contém nome, e-mail normalizado, cidade, estado, hash do código, expiração, tentativas, controle de reenvio e expiração da pendência
- **AND** a senha não é armazenada no Xano e nenhuma conta ou sessão é criada

#### Scenario: Manter e-mail único entre pendências
- **WHEN** duas solicitações concorrentes tentam criar uma pendência para o mesmo e-mail normalizado
- **THEN** existe no máximo uma pendência para esse e-mail

#### Scenario: Repetir cadastro para e-mail com pendência
- **WHEN** uma pessoa inicia novamente o cadastro para um e-mail que já tem uma pendência
- **THEN** o sistema atualiza os dados da pendência e envia um novo código somente se os limites de reenvio permitirem
- **AND** preserva o histórico usado para calcular o limite de cinco envios por hora
- **AND** se o reenvio estiver bloqueado, mantém os dados e limites existentes sem redefini-los e responde de forma neutra

#### Scenario: Limitar verificações do código
- **WHEN** uma pessoa envia um código incorreto para uma pendência
- **THEN** o sistema incrementa as tentativas e invalida o código após cinco tentativas
- **AND** todos os códigos têm validade de 10 minutos

#### Scenario: Limitar reenvios
- **WHEN** uma pessoa solicita novo código para uma pendência
- **THEN** o sistema não envia antes de 30 segundos do envio permitido anterior e não permite mais de cinco envios em qualquer período de uma hora
- **AND** um reenvio permitido invalida o código anterior e reinicia as tentativas do novo código

#### Scenario: Expirar e limpar uma pendência
- **WHEN** uma pendência completa 24 horas desde o último envio permitido
- **THEN** ela é considerada expirada e só é removida quando for acessada

### Requirement: Envio neutro do código de cadastro
O sistema SHALL enviar o código de confirmação por uma função própria via SendGrid e SHALL manter respostas neutras para solicitações elegíveis e não elegíveis.

#### Scenario: Solicitação elegível
- **WHEN** uma solicitação pode criar ou atualizar uma pendência e enviar o código
- **THEN** o destinatário recebe uma mensagem própria de confirmação de cadastro que informa o código de seis dígitos e sua validade de 10 minutos

#### Scenario: E-mail já cadastrado, envio limitado ou falha do provedor
- **WHEN** o e-mail já pertence a uma conta, o limite impede o envio ou o provedor falha
- **THEN** o endpoint retorna o mesmo status e corpo neutros da solicitação aceita
- **AND** o endpoint não cria pendência para uma conta existente nem envia código para ela
- **AND** a resposta não revela a causa nem contém e-mail, código, senha ou token

#### Scenario: Reenvio neutro
- **WHEN** uma pessoa solicita reenvio, inclusive para uma pendência inexistente, expirada ou limitada
- **THEN** o endpoint não revela qual dessas condições se aplica

### Requirement: Verificação e criação da conta
O sistema SHALL criar a conta somente após verificar o código da pendência e a senha enviada nessa verificação, sem emitir sessão.

#### Scenario: Código válido e senha válida
- **WHEN** a pessoa apresenta e-mail, código válido e senha que cumpre as regras da conta
- **THEN** o sistema cria a conta com os dados da pendência, remove a pendência e não emite token de sessão

#### Scenario: Código ou pendência inválidos
- **WHEN** a pendência não existe, expirou ou venceu, o código está incorreto, expirou, foi usado ou atingiu cinco tentativas
- **THEN** o sistema não cria a conta e retorna a mesma resposta genérica para todas essas condições

#### Scenario: Senha inválida na verificação
- **WHEN** a senha enviada na verificação tem menos de oito caracteres, não contém letra ou não contém dígito
- **THEN** o sistema não cria a conta nem remove a pendência
- **AND** não registra nem retorna a senha

### Requirement: Interface de verificação do cadastro
A aplicação SHALL reutilizar `/verificar-email` para confirmar cadastro sem alterar o fluxo de recuperação de senha.

#### Scenario: Exibir verificação de cadastro
- **WHEN** a pessoa inicia um cadastro e chega a `/verificar-email`
- **THEN** a tela informa de forma neutra que o código foi enviado ao e-mail parcialmente mascarado
- **AND** apresenta o campo para código de seis dígitos, a contagem de 30 segundos, o reenvio e “Usar outro e-mail”

#### Scenario: Reenviar código de cadastro
- **WHEN** a contagem termina e a pessoa aciona “Reenviar código”
- **THEN** a aplicação chama `POST /auth/signup_resend` com o e-mail do fluxo e reinicia a contagem após a resposta aceita
- **AND** os limites continuam sendo aplicados pelo Xano

#### Scenario: Verificar cadastro
- **WHEN** a pessoa envia o código e a senha mantida para o fluxo
- **THEN** a aplicação chama `POST /auth/signup_verify` com e-mail, código e senha
- **AND** o código não é mantido no estado Reflex nem registrado em logs

#### Scenario: Cadastro confirmado
- **WHEN** `POST /auth/signup_verify` confirma o cadastro
- **THEN** a aplicação apaga a senha do estado Reflex e redireciona para `/login` sem criar sessão

#### Scenario: Usar outro e-mail no cadastro
- **WHEN** a pessoa aciona “Usar outro e-mail” durante a confirmação de cadastro
- **THEN** a aplicação apaga o e-mail e a senha do estado Reflex e retorna a `/cadastro`

#### Scenario: Preservar a recuperação de senha
- **WHEN** a pessoa percorre o fluxo de recuperação em `/verificar-email`
- **THEN** a tela mantém as mensagens, os endpoints, a navegação e os comportamentos já especificados para recuperação de senha

### Requirement: Aviso transitório de cadastro confirmado
A aplicação SHALL informar no login que o cadastro foi confirmado, sem iniciar uma sessão automaticamente.

#### Scenario: Mostrar aviso após confirmar cadastro
- **WHEN** a pessoa conclui a verificação e chega a `/login`
- **THEN** o login apresenta um aviso verde de cadastro confirmado e não mantém sessão autenticada

#### Scenario: Dispensar o aviso de cadastro
- **WHEN** a pessoa começa a digitar, tenta entrar, sai do login ou recarrega a página
- **THEN** a aplicação limpa o aviso transitório de cadastro

### Requirement: Proteção dos dados de confirmação
O sistema SHALL proteger os dados do cadastro pendente e limitar registros de eventos aos dados permitidos.

#### Scenario: Armazenar dados pendentes
- **WHEN** o sistema persiste uma pendência
- **THEN** armazena somente os dados cadastrais necessários, metadados de validade e reenvio e o hash não reversível do código
- **AND** nunca armazena a senha no Xano

#### Scenario: Registrar criação da conta
- **WHEN** uma conta é criada após a confirmação
- **THEN** o sistema registra o evento somente com `user_id`, ação e data
- **AND** não registra e-mail, nome, código, senha ou token
