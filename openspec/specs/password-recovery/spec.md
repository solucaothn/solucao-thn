# password-recovery Specification

## Purpose

Permite que uma pessoa redefina a senha da conta por meio de um código temporário enviado ao e-mail cadastrado, sem criar uma sessão autenticada durante o processo.

## Requirements

### Requirement: Solicitação de código com resposta neutra
O sistema SHALL oferecer uma solicitação pública de código de recuperação cuja resposta não revele se o e-mail está cadastrado nem se o envio foi limitado ou falhou.

#### Scenario: E-mail cadastrado e elegível
- **WHEN** uma pessoa solicita um código para uma conta elegível
- **THEN** o sistema gera um código de seis dígitos com fonte aleatória segura, válido por 10 minutos, e envia o código ao e-mail da própria conta
- **AND** invalida qualquer código pendente anterior da conta
- **AND** responde com o mesmo status e corpo usados para e-mail inexistente, solicitação limitada ou falha de envio

#### Scenario: E-mail inexistente, limite atingido ou falha de envio
- **WHEN** uma solicitação usa um e-mail inexistente, excede um limite ou o provedor de e-mail falha
- **THEN** o sistema retorna exatamente o mesmo status e corpo da solicitação aceita
- **AND** não revela a causa nem inclui código, e-mail, token, hash ou chave na resposta

#### Scenario: Limites de emissão por conta
- **WHEN** uma conta recebe solicitações de recuperação
- **THEN** o sistema não envia novo código antes de 30 segundos desde o envio anterior
- **AND** não envia mais de cinco códigos por conta em qualquer período de uma hora

### Requirement: Código de recuperação verificável e de uso limitado
O sistema SHALL verificar códigos sem revelar a existência da conta e SHALL limitar tentativas de verificação.

#### Scenario: Código válido
- **WHEN** a pessoa apresenta e-mail e código existente, não expirado, não usado e com menos de cinco tentativas incorretas
- **THEN** o sistema invalida o código e devolve um token de redefinição aleatório, de uso único e válido por 10 minutos

#### Scenario: Código inválido, expirado, usado, bloqueado ou e-mail inexistente
- **WHEN** a verificação falha por qualquer uma dessas causas
- **THEN** o sistema retorna a mesma resposta genérica, com status e corpo idênticos para todas elas
- **AND** uma tentativa incorreta de conta existente incrementa seu contador e a quinta tentativa invalida o código

### Requirement: Confirmação de nova senha
O sistema SHALL aceitar a troca de senha somente com token de redefinição válido e senha que cumpra as regras da conta.

#### Scenario: Token válido e senha confirmada
- **WHEN** a pessoa apresenta um token não usado e não expirado, uma senha com no mínimo oito caracteres e ao menos uma letra e um dígito, e uma confirmação igual
- **THEN** o sistema atualiza a senha, marca o token como usado e invalida os códigos pendentes da conta
- **AND** não emite token de sessão; a pessoa precisa entrar pelo login

#### Scenario: Token inválido, expirado ou usado
- **WHEN** a pessoa tenta confirmar uma senha com token inexistente, expirado ou já usado
- **THEN** o sistema não altera a senha nem emite sessão

#### Scenario: Senha fora da regra ou confirmação diferente
- **WHEN** a senha não cumpre a regra da conta ou a confirmação é diferente
- **THEN** o sistema não altera a senha nem marca o token como concluído

### Requirement: Envio de código por e-mail
O sistema SHALL enviar o código por uma função interna usando o SendGrid, sem link de recuperação no conteúdo.

#### Scenario: Mensagem de recuperação
- **WHEN** uma solicitação elegível gera um código
- **THEN** o destinatário é o e-mail da conta solicitante
- **AND** assunto e mensagem são fixos, em português, e informam somente o código e sua validade de 10 minutos, sem links

### Requirement: Armazenamento e registro seguros
O sistema SHALL proteger credenciais temporárias em repouso e não registrar dados pessoais ou segredos do fluxo.

#### Scenario: Persistência de código e token
- **WHEN** o sistema armazena um código ou token de redefinição
- **THEN** persiste somente um hash não reversível do valor e os metadados necessários de validade, tentativas e uso
- **AND** não altera nem utiliza `user.password_reset`

