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
