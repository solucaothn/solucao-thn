## MODIFIED Requirements

### Requirement: Envio de código por e-mail
O sistema SHALL enviar o código por uma função interna usando o SendGrid, sem link de recuperação no conteúdo.

#### Scenario: Mensagem de recuperação
- **WHEN** uma solicitação elegível gera um código
- **THEN** o destinatário é o e-mail da conta solicitante
- **AND** o assunto MUST ser “Redefinir sua senha no DoaFácil”, fixo e em português
- **AND** a mensagem MUST ir em duas versões, texto simples (`text/plain`) e HTML (`text/html`), com os mesmos textos e sem links
- **AND** os textos MUST ser, nesta ordem: o título “Redefinir sua senha”; “Recebemos um pedido para redefinir a senha da sua conta. Use o código abaixo para continuar.”; “Seu código” com o código; “O código expira em 10 minutos.”; “Se você não pediu para redefinir sua senha, pode ignorar este e-mail. Sua senha atual continua valendo.”; e o rodapé “Você recebeu este e-mail porque alguém usou este endereço no DoaFácil.” e “Projeto acadêmico DoaFácil”
- **AND** a validade escrita no e-mail MUST ser a mesma usada para expirar o código

#### Scenario: Aparência do e-mail de recuperação
- **WHEN** a versão HTML é aberta no Gmail, no Outlook ou no celular
- **THEN** ela MUST mostrar, sobre fundo creme e com no máximo 600 px de largura, o logotipo do DoaFácil (160 px de largura, texto alternativo “DoaFácil”, por URL absoluta, sem anexo), o título em verde-escuro e o código num cartão cinza-claro com borda, em verde, grande e separado em 3 + 3 dígitos
- **AND** a mensagem MUST NOT levar anexos
- **AND** o HTML MUST ter no máximo 20 KB, para não ser cortado pelo Gmail
- **AND** copiar o código da versão HTML MUST resultar nos seis dígitos, sem espaço no meio
- **AND** a versão em texto simples MUST mostrar o código com os seis dígitos juntos
