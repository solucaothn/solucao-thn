## MODIFIED Requirements

### Requirement: Envio neutro do código de cadastro
O sistema SHALL enviar o código de confirmação por uma função própria via SendGrid e SHALL manter respostas neutras para solicitações elegíveis e não elegíveis.

#### Scenario: Solicitação elegível
- **WHEN** uma solicitação pode criar ou atualizar uma pendência e enviar o código
- **THEN** o destinatário recebe uma mensagem própria de confirmação de cadastro que informa o código de seis dígitos e sua validade de 10 minutos

#### Scenario: Conteúdo do e-mail de confirmação
- **WHEN** o sistema envia o código de confirmação de cadastro
- **THEN** o assunto MUST ser “Confirme seu e-mail no DoaFácil”
- **AND** a mensagem MUST ir em duas versões, texto simples (`text/plain`) e HTML (`text/html`), com os mesmos textos
- **AND** os textos MUST ser, nesta ordem: o título “Confirme seu e-mail”; “Use o código abaixo para confirmar seu endereço e ativar sua conta no DoaFácil.”; “Seu código” com o código; “O código expira em 10 minutos.”; “Se você não criou uma conta no DoaFácil, pode ignorar este e-mail. Nada será feito com o seu endereço.”; e o rodapé “Você recebeu este e-mail porque alguém usou este endereço no DoaFácil.” e “Projeto acadêmico DoaFácil”
- **AND** a validade escrita no e-mail MUST ser a mesma usada para expirar o código
- **AND** a mensagem MUST NOT ter links

#### Scenario: Aparência do e-mail de confirmação
- **WHEN** a versão HTML é aberta no Gmail, no Outlook ou no celular
- **THEN** ela MUST mostrar, sobre fundo creme e com no máximo 600 px de largura, o logotipo do DoaFácil (160 px de largura, texto alternativo “DoaFácil”, por URL absoluta), o título em verde-escuro e o código num cartão cinza-claro com borda, em verde, grande e separado em 3 + 3 dígitos
- **AND** copiar o código da versão HTML MUST resultar nos seis dígitos, sem espaço no meio
- **AND** a versão em texto simples MUST mostrar o código com os seis dígitos juntos

#### Scenario: E-mail já cadastrado, envio limitado ou falha do provedor
- **WHEN** o e-mail já pertence a uma conta, o limite impede o envio ou o provedor falha
- **THEN** o endpoint retorna o mesmo status e corpo neutros da solicitação aceita
- **AND** o endpoint não cria pendência para uma conta existente nem envia código para ela
- **AND** a resposta não revela a causa nem contém e-mail, código, senha ou token

#### Scenario: Reenvio neutro
- **WHEN** uma pessoa solicita reenvio, inclusive para uma pendência inexistente, expirada ou limitada
- **THEN** o endpoint não revela qual dessas condições se aplica
