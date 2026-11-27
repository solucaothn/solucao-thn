# Tarefas

Os comandos `git` e `xano` e as ações no painel do Xano são feitos pelo Higor. O agente só edita arquivos e revisa as saídas. Esta change não faz push ao Xano (decisão 2).

## 1. Script, teste e documentação

- [x] 1.1 Escrever `scripts/teste_endpoints_publicos_real.py` com os cenários EP1 a EP7 e o modo `--antes` (decisão 4): sem login, só entradas que falham nos dois momentos, e impressão só de cenário, status HTTP e OK/FALHOU. Verificação: `py_compile`, o `--help` e uma leitura conferindo que nenhum pedido envia e-mail, cria dados ou leva credenciais.
- [x] 1.2 Criar `tests/test_endpoints_publicos.py`, que confere que nenhum módulo de `doafacil/` cita as quatro rotas nem a `generate_magic_link`. Verificação: o teste passa.
- [x] 1.3 Atualizar o `docs/guia-do-colaborador.md`:
  - na linha dos pontos em aberto, tirar o destino dos 3 endpoints antigos e registrar que esta change os remove;
  - na seção 10.1, tirar `send_welcome_email_POST.xs`, `magic_link_login_POST.xs` e `update_password_POST.xs` da lista e corrigir a contagem;
  - documentar como rodar o `teste_endpoints_publicos_real.py`.

  Verificação: o texto bate com as specs delta e o design.
- [x] 1.4 Rodar `python -m unittest discover -s tests` e `openspec validate endpoints-publicos --strict`. Verificação: tudo passa, e os resultados ficam anotados aqui.
  - Resultados: 529 testes OK e `openspec validate --strict` OK.

## 2. Estado antes e remoção no painel

- [x] 2.1 (manual, Higor) Rodar `python scripts/teste_endpoints_publicos_real.py --antes`. Verificação: EP1 a EP7 OK (as quatro rotas ainda existem), anotados aqui.
  - Rodado pelo Higor. Foi o script que revelou o incidente abaixo: o EP6c (`reset/confirm_password`) deu 404.
- [x] 2.2 (manual, Higor) No painel do Xano, apagar os cinco objetos da tabela da decisão 2, com o `request-reset-link` antes da `generate_magic_link`. Verificação: o Higor confirma aqui que apagou os cinco.
  - **Confirmado pelo Higor:** os quatro endpoints e a `generate_magic_link` foram apagados no painel.
  - **Incidente: `POST /reset/confirm_password` apagado por engano no painel.**
    - **Como apareceu:** o EP6c do script deu 404, e a recuperação de senha ficou quebrada no último passo, a troca da senha.
    - **Dependências conferidas antes de restaurar:** só as tabelas `password_reset_code` e `user` e a função `Quick Start/log_event`, que não foram apagadas. Nada da `generate_magic_link` nem de `user.password_reset`.
    - **Restauração** pelo CLI, com o arquivo local do pull do mesmo dia (anterior à exclusão), enviando só esse arquivo. O push parcial com `-i` deixou de fora os quatro endpoints e a função, que ainda estavam no `xano/`:
      - dry-run: `xano workspace push -d ./xano -i "**/confirm_password_POST.xs" --dry-run`, que mostrou só um item, `CREATE reset/confirm_password POST`;
      - push real: o mesmo comando sem `--dry-run` e sem `--force`.
    - **Depois:** o script sem `--antes` deu 9/9 OK, e a recuperação de senha testada no site funcionou.
    - **GUID:** o arquivo continua com `guid = "e49ij53KjX2bw1Lap6uubkFGfYM"`, o mesmo de antes do push, então o CLI não gravou um GUID novo.

## 3. Arquivos locais e conferência

- [x] 3.1 Depois da confirmação da 2.2, apagar **só** os cinco arquivos, sem restore, stash nem checkout:
  - `xano/api/authentication/message/send_welcome_email_POST.xs`;
  - `xano/api/authentication/reset/request_reset_link_GET.xs`;
  - `xano/api/authentication/reset/magic_link_login_POST.xs`;
  - `xano/api/authentication/reset/update_password_POST.xs`;
  - `xano/function/quick_start/generate_magic_link.xs`.

  Acrescentar ao `tests/test_endpoints_publicos.py` a conferência de que os cinco arquivos não existem. Verificação: o teste passa, e uma busca em `xano/` não encontra `send_welcome_email`, `request-reset-link`, `magic-link-login`, `reset/update_password` nem `generate_magic_link`.
  - Feito: os cinco arquivos foram apagados (só eles), e a pasta `message/` ficou vazia.
  - O teste ganhou a conferência dos arquivos e a busca nos `.xs` do `xano/`.
  - Resultados: 531 testes OK e `openspec validate --strict` OK.
- [x] 3.2 (manual, Higor) Rodar `xano workspace pull -d ./xano` e o `git status`. Verificação: nenhum dos cinco arquivos voltou, e o `xano/` mostra só as cinco remoções e as pendências conhecidas. O resultado fica anotado aqui.
  - **Resultado (Higor):** o pull trouxe 53 documentos, 5 a menos que os 58 do pull anterior.
  - O `git status` mostra só as cinco remoções (`D`), além dos `M` de formatação já conhecidos. Nenhum dos cinco voltou.
- [x] 3.3 (manual, Higor) Rodar `python scripts/teste_endpoints_publicos_real.py`. Verificação: EP1 a EP4 com 404 e EP5 a EP7 OK, anotados aqui.
  - **Resultado (Higor), depois do pull:** 9/9 OK. EP1 a EP4 deram 404, e EP5, EP6a a EP6c e EP7 continuam existindo.

## 4. Verificação final

- [x] 4.1 Rodar de novo a suíte e o `openspec validate endpoints-publicos --strict`, e montar a lista de caminhos para o commit (decisão 3); o Higor roda o `git diff --stat` e confere. Verificação: entram só os cinco arquivos removidos, `openspec/changes/endpoints-publicos/`, o teste, o script e o guia. Não entram `user.xs`, `signup_pending.xs`, `donation_photo.xs` nem os outros arquivos que o pull marca como modificados. Verificado em 27/11/2026: chegou à `main` pelo PR #95 (merge 90ee3cd). O `git show --stat` mostra só os cinco `.xs` removidos, a change arquivada, `tests/test_endpoints_publicos.py`, `scripts/teste_endpoints_publicos_real.py` e o guia; os únicos extras são as specs principais em `openspec/specs/`, atualizadas pelo arquivamento. Não entram `user.xs`, `signup_pending.xs` nem `donation_photo.xs`. Além disso, a suíte (825 testes) e o `openspec validate --specs --strict` (18 specs) passam hoje; a validação da change na época não tem registro.
  - Resultados: 531 testes OK e `openspec validate endpoints-publicos --strict` OK.
  - Caminhos para o commit, adicionados um por um:
    - remoções: `xano/api/authentication/message/send_welcome_email_POST.xs`, `xano/api/authentication/reset/request_reset_link_GET.xs`, `xano/api/authentication/reset/magic_link_login_POST.xs`, `xano/api/authentication/reset/update_password_POST.xs` e `xano/function/quick_start/generate_magic_link.xs`;
    - novos: `openspec/changes/endpoints-publicos/`, `tests/test_endpoints_publicos.py` e `scripts/teste_endpoints_publicos_real.py`;
    - alterado: `docs/guia-do-colaborador.md`.
  - Falta a conferência do `git diff --stat` pelo Higor.
