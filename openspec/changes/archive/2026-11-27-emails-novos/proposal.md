# Proposta

## Por quê

Os e-mails de código (confirmação de cadastro e redefinição de senha) saem hoje só em texto simples, com uma frase solta: “Seu código de … é 482913. Ele é válido por 10 minutos.”. Não têm a marca do DoaFácil, não explicam por que a pessoa recebeu a mensagem e deixam o código perdido no meio da frase. O grupo aprovou um modelo visual para os dois e-mails, com logotipo, título, cartão destacado para o código e um rodapé explicativo.

## O que muda

- **Conteúdo dos dois e-mails**, em `xano/function/signup/send_confirmation_code.xs` e `xano/function/password_recovery/send_recovery_code.xs`:
  - novo assunto: “Confirme seu e-mail no DoaFácil” (cadastro) e “Redefinir sua senha no DoaFácil” (recuperação);
  - nova versão HTML, igual ao modelo aprovado: fundo creme, logotipo, título verde-escuro, texto de apresentação, cartão cinza-claro com borda e o código grande, verde e espaçado em 3 + 3 dígitos, aviso de validade, linha divisória, aviso para quem não pediu e rodapé;
  - nova versão em texto simples, com os mesmos textos;
  - o e-mail passa a ir com as duas versões (`text/plain` e `text/html`), para que cada leitor mostre a que suportar.
- **HTML próprio para e-mail**: layout em tabelas, CSS inline, no máximo 600 px de largura, fontes Helvetica/Arial e logotipo por URL absoluta (`assets/email/logo-email.png` na `main` do GitHub), sem anexos, para funcionar no Gmail, no Outlook e no celular. O HTML fica com cerca de 3,5 KB, longe do limite em que o Gmail corta a mensagem.
- **Validade**: o texto “O código expira em 10 minutos.” bate com o que os endpoints usam hoje (`code_expires_at` = agora + 600 s, no cadastro, no reenvio e na recuperação).
- **Prévias locais** em `docs/emails/`, uma por e-mail, com um código de exemplo, para abrir no navegador.

## Fora do escopo

- A lógica das funções e dos endpoints: geração do código, validade, limites de envio, tentativas, respostas neutras e tratamento de falha continuam iguais.
- A chamada ao SendGrid (URL, método, cabeçalhos, tempo limite e conferência do status). A chave continua só na variável de ambiente `SENDGRID_API_KEY` do workspace, e o remetente em `SENDGRID_FROM_EMAIL`.
- Links no e-mail: continua sem nenhum link (nem para o site nem para redefinir a senha).
- Publicar o logotipo: a URL aponta para a `main` no GitHub, então a versão nova de `assets/email/logo-email.png` (320 × 116) precisa estar lá. O envio para o Git e para o Xano é feito pelo Higor.

## Capacidades

### Novas capacidades

Nenhuma.

### Capacidades modificadas

- `user-account`: o requisito “Envio neutro do código de cadastro” passa a descrever o assunto, as versões HTML e texto simples e os textos do e-mail de confirmação.
- `password-recovery`: o requisito “Envio de código por e-mail” passa a descrever o assunto, as versões HTML e texto simples e os textos do e-mail de redefinição; deixa de dizer que a mensagem informa “somente o código e sua validade”.

## Impacto

- Código: as duas funções do Xano listadas acima (só o conteúdo do e-mail).
- Novos arquivos: `docs/emails/confirmacao-cadastro.html`, `docs/emails/redefinicao-senha.html`, o script `scripts/gerar_previas_emails.py`, que gera as prévias a partir dos `.xs`, e `tests/test_emails_codigo.py`.
- Nenhum endpoint, tabela, variável de ambiente ou dependência nova.
