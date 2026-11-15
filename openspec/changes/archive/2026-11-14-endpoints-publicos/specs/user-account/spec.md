## ADDED Requirements

### Requirement: Nenhum envio de e-mail para conta escolhida pelo cliente
O backend MUST NOT expor endpoint público que envie e-mail, grave evento ou revele a existência de uma conta a partir de um identificador de conta informado pelo cliente. Mensagens de conta saem somente dos fluxos de cadastro e recuperação, para o e-mail da própria conta.

#### Scenario: Pedido de e-mail de boas-vindas
- **WHEN** qualquer cliente chama `POST message/send_welcome_email`, com ou sem `user_id`, com ou sem sessão
- **THEN** o backend responde “não encontrado”
- **AND** não envia e-mail e não grava evento para nenhuma conta
- **AND** a resposta é a mesma para um id existente ou inexistente

#### Scenario: Login, sessão e cadastro preservados
- **WHEN** uma pessoa entra pelo login, consulta a sessão ou conclui o cadastro com código
- **THEN** esses fluxos funcionam como antes, com as mesmas respostas e regras
