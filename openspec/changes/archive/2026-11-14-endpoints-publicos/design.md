# Design

## Context

O motivo está no `proposal.md` (Why). Estado atual levantado no `xano/`, depois do pull do Higor na branch `fix/endpoints-publicos`:

| Arquivo | Rota | `auth` | O que faz hoje |
|---|---|---|---|
| `api/authentication/message/send_welcome_email_POST.xs` | `POST message/send_welcome_email` | nenhum | busca a conta pelo `user_id`, envia e-mail (`util.send_email`, provedor `xano`) e grava `welcome_email_sent` com o `log_event` |
| `api/authentication/reset/request_reset_link_GET.xs` | `GET reset/request-reset-link` | nenhum | chama `generate_magic_link`, que grava um UUID em `user.password_reset`, e envia e-mail com link para a página de demo do modelo |
| `api/authentication/reset/magic_link_login_POST.xs` | `POST reset/magic-link-login` | nenhum | confere o token em `user.password_reset` e emite `authToken` de 24 h |
| `api/authentication/reset/update_password_POST.xs` | `POST reset/update_password` | `user` | troca a senha da sessão (mínimo de 8, igual à confirmação) |
| `function/quick_start/generate_magic_link.xs` | (função) | — | usada só pelo `request-reset-link` |

- **Quem usa:** nenhum módulo de `doafacil/`, nenhum teste e nenhum script chama essas rotas. Dentro do `xano/`, a única referência à `generate_magic_link` é o `request-reset-link`.
- **O que continua sendo usado:** a `Quick Start/log_event` (login, `me`, cadastro, recuperação e chat) e a tabela `event_log`. Elas ficam.
- **Push do CLI** (Xano Developer MCP, tópico `workspace`):
  - o push padrão é **parcial e aditivo**: envia o que mudou e **não apaga** nada no workspace;
  - apagar objetos remotos pelo CLI exige **`--sync --delete`**, que faz o push completo e apaga **tudo** o que estiver no workspace e não estiver na pasta local.
- **Pendências conhecidas que não entram:** as três diferenças de esquema entre a `main` e o workspace (`user.email_verified?`, os padrões de `signup_pending` e `donation_photo.photo` opcional).

## Goals / Non-Goals

**Goals:**
- As quatro rotas deixam de existir no workspace, e a função sem uso sai junto.
- Nada mais muda no workspace: a change não faz nenhum push.
- O `xano/` local fica igual ao workspace nesses cinco objetos, e o commit leva só a remoção dos cinco arquivos, os artefatos, o teste, o script e a documentação.

**Non-Goals:**
- Desativar os endpoints mantendo os arquivos (alternativa descartada na decisão 1).
- Remover `user.password_reset`, mexer no `logs/user/my_events` ou nos arquivos do `contact-email`.
- Qualquer mudança no frontend.

## Decisions

### 1. Remover os objetos, e não desativar os endpoints

- **Escolha do grupo:** apagar os quatro endpoints e a `generate_magic_link`.
- **Alternativa descartada:** manter os arquivos com o `stack` trocado por uma `precondition` que sempre falha. É reversível, mas deixa no workspace código morto com nomes que parecem válidos, e cada pull continua trazendo esses arquivos.
- **Resposta depois da remoção:** a rota inexistente recebe o “não encontrado” do próprio Xano (HTTP 404), igual para qualquer entrada, o que atende aos cenários das specs. O corpo exato é o padrão da plataforma e não é conferido.

### 2. Apagar pelo painel do Xano, sem push

Decisão do Higor com o Claude. O Higor faz tudo o que envolve o painel e os comandos `git` e `xano`; o agente só edita os arquivos.

| Objeto no painel | Onde fica | Arquivo local |
|---|---|---|
| `POST /message/send_welcome_email` | API Group **Authentication** | `xano/api/authentication/message/send_welcome_email_POST.xs` |
| `GET /reset/request-reset-link` | API Group **Authentication** | `xano/api/authentication/reset/request_reset_link_GET.xs` |
| `POST /reset/magic-link-login` | API Group **Authentication** | `xano/api/authentication/reset/magic_link_login_POST.xs` |
| `POST /reset/update_password` | API Group **Authentication** | `xano/api/authentication/reset/update_password_POST.xs` |
| função `Quick Start/generate_magic_link` | Library → Functions, pasta **Quick Start** | `xano/function/quick_start/generate_magic_link.xs` |

Ordem:

