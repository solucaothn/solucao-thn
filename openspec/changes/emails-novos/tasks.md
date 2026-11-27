# Tarefas

Os comandos `git` e `xano` são do Higor. Nada aqui envia ao Xano nem ao SendGrid: a verificação é feita pelo validador do Xano Developer MCP, pelos testes e pelas prévias locais.

## 1. E-mail de confirmação de cadastro

- [x] 1.1 Em `xano/function/signup/send_confirmation_code.xs`, trocar o assunto e o texto simples e acrescentar o HTML (decisões 1 a 6), com `content` em `text/plain` e `text/html`, nessa ordem. O `api.request`, a `precondition` e a resposta não mudam. Verificação: `xano_validate_xanoscript` sem erros.

## 2. E-mail de redefinição de senha

- [x] 2.1 Mesmo trabalho em `xano/function/password_recovery/send_recovery_code.xs`, com os textos da redefinição. Verificação: `xano_validate_xanoscript` sem erros.

## 3. Prévias

- [x] 3.1 Criar `scripts/gerar_previas_emails.py`, que gera `docs/emails/confirmacao-cadastro.html` e `docs/emails/redefinicao-senha.html` a partir dos `.xs`, com o código de exemplo 482913 (decisão 7). Rodar o script. Verificação: os dois arquivos existem e abrem no navegador.

## 4. Testes

- [x] 4.1 Criar `tests/test_emails_codigo.py`. Ele confere, nas duas funções:
  - o assunto, a ordem `text/plain` e `text/html`, e os textos do modelo nas duas versões;
  - o logotipo (URL, 160 px e `alt`), a largura de 600 px, a pilha de fontes, o CSS só inline e a ausência de links;
  - o código copiável sem espaço nas duas versões;
  - os “10 minutos” iguais aos 600 s dos endpoints;
  - a chamada ao SendGrid sem mudança, com a chave só em `$env`;
  - as prévias atualizadas.

  Verificação: a suíte completa passa.

## 5. Conferência

- [x] 5.1 Rodar `openspec validate emails-novos --strict`. Verificação: sem erros.
