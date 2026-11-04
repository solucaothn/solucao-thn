## MODIFIED Requirements

### Requirement: Verificar o código na interface
A aplicação SHALL permitir verificar o código de seis dígitos sem revelar a existência da conta.

#### Scenario: Exibir a tela de verificação
- **WHEN** a pessoa chega à rota `/verificar-email`
- **THEN** no fluxo de recuperação, a aplicação apresenta cartão com `auth-card-enter`, título “Verifique seu e-mail”, e-mail mascarado mostrando a primeira letra, `***` e domínio, campo Código, a dica “Pode demorar um minutinho. Olha também no spam.”, botão “Continuar” e link “← Voltar” para `/recuperar-senha`
- **AND** no fluxo de recuperação, exibe a mensagem neutra “Se existir uma conta com esse e-mail, enviamos um código de 6 dígitos para <e-mail mascarado>.”
- **AND** no fluxo de cadastro, os textos e o link “← Voltar” para `/cadastro` são definidos em `user-account`
- **AND** o valor do código não é mantido no estado Reflex nem registrado em logs

#### Scenario: Reenvio após a contagem regressiva
- **WHEN** a tela de verificação é exibida após uma solicitação
- **THEN** a aplicação apresenta “Reenviar código em 0:30” e atualiza a contagem regressiva até zero
- **AND** ao zerar, apresenta o link “Reenviar código”, que chama `reset/request_code` novamente no fluxo de recuperação
- **AND** ao zerar, apresenta o link “Reenviar código”, que chama `auth/signup_resend` no fluxo de cadastro
- **AND** a proteção contra reenvios continua sendo imposta pelo Xano

#### Scenario: Usar outro e-mail
- **WHEN** a pessoa aciona “Usar outro e-mail”
- **THEN** no fluxo de recuperação, a aplicação apaga o e-mail do estado e retorna para `/recuperar-senha`
- **AND** no fluxo de cadastro, a aplicação apaga o e-mail e a senha do estado e retorna para `/cadastro`

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