#### Scenario: Registro de evento de recuperação
- **WHEN** o sistema registra solicitação ou conclusão de recuperação
- **THEN** o evento contém somente a associação própria ao usuário, quando houver, e a ação
- **AND** nenhum log ou erro, nem resposta diferente do sucesso de verificação, contém e-mail, código, token, hash ou chave

### Requirement: Solicitar código pela interface
A aplicação SHALL oferecer uma tela pública para solicitar um código de recuperação pelo e-mail da conta.

#### Scenario: Exibir a tela de solicitação
- **WHEN** uma pessoa acessa `/recuperar-senha`
- **THEN** a aplicação mostra cabeçalho branco com logotipo, fundo creme, cartão branco com animação `auth-card-enter`, título “Esqueceu a senha?”, campo E-mail, botão “Continuar” e link “← Voltar” para `/login`

#### Scenario: Solicitação aceita pelo Xano
- **WHEN** a pessoa envia um e-mail válido e `reset/request_code` responde com `{success: true}`
- **THEN** a aplicação avança para `/verificar-email` independentemente de existir uma conta para o e-mail
- **AND** mantém o e-mail somente no estado Reflex enquanto o fluxo estiver em andamento

#### Scenario: Falha de conexão ao solicitar código
- **WHEN** a requisição não pode ser concluída por falha de rede ou configuração do endpoint
- **THEN** a tela apresenta uma mensagem própria e genérica de falha de conexão
- **AND** não indica se o e-mail está cadastrado nem avança para a verificação

#### Scenario: Requisição em andamento
- **WHEN** a solicitação está sendo enviada
- **THEN** o botão apresenta carregamento e não permite envios concorrentes

### Requirement: Verificar o código na interface
A aplicação SHALL permitir verificar o código de seis dígitos sem revelar a existência da conta.

#### Scenario: Exibir a tela de verificação
- **WHEN** a pessoa chega à rota `/verificar-email`
- **THEN** a aplicação apresenta cartão com `auth-card-enter`, título “Verifique seu e-mail”, e-mail mascarado mostrando a primeira letra, `***` e domínio, campo Código, a dica “Pode demorar um minutinho. Olha também no spam.”, botão “Continuar” e link “← Voltar” para `/recuperar-senha`
- **AND** exibe a mensagem neutra “Se existir uma conta com esse e-mail, enviamos um código de 6 dígitos para <e-mail mascarado>.”
- **AND** o valor do código não é mantido no estado Reflex nem registrado em logs

#### Scenario: Reenvio após a contagem regressiva
- **WHEN** a tela de verificação é exibida após uma solicitação
- **THEN** a aplicação apresenta “Reenviar código em 0:30” e atualiza a contagem regressiva até zero
- **AND** ao zerar, apresenta o link “Reenviar código”, que chama `reset/request_code` novamente
- **AND** a proteção contra reenvios continua sendo imposta pelo Xano

#### Scenario: Usar outro e-mail
- **WHEN** a pessoa aciona “Usar outro e-mail”
- **THEN** a aplicação apaga o e-mail do estado e retorna para `/recuperar-senha`

#### Scenario: Código verificado com sucesso
- **WHEN** `reset/verify_code` responde `{success: true, reset_token: <token>}`
- **THEN** a aplicação guarda o reset token somente no estado Reflex e avança para `/nova-senha`
- **AND** não coloca o token na URL, no armazenamento do navegador, em logs ou em mensagens

#### Scenario: Código inválido, expirado ou bloqueado
- **WHEN** `reset/verify_code` responde `{success: false}` por qualquer causa
- **THEN** a aplicação mostra a mensagem única “Código inválido ou vencido. Confira e tente de novo, ou peça um novo código.”

#### Scenario: Falha de conexão ao verificar código
- **WHEN** a requisição de verificação não pode ser concluída por falha de rede ou configuração
- **THEN** a aplicação mostra uma mensagem genérica de falha de conexão, sem detalhes do serviço

### Requirement: Definir nova senha pela interface
A aplicação SHALL permitir definir nova senha somente depois da verificação do código e validar os dados antes de chamar o Xano.

