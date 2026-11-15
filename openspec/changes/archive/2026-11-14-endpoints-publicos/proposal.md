# Proposal

## Why

O workspace do Xano ainda tem quatro endpoints do modelo “Quick Start”, que o site não usa e que ficaram de fora das changes anteriores. Três são públicos e um aceita qualquer sessão. Juntos, eles contornam regras que o projeto já adotou:

- **`message/send_welcome_email` (POST, público):** recebe qualquer `user_id`, envia um e-mail, grava um evento em nome dessa conta e devolve o resultado do envio. O erro “User not found.” revela quais ids existem.
- **`reset/request-reset-link` (GET, público):** gera um token de link mágico em `user.password_reset` para qualquer e-mail. O erro “No user found for that email.” revela quais e-mails têm conta, o que contradiz a resposta neutra da recuperação por código.
- **`reset/magic-link-login` (POST, público):** troca esse token por uma sessão de 24 horas, fora do login e da recuperação por código.
- **`reset/update_password` (POST, com sessão):** troca a senha com qualquer token de sessão, sem a senha atual e sem a regra de senha da recuperação (letra e dígito), nem a invalidação de códigos.

A change `recuperacao-senha-api` deixou a decisão sobre eles para uma change separada, e o `docs/guia-do-colaborador.md` lista o destino dos três endpoints de link mágico como ponto em aberto. O grupo decidiu removê-los.

## What Changes

- **BREAKING (sem consumidores conhecidos):** remover do Xano os endpoints `POST message/send_welcome_email`, `GET reset/request-reset-link`, `POST reset/magic-link-login` e `POST reset/update_password`. As rotas passam a responder “não encontrado”.
- Remover a função `Quick Start/generate_magic_link`, usada só pelo `request-reset-link`.
- Manter sem mudança:
  - o campo `user.password_reset`, que fica na tabela e sem uso;
  - a função `Quick Start/log_event` e a tabela `event_log`, usadas por outros endpoints;
  - o login, o cadastro com código e a recuperação por código.
- Não enviar ao Xano as três diferenças de esquema já conhecidas (`user.email_verified`, os padrões de `signup_pending` e `donation_photo.photo`): elas ficam fora desta change e de qualquer push dela.
- Atualizar o `docs/guia-do-colaborador.md`: o ponto em aberto resolvido e a lista da seção 10.1 sem os arquivos removidos.
- Script de verificação contra o Xano real, que confere o “não encontrado” das quatro rotas sem enviar e-mail nem criar dados.

## Capabilities

### New Capabilities

Nenhuma.

### Modified Capabilities

- `password-recovery`: requisito novo, a recuperação de senha só pelo código. Não há link mágico, sessão emitida pela recuperação nem troca de senha fora da confirmação com token de redefinição.
- `user-account`: requisito novo, nenhum endpoint público envia e-mail ou grava evento para uma conta escolhida pelo cliente (o fim do `send_welcome_email`).

## Impact

- **Xano:** quatro endpoints e uma função removidos pelo painel, sem push (decisão 2 do `design.md`). Nenhuma tabela muda. O `xano/` local perde os cinco arquivos correspondentes.
- **Frontend (Reflex):** nenhuma mudança. Nenhum módulo de `doafacil/` chama essas rotas.
- **Documentação:** `docs/guia-do-colaborador.md`.
- **Fora do escopo:**
  - remover o campo `user.password_reset`;
  - o endpoint `logs/user/my_events`, também do modelo, mas restrito à própria conta;
  - os dois arquivos do `contact-email` (`contact_email_GET.xs` e `contact-email_GET.xs`) que aparecem no `xano/`;
  - as três diferenças de esquema citadas acima.
