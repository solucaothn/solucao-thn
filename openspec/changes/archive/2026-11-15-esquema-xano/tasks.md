# Tarefas

Os comandos `git` e `xano` e as ações no painel do Xano são feitos pelo Higor. O agente só edita arquivos e revisa as saídas. Esta change não faz push ao Xano (decisão 1).

## 1. Arquivos locais, teste, script e documentação

- [x] 1.1 Conferir o esquema das três tabelas (decisão 1). Verificação: o que o painel mostra, anotado aqui.
  - **Primeira rodada:** o agente editou as três linhas para a versão da `main` (`image photo`, `int attempts?=0`, `bool code_used?=false` e `bool email_verified?=false`), e os três arquivos passaram na validação do Xano Developer MCP.
  - **Descoberta (Higor, painel, 2026-11-14):**
    - `donation_photo.photo` está com **Required** marcado;
    - `signup_pending.attempts` tem padrão `0` e `code_used` tem padrão `false`, os dois não nuláveis;
    - `user.email_verified` tem padrão `false`, não nulável.
  - Com as linhas editadas, o dry-run do push A respondeu **“No changes to push”**.
  - O pull seguinte voltou a exportar `image?` e os campos sem `=0`/`=false`, desfazendo as edições.
  - **Conclusão:** é só o jeito que o CLI exporta. Os três `.xs` ficam como o pull os traz e **não entram em commit**.
- [x] 1.2 Apagar só o `xano/api/catalog/catalog/donations/contact-email_GET.xs` (o de 01/11) e manter o `contact_email_GET.xs` (decisão 3). Verificação: uma busca em `xano/` encontra um único arquivo com `catalog/donations/contact-email`.
  - Depois do pull de conferência, o arquivo antigo continua ausente.
- [x] 1.3 Criar `tests/test_esquema_xano.py`, que confere que um único arquivo declara a rota `contact-email` (decisão 4). Verificação: o teste passa, e falha se o arquivo antigo voltar.
  - As checagens das linhas de esquema da primeira rodada foram retiradas, porque falhariam depois de qualquer pull.
- [x] 1.4 Escrever `scripts/teste_esquema_xano_real.py` com os cenários ES1 a ES3 (decisão 4): login só no ES3, nenhum dado criado, nenhum e-mail enviado, e impressão só de cenário, status e OK/FALHOU. Verificação: `py_compile`, o `--help` e uma leitura conferindo que nenhum pedido cria ou altera dados.
- [x] 1.5 Atualizar o `docs/guia-do-colaborador.md` (decisão 2):
  - na seção 10.1, as três tabelas como divergência de exportação conhecida, com o que o painel mostra, que nunca entram em commit;
  - na seção 11, o painel como fonte da verdade para padrão, obrigatoriedade e nulo (o CLI omite o `=valor` e mostra `?` mesmo com Required), e a regra dos nomes de arquivo: uma sobra local com outro nome se apaga só no `xano/`, nunca no painel;
  - na seção “Fotos obrigatórias”, a conferência no painel desta change;
  - como rodar o `teste_esquema_xano_real.py`.

  Verificação: o texto bate com o design.

## 2. Verificação contra o Xano real

- [x] 2.1 (manual, Higor) Rodar `python scripts/teste_esquema_xano_real.py`. Verificação: ES1 a ES3 OK, anotados aqui.
  - **Resultado (Higor):** 3/3 OK.
- [x] 2.2 (manual, Higor) No painel, conferir a tabela `donation_photo` com o filtro de `photo` vazio. Verificação: 0 registros, anotados aqui.
  - **Resultado (Higor), 2026-11-14:** 0 registros.

### Canceladas (decisão 1)

Estas tarefas da primeira versão foram canceladas porque o Xano já tem o esquema pretendido:

- Push A: `xano workspace push -d ./xano -i "table/signup_pending.xs" -i "table/user.xs"`. O dry-run respondeu “No changes to push”.
- Cadastro manual depois do push A: sem push, nada mudou no cadastro.
- Push B: `xano workspace push -d ./xano -i "table/donation_photo.xs"`. Desnecessário, porque o campo já está com Required.
- `teste_fotos_formulario_real.py` depois do push B: sem push, nada mudou na publicação.

## 3. Conferência final

- [ ] 3.1 (manual, Higor) Rodar o `git status` depois do pull. Verificação: o `contact-email_GET.xs` aparece como removido (ou não aparece, se nunca foi versionado), o `contact_email_GET.xs` está versionado ou aparece como novo, e as três tabelas aparecem só como a divergência conhecida. O resultado fica anotado aqui.
- [ ] 3.2 Rodar `python -m unittest discover -s tests` e `openspec validate esquema-xano --strict`, e montar a lista de caminhos para o commit (decisão 3); o Higor roda o `git diff --stat` e confere. Verificação: entram só a remoção do `contact-email_GET.xs`, o `contact_email_GET.xs` (se ainda não estiver versionado), `openspec/changes/esquema-xano/`, `tests/test_esquema_xano.py`, `scripts/teste_esquema_xano_real.py` e o guia. Não entram os três `.xs` de tabela nem os outros arquivos que o pull marca como modificados.
