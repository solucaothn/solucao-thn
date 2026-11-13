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
O sistema SHALL permitir que uma pessoa autenticada consulte e atualize apenas o próprio perfil, incluindo nome, cidade, estado e o texto de Sobre. A consulta também devolve a URL pública da foto de perfil. O e-mail e a foto MUST NOT ser alterados por essa atualização.

#### Scenario: Consultar perfil
- **WHEN** uma pessoa autenticada solicita seu perfil
- **THEN** o sistema retorna o identificador, a data de criação, o nome, o e-mail, a cidade, o estado, o texto de Sobre e a URL pública da foto de perfil da própria conta
- **AND** sem foto, a URL MUST vir nula
- **AND** um Sobre nunca preenchido MUST vir vazio ou nulo

#### Scenario: Atualizar perfil
- **WHEN** uma pessoa autenticada envia nome, cidade, estado e Sobre válidos para atualização
- **THEN** o sistema atualiza esses campos da própria conta e retorna identificador, data de criação, nome, e-mail, cidade, estado e Sobre atualizados
- **AND** o e-mail, a senha, a foto de perfil e as doações já publicadas MUST permanecer iguais

#### Scenario: Perfil com campo obrigatório inválido
- **WHEN** uma pessoa autenticada envia nome, cidade ou estado vazio
- **THEN** o sistema rejeita a atualização e mantém os valores existentes

#### Scenario: Estado fora das unidades federativas
- **WHEN** uma pessoa autenticada envia um estado que não é uma das 27 siglas de unidades federativas do Brasil
- **THEN** o sistema rejeita a atualização com HTTP 400 e mantém os valores existentes

#### Scenario: Sobre sempre gravado
- **WHEN** uma pessoa autenticada envia uma atualização do perfil
- **THEN** o sistema MUST gravar o Sobre em toda atualização: com texto, grava o texto sem os espaços das pontas
- **AND** com o Sobre vazio, nulo ou omitido, MUST gravar o Sobre vazio, apagando o texto anterior
- **AND** um Sobre com mais de 300 caracteres, depois de tirar os espaços das pontas, MUST ser rejeitado com HTTP 400 sem alterar o perfil

#### Scenario: Atualização sem sessão válida
- **WHEN** uma pessoa sem sessão válida tenta atualizar um perfil
- **THEN** o sistema responde HTTP 401 sem alterar dados

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

### Requirement: Página de edição do perfil
A página `/perfil/editar` MUST exigir login e permitir trocar ou remover a foto de perfil e editar nome, Sobre, cidade e estado, com o e-mail só para leitura, seguindo o frame `Group 7` do Figma com as diferenças registradas em `docs/design/README.md`.

#### Scenario: Acesso sem login
- **WHEN** uma pessoa sem sessão válida abre `/perfil/editar` ou recebe HTTP 401 durante o uso
- **THEN** a página MUST levar a `/login` sem mostrar dados

#### Scenario: Entrada pela página Minhas doações
- **WHEN** a pessoa aciona “Editar perfil” no cartão da pessoa em `/minhas-doacoes`
- **THEN** o sistema MUST abrir `/perfil/editar`

#### Scenario: Cabeçalho e título
- **WHEN** a página é exibida, em qualquer estado
- **THEN** a linha do logotipo MUST mostrar, à esquerda, “Voltar a Minhas doações” em `#007A42`, com rótulo acessível e área de toque de pelo menos 44 px, levando a `/minhas-doacoes`
- **AND** o título “Editar perfil” MUST aparecer à esquerda, em negrito e verde

#### Scenario: Formulário preenchido
- **WHEN** a página carrega o perfil com sucesso
- **THEN** MUST mostrar os campos Nome, Sobre, Cidade e Estado preenchidos com os valores atuais
- **AND** o campo Nome MUST conter o nome completo da conta, com a ajuda “Só o primeiro nome aparece para outras pessoas.”
- **AND** o campo Sobre MUST aceitar quebras de linha e mostrar a dica “Não coloque telefone, endereço ou e-mail: este texto é público.”
- **AND** Estado MUST permitir selecionar uma das 27 siglas de unidades federativas do Brasil
- **AND** MUST mostrar o e-mail num campo só de leitura, com o texto “O e-mail é usado para entrar e não pode ser alterado.”
- **AND** o campo de e-mail MUST ser somente leitura e não desativado, para permitir selecionar e copiar, com texto `#1F1F1F` sobre fundo `#F1F1F1`, um ícone de cadeado `#6B6B6B` dentro do campo à direita, o rótulo acessível “E-mail (não pode ser alterado)” e cursor padrão

