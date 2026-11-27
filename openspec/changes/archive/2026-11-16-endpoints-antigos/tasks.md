# Tarefas

Os comandos `git` e `xano` e as ações no painel do Xano são feitos pelo Higor. O agente só edita arquivos e revisa as saídas. Esta change não faz push ao Xano (decisão 1).

## 1. Script, testes, contato e documentação

- [x] 1.1 Escrever `scripts/teste_endpoints_antigos_real.py` com os cenários EA1 a EA6 e o modo `--antes` (decisão 2): sem login e sem token, só entradas que não devolvem doações nem criam dados, e impressão só de cenário, status HTTP e OK/FALHOU. Verificação: `py_compile`, o `--help` e uma leitura conferindo que nenhum pedido leva credenciais, cria dados ou imprime corpos.
- [x] 1.2 Criar `tests/test_endpoints_antigos.py`, que confere que em `doafacil/` o caminho `/catalog/donations` sem sufixo só é usado por `client.patch` e `client.delete` (decisão 4). Verificação: o teste passa.
- [x] 1.3 Contato (decisão 3):
  - `CONTACT_EMAIL = "solucaothn@gmail.com"` em `doafacil/rodape.py`;
  - `contact_href()` sempre `/contato`;
  - em `doafacil/institucional.py`: a `/contato`, a caixa da Central de ajuda e as seções 7 dos Termos e da Privacidade com os textos da decisão 3, o e-mail como link `mailto:`; o ramo “sem e-mail” fica como reserva, com o `CONTACT_PENDING_TEXT`.

  Verificação: os testes da tarefa 1.4.
- [x] 1.4 Atualizar `tests/test_institucional.py`:
  - o teste de e-mail inventado aceita só `solucaothn@gmail.com`;
  - os convites levam a `/contato`;
  - a `/contato`, a caixa, os Termos e a Privacidade mostram o e-mail com `mailto:`;
  - com o e-mail definido, nenhum texto diz “ainda vai ser publicado”;
  - com o `CONTACT_EMAIL` vazio (por `patch`), os quatro lugares voltam ao texto pendente.

  Verificação: os testes passam.
- [x] 1.5 Atualizar a documentação:
  - no `docs/guia-do-colaborador.md`:
    - a pendência do e-mail de contato fica resolvida (seções 7 e 8 e a tabela dos links da home);
    - a nota do “`GET /catalog/donations` antigo” sai;
    - registrar que os pedidos sobre dados chegam pelo e-mail e são atendidos pelo grupo à mão;
    - documentar como rodar o script novo;
  - no `docs/design/README.md`, a linha do contato na tabela de diferenças do Figma.

  Verificação: o texto bate com as specs delta e o design.
- [x] 1.6 Rodar `python -m unittest discover -s tests`, `reflex compile` e `openspec validate endpoints-antigos --strict`. Verificação: tudo passa, e os resultados ficam anotados aqui.
  - Resultados: 628 testes OK, `reflex compile` OK e `openspec validate --strict` OK.

## 2. Estado antes e remoção no painel

- [x] 2.1 (manual, Higor) Rodar `python scripts/teste_endpoints_antigos_real.py --antes`. Verificação: EA1 a EA6 OK (o GET e o POST ainda existem), anotados aqui.
  - Resultado: 6/6 OK.
- [x] 2.2 (manual, Higor) No painel do Xano, grupo **Catalog**, apagar **só** o `GET /catalog/donations` e o `POST /catalog/donations`, deixando o PATCH e o DELETE do mesmo caminho (decisão 1). Verificação: o Higor confirma aqui que apagou os dois.
  - Resultado: o Higor apagou só o GET e o POST; conferiu por print que o PATCH e o DELETE continuam.

## 3. Arquivos locais e conferência

- [x] 3.1 Depois da confirmação da 2.2, apagar **só** `xano/api/catalog/catalog/donations_GET.xs` e `xano/api/catalog/catalog/donations_POST.xs`, sem restore, stash nem checkout. Acrescentar ao `tests/test_endpoints_antigos.py` a conferência de que os dois não existem e de que o `donations_PATCH.xs` e o `donations_DELETE.xs` continuam. Verificação: o teste passa.
  - Resultado: os dois arquivos foram apagados; o teste passa (4 testes) e a suíte também (630 testes OK).
- [x] 3.2 (manual, Higor) Rodar `xano workspace pull -d ./xano` e o `git status`. Verificação: os dois arquivos não voltam, o PATCH e o DELETE continuam, e o `xano/` mostra só as duas remoções e as pendências conhecidas. O resultado fica anotado aqui.
  - Resultado: o pull trouxe 52 documentos; os dois `.xs` aparecem como `D` e não voltaram.
- [x] 3.3 (manual, Higor) Rodar `python scripts/teste_endpoints_antigos_real.py`. Verificação: EA1 e EA2 com 404 (ou 405), e EA3 a EA6 diferentes de 404, anotados aqui.
  - Resultado: 6/6 OK, com EA1 e EA2 em 404 (rodado logo depois da 2.2, antes da 3.1 e da 3.2).

## 4. Verificação final

- [x] 4.1 (manual) No navegador: o rodapé e o “Fale com a gente” levam a `/contato`, a `/contato` mostra o e-mail e o `mailto:` abre o programa de e-mail, e os Termos e a Privacidade mostram o e-mail na seção 7. Verificação: os itens anotados aqui.
  - Resultado (Higor): a `/contato` mostra `solucaothn@gmail.com`, os convites levam a `/contato`, os Termos e a Privacidade mostram o e-mail, e editar e apagar doação em Minhas doações continuam funcionando.
- [x] 4.2 Rodar de novo a suíte e o `openspec validate endpoints-antigos --strict`, e montar a lista de caminhos para o commit (decisão 5); o Higor roda o `git diff --stat` e confere. Verificação: entram só os caminhos da decisão 5. Verificado em 27/11/2026: chegou à `main` pelo PR #102 (merge eeeaa72). O `git show --name-status` mostra a remoção de `donations_GET.xs` e `donations_POST.xs`, a change arquivada, `rodape.py`, `institucional.py`, os dois testes, o script, o guia e o `docs/design/README.md`, sem outros `.xs`; os únicos extras são as specs principais em `openspec/specs/`, atualizadas pelo arquivamento. Além disso, a suíte (825 testes) e o `openspec validate --specs --strict` (18 specs) passam hoje; a validação da change na época não tem registro.
  - Resultado parcial: 630 testes OK e `openspec validate --strict` OK; a lista foi entregue e falta a conferência do Higor.
