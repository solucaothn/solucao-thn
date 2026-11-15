# Proposal

## Why

O `xano/` da `main` e o workspace do Xano divergem em três tabelas: no Xano, `donation_photo.photo` aceita nulo, e `signup_pending.attempts`, `signup_pending.code_used` e `user.email_verified` não têm valor padrão. A `main` tem a versão pretendida pelas changes anteriores. Enquanto isso não se resolve, cada pull marca essas tabelas como alteradas, e um push descuidado pode apagar uma regra ou outra sem querer. Além disso, o `xano/` tem dois arquivos para a mesma rota `catalog/donations/contact-email`, o que confunde a revisão e pode gerar conflito num push.

**Atualização (2026-11-14):** o painel mostrou que o Xano já tem o esquema da `main`. Os três campos já estão como pretendido, e a diferença é só do jeito que o CLI exporta (decisão 1 do `design.md`). Os pushes foram cancelados, e a change ficou com a sobra do `contact-email`, o teste, o script e a documentação. Os itens abaixo são o plano original; os dois primeiros não exigiram mudança.

## What Changes

- **`donation_photo.photo` obrigatório:** `image? photo` volta a ser `image photo`, como na `main`. Só vai ao Xano depois de conferir no painel que não há linha com a foto vazia.
- **Valores padrão:** `signup_pending.attempts?=0`, `signup_pending.code_used?=false` e `user.email_verified?=false`, como na `main`. Nenhum endpoint depende deles: o cadastro, o reenvio e a verificação gravam `attempts` e `code_used` sempre, a verificação grava `email_verified: true`, e as leituras usam `== true`. O padrão vale para linhas novas criadas sem o campo, e as existentes não mudam.
- **`contact-email` duplicado:** os dois arquivos têm o mesmo GUID, ou seja, são **o mesmo objeto** no Xano. O pull de hoje gravou só o `contact_email_GET.xs`, o nome que o CLI usa. O `contact-email_GET.xs` é uma sobra local, que o pull não reescreve. A change apaga só esse arquivo do `xano/`. **Nada é apagado no painel:** apagar ali removeria o endpoint que o site usa no “Ver e-mail” do detalhe.
- **Push só dos arquivos da change**, com `-i` e dry-run antes. Nunca `--sync` nem `--delete`.
- Teste local do esquema e um script real curto de regressão.

## Capabilities

### New Capabilities

Nenhuma.

### Modified Capabilities

Nenhuma. As specs já descrevem esse comportamento (foto obrigatória na publicação e e-mail não verificado por padrão), e esta change só alinha o esquema do Xano a elas. Por isso a change usa `skip_specs: true`.

## Impact

- **Xano:** as tabelas `donation_photo`, `signup_pending` e `user`, com um campo cada (`user` e `signup_pending` só o padrão). Nenhum endpoint muda.
- **`xano/` local:** os três arquivos de tabela e a remoção do `contact-email_GET.xs`.
- **Frontend:** nenhuma mudança.
- **Fora do escopo:**
  - preencher com `false` o `email_verified` das contas antigas que estão nulas;
  - o `password_reset_code`, que tem o mesmo padrão de `attempts?` e `code_used?` sem valor padrão, igual na `main` e no Xano;
  - os arquivos que só mudam por LF/CRLF.