#### Scenario: Seção Foto
- **WHEN** a página carrega o perfil com sucesso
- **THEN** MUST mostrar, antes de “Dados públicos”, a seção “Foto” com a foto atual (ou o círculo da inicial), o botão “Alterar foto”, os formatos aceitos “JPG, PNG, GIF ou WEBP, até 5 MB” e o aviso “Sua foto aparece para outras pessoas.”
- **AND** “Remover foto” MUST aparecer somente quando a pessoa tem foto
- **AND** os controles MUST ser acessíveis pelo teclado, com área de toque de pelo menos 44 px

#### Scenario: Enviar uma foto nova
- **WHEN** a pessoa escolhe em “Alterar foto” um arquivo JPG, PNG, GIF ou WEBP com até 5 MB
- **THEN** a página MUST enviar a foto na hora, sem depender de “Salvar alterações”, e mostrar um estado de envio
- **AND** no sucesso, a seção “Foto” e a prévia MUST passar a mostrar a foto nova, com uma mensagem curta de sucesso anunciada ao leitor de tela
- **AND** os valores já digitados no formulário MUST permanecer, sem serem salvos

#### Scenario: Arquivo de formato ou tamanho inválido
- **WHEN** a pessoa escolhe um arquivo que não é JPG, PNG, GIF ou WEBP, ou que passa de 5 MB
- **THEN** a página MUST mostrar uma mensagem clara sobre o formato ou o tamanho e MUST NOT enviar a requisição
- **AND** quando o Xano recusar o arquivo com HTTP 400, a página MUST mostrar a mensagem correspondente, mantendo a foto anterior

#### Scenario: Remover a foto
- **WHEN** a pessoa aciona “Remover foto”
- **THEN** a página MUST remover a foto na hora, sem depender de “Salvar alterações”
- **AND** a seção “Foto” e a prévia MUST voltar ao círculo da inicial

#### Scenario: Falha ao enviar ou remover
- **WHEN** ocorre falha de rede, HTTP 429 ou outro erro ao enviar ou remover a foto
- **THEN** a página MUST mostrar uma mensagem de erro simples e manter a foto anterior
- **AND** um HTTP 401 MUST limpar a sessão e levar a `/login`

#### Scenario: Contador do Sobre
- **WHEN** a pessoa digita no campo Sobre
- **THEN** a página MUST mostrar o contador “N/300”, atualizado conforme o texto
- **AND** o campo MUST impedir mais de 300 caracteres

#### Scenario: Prévia do perfil
- **WHEN** a página está com o formulário preenchido
- **THEN** MUST mostrar, à esquerda, uma prévia com a foto de perfil (ou, sem foto, o círculo da inicial), o primeiro nome, “Cidade, UF” e o texto de Sobre, acompanhando o que a pessoa digita
- **AND** a prévia MUST NOT mostrar e-mail, contadores, “Editar perfil” ou “Compartilhar”
- **AND** com o Sobre vazio, a prévia MUST NOT mostrar nada no lugar dele

#### Scenario: Quem vê estas informações
- **WHEN** a página está com o formulário
- **THEN** MUST mostrar o quadro “Quem vê estas informações” com o texto: “Seu primeiro nome, sua foto, cidade, estado e o texto de Sobre aparecem no seu perfil público. Suas doações mostram o primeiro nome, a foto atual e a cidade e o estado do momento em que foram publicadas. Seu e-mail é usado para entrar e só é mostrado a pessoas logadas que pedirem contato numa doação sua com a preferência “E-mail”.”

#### Scenario: Validação antes de enviar
- **WHEN** a pessoa salva com nome ou cidade vazios, estado não selecionado ou Sobre com mais de 300 caracteres
- **THEN** a página MUST indicar o campo a corrigir, MUST NOT enviar a requisição e MUST manter os valores digitados

#### Scenario: Salvar com sucesso
- **WHEN** a pessoa salva valores válidos
- **THEN** a página MUST enviar o formulário inteiro (nome, cidade, estado e Sobre, mesmo vazio) e voltar a `/minhas-doacoes`, que mostra o aviso “Alterações salvas.”
- **AND** o cabeçalho da home MUST passar a mostrar o primeiro nome novo, sem novo login

