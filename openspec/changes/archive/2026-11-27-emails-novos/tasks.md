# Tarefas

Os comandos `git` e `xano` são do Higor. As tarefas 1 a 7 não enviam nada ao Xano nem ao SendGrid: a verificação é feita pelo validador do Xano Developer MCP, pelos testes e pelas prévias locais. O envio ao Xano e o teste real (tarefa 8) foram feitos pelo Higor.

## 1. E-mail de confirmação de cadastro

- [x] 1.1 Em `xano/function/signup/send_confirmation_code.xs`, trocar o assunto e o texto simples e acrescentar o HTML (decisões 1 a 6), com `content` em `text/plain` e `text/html`, nessa ordem. O `api.request`, a `precondition` e a resposta não mudam. Verificação: `xano_validate_xanoscript` sem erros.

## 2. E-mail de redefinição de senha

- [x] 2.1 Mesmo trabalho em `xano/function/password_recovery/send_recovery_code.xs`, com os textos da redefinição. Verificação: `xano_validate_xanoscript` sem erros.

## 3. Prévias

- [x] 3.1 Criar `scripts/gerar_previas_emails.py`, que gera `docs/emails/confirmacao-cadastro.html` e `docs/emails/redefinicao-senha.html` a partir dos `.xs`, com o código de exemplo 482913 (decisão 7). Rodar o script. Verificação: os dois arquivos existem e abrem no navegador.

## 4. Testes

- [x] 4.1 Criar `tests/test_emails_codigo.py`. Ele confere, nas duas funções:
  - o assunto, a ordem `text/plain` e `text/html`, e os textos do modelo nas duas versões;
  - o logotipo por URL absoluta (160 × 58 e `alt`), sem anexos, o HTML abaixo de 20 KB, a largura de 600 px, a pilha de fontes, o CSS só inline e a ausência de links;
  - o código copiável sem espaço nas duas versões;
  - os “10 minutos” iguais aos 600 s dos endpoints;
  - a chamada ao SendGrid sem mudança, com a chave só em `$env`;
  - as prévias atualizadas.

  Verificação: a suíte completa passa.

## 5. Conferência

- [x] 5.1 Rodar `openspec validate emails-novos --strict`. Verificação: sem erros.

## 6. Logotipo embutido (desfeito na tarefa 7.1)

- [x] 6.1 Trocar o logotipo por URL pelo anexo inline do SendGrid (decisão 6) nas duas funções: `attachments` com o base64 de `assets/email/logo-email.png`, `disposition: "inline"` e `content_id: "logo-doafacil"`, e `src="cid:logo-doafacil"` no `<img>`. As prévias passam a usar o arquivo local. Verificação: `xano_validate_xanoscript` sem erros, testes de `tests/test_emails_codigo.py` e as prévias com o logotipo no navegador.

## 7. Volta ao logotipo por URL

- [x] 7.1 Nas duas funções, tirar `attachments` do payload e voltar o `src` do `<img>` para a URL absoluta do GitHub, mantendo `width="160"`, `height="58"` e `alt="DoaFácil"` (decisão 6). As prévias trocam a URL pelo arquivo local. Verificação: `xano_validate_xanoscript` sem erros, testes de `tests/test_emails_codigo.py` (sem anexos, HTML abaixo de 20 KB e logotipo de 320 × 116) e `openspec validate emails-novos --strict`.

## 8. Teste real

- [x] 8.1 Levar o logotipo novo (`assets/email/logo-email.png`, 320 × 116) para a `main` e enviar as duas funções ao Xano. Feito pelo Higor. Evidência: os e-mails reais de 27/11/2026 (tarefa 8.2) chegaram com o logotipo.
- [x] 8.2 Pedir um código de cadastro e um de redefinição de senha e conferir os e-mails no Gmail. Evidência (27/11/2026, Higor): os dois e-mails chegaram com o logotipo, o layout e o código corretos, sem anexo. O primeiro caiu no Spam, porque o remetente é um endereço @gmail.com enviado pelo SendGrid. Trocar o remetente é assunto à parte, fora desta change.
- [ ] 8.3 Conferir os dois e-mails no Outlook e no app de e-mail do celular. Ainda não feito: o teste real foi só no Gmail.