1. **Estado antes:** o Higor roda o script real (decisão 4) e anota o resultado. As quatro rotas devem existir (status diferente de 404).
2. **Painel:** o Higor apaga os cinco objetos, nesta ordem: o `request-reset-link` antes da `generate_magic_link`, porque é ele que chama a função.
3. **Arquivos:** depois que o Higor confirmar, o agente apaga **só** os cinco `.xs` acima. Não usa restore, stash nem checkout.
4. **Pull de conferência:** o Higor roda `xano workspace pull -d ./xano` e o `git status`. Nenhum dos cinco arquivos volta, e o `xano/` mostra só as cinco remoções e as pendências conhecidas.
5. **Estado depois:** o Higor roda o script de novo. As quatro rotas removidas dão 404, e as que ficam continuam existindo.

- **Por que não o `--sync --delete`:** ele apagaria qualquer objeto do workspace que não estivesse na pasta local e reenviaria todos os arquivos, inclusive os das pendências conhecidas. O painel apaga só os cinco objetos escolhidos.
- **Por que não o push parcial:** ele não apaga nada.
- **Por que não o Xano MCP Server:** o `AGENTS.md` não permite alterar o workspace por ele.
- **Por que o pull depois:** confirma pelo próprio CLI que o workspace não tem mais os cinco objetos, e deixa o `xano/` local igual ao workspace.

### 3. Commit só com o que é da change

- Entram: a remoção dos cinco `.xs`, `openspec/changes/endpoints-publicos/`, o teste, o script de verificação e o `docs/guia-do-colaborador.md`.
- Não entram: os outros arquivos do `xano/` que o pull marca como modificados, inclusive `user.xs`, `signup_pending.xs` e `donation_photo.xs`. Cada caminho é adicionado um por um (o guia proíbe `git add .`).

### 4. Verificação contra o Xano real, antes e depois, sem efeito colateral

- **Script** `scripts/teste_endpoints_publicos_real.py`, no padrão dos outros scripts reais. Não pede login, não imprime corpos, tokens nem e-mails, e não cria dados.
- **Dois modos:** `--antes` (as quatro rotas ainda existem) e o padrão, depois da remoção (as quatro dão 404).
- **Removidos (EP1 a EP4):** cada rota recebe uma entrada que falha antes da remoção, para o script ser inofensivo nos dois momentos:

  | Cenário | Pedido | Esperado com `--antes` | Esperado depois |
  |---|---|---|---|
  | EP1 | `POST message/send_welcome_email` sem `user_id` | diferente de 404 (erro de entrada, sem e-mail) | 404 |
  | EP2 | `GET reset/request-reset-link` sem e-mail | diferente de 404 (erro da função, sem token nem e-mail) | 404 |
  | EP3 | `POST reset/magic-link-login` sem token nem e-mail | diferente de 404 (erro de validação, sem sessão) | 404 |
  | EP4 | `POST reset/update_password` sem token, com senhas diferentes | diferente de 404 (401, sem troca) | 404 |

- **Preservados (EP5 a EP7), nos dois modos:** as rotas que ficam respondem com algo **diferente de 404**, com entradas que não enviam e-mail nem criam dados:
  - EP5: `auth/login` com corpo vazio;
  - EP6: `reset/request_code`, `reset/verify_code` e `reset/confirm_password` com corpo vazio (entradas obrigatórias, então erro de entrada);
  - EP7: `auth/signup` com corpo vazio (entradas obrigatórias).
- O roteiro completo do login, do cadastro e da recuperação já foi validado pelas changes anteriores. Aqui a regressão é só “a rota continua existindo”, e a mudança não toca nesses arquivos.

## Risks / Trade-offs

- **[Apagar o objeto errado no painel]** → a tabela da decisão 2 dá o grupo, o método e a rota exatos. O pull de conferência mostra, no `git status`, qualquer outro arquivo removido.
- **[O pull trazer mudanças de outra pessoa]** → o `git status` depois do pull é conferido. Só os cinco arquivos entram no commit (decisão 3).
- **[Um dos cinco voltar no pull]** → indica que o objeto não foi apagado no painel. Repete o passo 2 para ele antes de seguir.
- **[Algum consumidor externo desconhecido]** → nenhum no repositório. Os endpoints eram do modelo e nunca foram documentados para o site; o risco é aceito pelo grupo.
- **[O e-mail do provedor `xano` só chega ao dono do workspace]** → isso reduz o alcance do abuso, mas não resolve a enumeração de contas nem a sessão do `magic-link-login`. Não muda a decisão.

## Migration Plan

1. O agente escreve o script, o teste e a documentação.
2. O Higor roda o script com `--antes`, apaga os cinco objetos no painel e avisa.
3. O agente apaga os cinco `.xs`.
4. O Higor faz o pull de conferência, confere o `git status` e roda o script sem `--antes`.
5. **Rollback:** recriar os objetos no Xano a partir dos arquivos na `main` (eles continuam no histórico do `git`), com um push parcial só deles, revisado no dry-run e aprovado pelo grupo.
