# Delta da especificação

## ADDED Requirements

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

## MODIFIED Requirements

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
