## ADDED Requirements

### Requirement: Recuperação de senha somente pelo código
O sistema SHALL oferecer a recuperação de senha somente pelo fluxo de código temporário. O backend MUST NOT expor endpoint que gere link mágico, que troque um link ou token de recuperação por sessão, ou que troque a senha fora da confirmação com token de redefinição.

#### Scenario: Pedido de link mágico
- **WHEN** qualquer cliente chama `GET reset/request-reset-link`, com ou sem e-mail
- **THEN** o backend responde “não encontrado”, sem gerar token, sem alterar dados da conta e sem enviar e-mail
- **AND** a resposta é a mesma para e-mail cadastrado, inexistente ou ausente

#### Scenario: Login por link mágico
- **WHEN** qualquer cliente chama `POST reset/magic-link-login`, com qualquer token e e-mail
- **THEN** o backend responde “não encontrado” e não emite sessão

#### Scenario: Troca de senha com sessão
- **WHEN** uma pessoa com sessão válida chama `POST reset/update_password` com uma senha nova
- **THEN** o backend responde “não encontrado” e não altera a senha
- **AND** a senha só pode ser trocada pela confirmação com token de redefinição válido

#### Scenario: Fluxo por código preservado
- **WHEN** uma pessoa solicita, verifica e confirma a recuperação pelo código
- **THEN** o fluxo funciona como antes, com as mesmas respostas e regras