#### Scenario: Exibir a tela de nova senha
- **WHEN** a pessoa chega à rota `/nova-senha` após verificar o código
- **THEN** a aplicação apresenta cartão com `auth-card-enter`, título “Altere sua senha”, campos “Nova senha” e “Confirmar senha”, cada um com controle acessível e independente para mostrar ou ocultar a senha, botão “Salvar nova senha” e link “← Voltar” para `/login`

#### Scenario: Validar os campos antes do envio
- **WHEN** a pessoa envia uma senha com menos de oito caracteres, sem letra, sem dígito ou uma confirmação diferente
- **THEN** o envio é impedido e a aplicação apresenta a mensagem de validação em português correspondente
- **AND** nenhum valor de senha ou confirmação é armazenado no estado Reflex ou registrado em logs

#### Scenario: Salvar senha com token válido
- **WHEN** os campos são válidos e `reset/confirm_password` responde `{success: true}`
- **THEN** a aplicação apaga o reset token e o e-mail do estado, limpa os dados transitórios do fluxo e redireciona para `/login`
- **AND** prepara um aviso verde “Senha alterada com sucesso! Entre com a sua nova senha.”

#### Scenario: Token inválido ou expirado
- **WHEN** os campos são válidos e `reset/confirm_password` responde `{success: false}`
- **THEN** a aplicação mostra “O tempo para trocar a senha acabou. Peça um novo código.” e um link para `/recuperar-senha`
- **AND** apaga o reset token e o e-mail do estado

#### Scenario: Falha de conexão ao salvar senha
- **WHEN** a requisição de confirmação não pode ser concluída por falha de rede ou configuração
- **THEN** a aplicação mostra uma mensagem própria e genérica de falha de conexão
- **AND** não mostra detalhes da resposta ou do serviço

#### Scenario: Requisição de confirmação em andamento
- **WHEN** a nova senha está sendo enviada
- **THEN** o botão apresenta carregamento e não permite envios concorrentes

### Requirement: Aviso transitório de senha alterada no login
A aplicação SHALL apresentar o aviso de sucesso no login somente na navegação que conclui a recuperação.

#### Scenario: Mostrar o aviso após redefinir a senha
- **WHEN** a recuperação termina com sucesso e a pessoa é redirecionada para `/login`
- **THEN** o login mostra, entre o subtítulo e o campo E-mail, uma faixa verde clara com ícone de check e o texto “Senha alterada com sucesso! Entre com a sua nova senha.”
- **AND** a faixa é anunciada como mensagem de status para leitores de tela

#### Scenario: Consumir ou dispensar o aviso
- **WHEN** a pessoa começa a digitar, clica em “Entrar”, sai da página de login, recarrega a página ou retorna a ela pelo histórico
- **THEN** a aplicação apaga o indicador transitório e não volta a mostrar o aviso

### Requirement: Segurança e tratamento transitório dos dados de recuperação
A aplicação SHALL limitar o estado da recuperação a e-mail e token temporário, tratar credenciais e mensagens de erro com segurança e apresentar as páginas de forma acessível e responsiva.

#### Scenario: Dados transitórios e fim do fluxo
- **WHEN** a pessoa percorre ou encerra a recuperação
- **THEN** entre os dados pessoais e credenciais, somente o e-mail durante o fluxo e o reset token após a verificação podem permanecer no estado Reflex
- **AND** e-mail e token são apagados quando o fluxo termina ou é abandonado
- **AND** código, senha e confirmação são recebidos apenas como dados transitórios do formulário e nunca são persistidos ou registrados

#### Scenario: Acesso direto sem estado prévio
- **WHEN** a pessoa abre `/verificar-email` sem e-mail no estado ou `/nova-senha` sem reset token válido no estado Reflex
- **THEN** a aplicação redireciona para `/recuperar-senha` sem revelar dados do fluxo

#### Scenario: Estilo responsivo, animação e autofill
- **WHEN** qualquer tela de recuperação é exibida, inclusive em janela estreita ou com preenchimento automático do navegador
- **THEN** a página mantém o padrão visual de cabeçalho, fundo e cartão das telas de autenticação, usa `auth-card-enter` no cartão, respeita `prefers-reduced-motion` e mantém o texto autofill escuro e legível sobre fundo branco