#### Scenario: Mudar a cidade não altera doações publicadas
- **WHEN** a pessoa muda a cidade ou o estado e salva
- **THEN** as doações já publicadas MUST manter a cidade e a UF do momento da publicação
- **AND** novas doações MUST usar a cidade e a UF novas

#### Scenario: Falha ao salvar
- **WHEN** o Xano recusa a atualização ou ocorre falha de rede ou HTTP 429
- **THEN** a página MUST mostrar uma mensagem de erro simples e manter os valores digitados

#### Scenario: Cancelar
- **WHEN** a pessoa aciona “Cancelar”
- **THEN** a página MUST voltar a `/minhas-doacoes` sem enviar requisição de atualização

#### Scenario: Texto de Sobre literal
- **WHEN** o Sobre contém marcação HTML ou quebras de linha
- **THEN** a prévia, o perfil público e o cartão de Minhas doações MUST apresentá-lo como texto simples, preservando as quebras de linha, sem interpretar HTML

#### Scenario: Texto digitado legível
- **WHEN** a pessoa digita ou cola um texto em Nome, Sobre ou Cidade, inclusive com o tema escuro do sistema
- **THEN** o texto MUST aparecer em `#1F1F1F`, com opacidade total
- **AND** os textos de exemplo MUST aparecer em `#6B6B6B`, com opacidade total

#### Scenario: Layout, contraste e movimento
- **WHEN** a página é exibida numa largura de 360 px
- **THEN** a prévia e o formulário MUST aparecer em uma coluna, sem rolagem horizontal, e Cidade e Estado MAY ficar um abaixo do outro
- **AND** todos os textos e controles MUST ter contraste mínimo AA, inclusive o campo de e-mail só de leitura
- **AND** o cartão do formulário MUST usar a animação de entrada `auth-card-enter`, desativada com `prefers-reduced-motion`

### Requirement: Foto de perfil
O sistema MUST permitir que a pessoa autenticada envie e remova somente a própria foto de perfil, por endpoints próprios. A foto MUST ser uma imagem JPG, PNG, GIF ou WEBP de até 5 MB, guardada com acesso público. A pessoa é sempre derivada da sessão.

#### Scenario: Enviar foto válida
- **WHEN** uma pessoa autenticada envia uma imagem aceita
- **THEN** o sistema MUST guardar a imagem como foto de perfil da própria conta, substituindo a anterior
- **AND** MUST responder com a URL pública da foto nova, sem e-mail nem identificadores

#### Scenario: Formato não aceito
- **WHEN** o arquivo enviado não é JPG, PNG, GIF ou WEBP
- **THEN** o endpoint MUST responder HTTP 400 com a mensagem “Envie uma imagem JPG, PNG, GIF ou WEBP.”
- **AND** MUST NOT alterar a foto atual

#### Scenario: Arquivo grande demais
- **WHEN** o arquivo enviado passa de 5 MB
- **THEN** o endpoint MUST responder HTTP 400 com a mensagem “A foto pode ter no máximo 5 MB.”
- **AND** MUST NOT alterar a foto atual

#### Scenario: Envio sem arquivo
- **WHEN** a requisição de envio não traz arquivo
- **THEN** o endpoint MUST responder HTTP 400 sem alterar a foto atual
- **AND** a mensagem MAY ser a da própria plataforma, que recusa a requisição antes de executar o endpoint; a página só envia com um arquivo escolhido

#### Scenario: Remover a foto
- **WHEN** uma pessoa autenticada remove a foto de perfil
- **THEN** o sistema MUST deixar a conta sem foto, e as respostas que trazem a foto MUST passar a trazê-la nula
- **AND** remover quando já não há foto MUST responder com sucesso, sem erro

#### Scenario: Envio ou remoção sem sessão válida
- **WHEN** uma pessoa sem sessão válida tenta enviar ou remover uma foto
- **THEN** o endpoint MUST responder HTTP 401 sem alterar dados

#### Scenario: Foto de outra pessoa
- **WHEN** qualquer requisição de envio ou remoção é feita
- **THEN** ela MUST alterar somente a conta da sessão, sem aceitar identificador de usuário enviado pelo cliente
