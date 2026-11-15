# Design

## Context

O motivo está no `proposal.md` (Why). O `git diff` contra a `main` mostrava três tabelas diferentes:

| Arquivo | Na `main` | Exportado pelo pull |
|---|---|---|
| `table/donation_photo.xs` | `image photo` | `image? photo` |
| `table/signup_pending.xs` | `int attempts?=0` e `bool code_used?=false` | `int attempts?` e `bool code_used?` |
| `table/user.xs` | `bool email_verified?=false` | `bool email_verified?` |

Na sintaxe do XanoScript (Xano Developer MCP, tópico `types`), a versão exportada leria como “a foto aceita nulo” e “os campos não têm padrão”. A primeira versão desta change partiu daí para planejar dois pushes.

### Descoberta: o Xano já estava certo (2026-11-14)

O Higor conferiu cada campo no painel do Xano:

| Campo | No painel |
|---|---|
| `donation_photo.photo` | **Required** marcado, e 0 linhas com a foto vazia |
| `signup_pending.attempts` | padrão `0`, não nulável |
| `signup_pending.code_used` | padrão `false`, não nulável |
| `user.email_verified` | padrão `false`, não nulável |

- Com as três linhas editadas para a versão da `main`, o dry-run do push A respondeu **“No changes to push”**.
- O pull seguinte voltou a exportar `image?` e os campos sem `=0`/`=false`.

**Conclusão:** a diferença é só do jeito que o CLI exporta. Ele omite o `=valor` do padrão e mostra `?` mesmo em campo com Required. Não falta nada no Xano.

**Quem depende dos padrões:** de qualquer forma, ninguém. Todo `db.add` e toda reinicialização gravam os campos explicitamente:

| Campo | Onde é gravado | Onde é lido |
|---|---|---|
| `signup_pending.attempts` e `code_used` | `auth/signup` e `auth/signup_resend` (`attempts: 0` e `code_used: false`) e `auth/signup_verify` (o incremento e o bloqueio) | `auth/signup_verify`: `code_used == false && attempts < 5` |
| `user.email_verified` | `auth/signup_verify`, com `email_verified: true` | `profile`, `mine`, `detail` e `donor`, sempre com `== true` |
| `donation_photo.photo` | só o `catalog/donations/publish`, que recusa publicação sem fotos | `detail` e os cartões |

### Os dois arquivos do `contact-email`

| Arquivo | GUID | Pull de 2026-11-14 | Situação |
|---|---|---|---|
| `contact_email_GET.xs` | `Pafl9c535tv4_-PvNUsoZLyF33g` | reescrito | nome que o CLI gera para a rota |
| `contact-email_GET.xs` | `Pafl9c535tv4_-PvNUsoZLyF33g` | não tocado (01/11) | sobra local de um nome antigo |

- A pasta tinha 54 `.xs` para os 53 documentos do pull: o arquivo a mais era esse.
- O frontend chama a rota `/catalog/donations/contact-email` (`DONOR_CONTACT_EMAIL_PATH` em `doafacil/detalhe_doacao.py`), servida por esse único objeto.

## Goals / Non-Goals

**Goals:**
- O `xano/` tem um único arquivo para a rota `contact-email`.
- O guia registra que o painel é a fonte da verdade para padrões e obrigatoriedade, e que as três tabelas são uma divergência de exportação conhecida.
- Nada muda no Xano.

**Non-Goals:**
- Fazer qualquer push. Os pushes A e B foram cancelados.
- Commitar os três `.xs` de tabela, que continuam como o pull exporta.
- Preencher `email_verified` nulos de contas antigas, se existirem: o padrão do painel e as leituras com `== true` já tratam o caso.
- Mudar o `password_reset_code`.

## Decisions

### 1. Sem push: o esquema do Xano já é o pretendido

- **Cancelados:** o push A (padrões) e o push B (foto obrigatória). O painel mostra o esquema pretendido, e o dry-run não encontra diferença.
- **As edições das três linhas** feitas na primeira rodada da implementação foram desfeitas pelo pull seguinte. Os arquivos ficam como o CLI exporta e **não entram em commit**. O guia passa a listá-los na seção 10.1, ao lado dos arquivos que só mudam por LF/CRLF.
- **Alternativa descartada:** commitar a versão exportada, com `image?` e sem padrão, para a `main` bater com o pull. A `main` passaria a dizer algo diferente do painel para quem lê o `.xs`. O grupo preferiu manter a versão escrita à mão e registrar a divergência.

### 2. O painel é a fonte da verdade para padrão, obrigatoriedade e nulo

- Antes de concluir que falta algo no Xano, confira o campo no painel e rode um dry-run com `-i` só do arquivo. “No changes to push” quer dizer que não falta nada.
- O guia (seção 11) registra essa regra.

### 3. `contact-email`: apagar só o arquivo local antigo

- O agente apagou o `xano/api/catalog/catalog/donations/contact-email_GET.xs` e manteve o `contact_email_GET.xs`.
- **Nada no painel e nenhum push:** o objeto no Xano é um só, e é o que o site usa.
- **No `git`:** o commit registra a remoção do `contact-email_GET.xs` e, se o `contact_email_GET.xs` ainda não estiver versionado, a inclusão dele. O Higor confere no `git status`.

### 4. Verificação

- **Teste local** `tests/test_esquema_xano.py`: um único arquivo no `xano/` declara a rota `catalog/donations/contact-email`. As linhas de esquema não são conferidas, porque qualquer pull as mudaria.
- **Script real** `scripts/teste_esquema_xano_real.py`, que só lê. Não cria dados, não envia e-mail e não imprime corpos, tokens nem e-mails:

  | Cenário | O que confere |
  |---|---|
  | ES1 | `GET catalog/donations/contact-email` sem token responde 401: a rota existe |
  | ES2 | o detalhe das doações recentes traz as fotos só como URL, nunca nulas |
  | ES3 | com login, `auth/profile` traz `email_verified` como verdadeiro ou falso |

## Risks / Trade-offs

- **[Alguém “corrigir” os três `.xs` e commitar]** → a seção 10.1 do guia lista os três como divergência conhecida, com o que o painel mostra.
- **[Alguém confiar no `.xs` exportado para saber se um campo é obrigatório]** → a seção 11 do guia manda conferir no painel.
- **[Apagar o `contact-email` errado]** → só o arquivo local com o nome antigo foi apagado, e o Xano não foi tocado. O ES1 confirma que a rota continua no ar.

## Migration Plan

1. O agente apaga o `contact-email_GET.xs`, escreve o teste e o script e atualiza o guia.
2. O Higor roda o ES1 a ES3. Resultado: 3/3 OK.
3. O Higor faz o pull de conferência e o `git status`: o `contact-email_GET.xs` não volta, e as três tabelas aparecem só como a divergência conhecida.
4. **Rollback:** restaurar o `contact-email_GET.xs` a partir da `main`. Isso não muda nada no Xano.
