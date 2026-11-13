# Tarefas

Apply em duas partes:
- **Parte A (Xano):** grupos 1 a 4, até o teste real.
- **Parte B (frontend):** grupos 5 a 9.

O dry-run e o push são feitos pelo Higor.

## 1. Preparação

- [x] 1.1 (manual) Responder às dúvidas 1 a 5 do `design.md` e ajustar a spec, o design e estas tarefas se alguma resposta mudar o comportamento. Verificação: o `design.md` tem as respostas e o `openspec validate editar-perfil --strict` passa.
- [x] 1.2 Pedir confirmação ao Higor e rodar `xano workspace pull -d ./xano`. Verificação: `git diff --ignore-all-space --ignore-cr-at-eol --stat -- xano` mostra só as divergências antigas e conhecidas.
  - Pull feito pelo Higor. O diff sem espaços mostra só as divergências antigas, que não são desta change. Os `guid` da tabela `user`, do `profile_PATCH.xs`, do `profile_GET.xs`, do `donor_GET.xs` e do `mine_GET.xs` estão iguais aos de antes.

## 2. Xano (Parte A)

- [x] 2.1 Consultar no Xano Developer MCP a sintaxe de um campo novo opcional na tabela, do `text? about?` com `max:`, do enum com as 27 siglas, do `db.patch` com objeto montado no `stack` e do teste de “campo enviado” para o `about`. Verificação: as respostas anotadas no `design.md`.
- [x] 2.2 Acrescentar o `about` em `xano/table/user.xs` (decisão 1). Verificação: validação no MCP sem erros e o `guid` da tabela mantido.
- [x] 2.3 Alterar `profile_PATCH.xs` (decisão 2) e `profile_GET.xs` (decisão 3). Verificação: validação no MCP sem erros e os `guid` mantidos.
- [x] 2.4 Alterar `donations/donor_GET.xs` (decisão 4) e `donations/mine_GET.xs` (decisão 5). Verificação: validação no MCP sem erros, os `guid` mantidos e o `about` como único campo novo nas respostas.
- [x] 2.5 Mostrar ao Higor os arquivos e o `git diff -- xano` e parar antes do dry-run. Verificação: o diff tem só os arquivos desta change, além das divergências conhecidas.
- [x] 2.6 (manual) O Higor roda `xano workspace push -d ./xano --dry-run`, revisa e faz o push. Verificação: no dry-run, só a tabela `user` e os quatro endpoints como UPDATE.
  - Dry-run conferido pelo Higor: UPDATE/ADD_FIELD na tabela `user` e UPDATE no `auth/profile` (GET e PATCH), no `donations/donor` (GET) e no `donations/mine` (GET). Com o OK do grupo, o push foi feito.
- [x] 2.7 (manual) Pull pós-push. Verificação: os arquivos alterados ficaram sem mudança de lógica.
  - Os cinco arquivos continuam válidos no MCP, com os mesmos `guid`. A única mudança foi o Xano reformatar o objeto `$updates` do `profile_PATCH.xs` em várias linhas.

- [x] 2.8 (manual) Correção depois do teste real 4.1: o `PATCH auth/profile` passa a gravar sempre o `about` (com `db.edit` e `$input.about ?? ""`). O Higor roda o dry-run e o push dessa correção e depois o pull. Verificação: no dry-run, só o UPDATE do `auth/profile` (PATCH); depois do pull, o arquivo sem mudança de lógica e com o mesmo `guid`.
  - Dry-run conferido pelo Higor: só o UPDATE do `auth/profile` (PATCH). Push e pull feitos. O arquivo segue com `about: $input.about ?? ""` e o mesmo `guid`.

## 3. Teste real e documentação do backend (Parte A)

- [x] 3.1 Escrever `scripts/teste_editar_perfil_real.py` com os cenários EP1 a EP12 (decisão 6), sem imprimir nomes, e-mails, cidades, textos de Sobre, URLs nem corpos de resposta, e restaurando o perfil original num `finally`. Verificação: `python -m py_compile scripts/teste_editar_perfil_real.py` e a leitura do script pelo Higor.
- [x] 3.2 Ajustar o PP1 de `scripts/teste_perfil_real.py` e o MD2 de `scripts/teste_minhas_doacoes_real.py` para aceitar o `about`. Verificação: `py_compile` dos dois e as chaves novas nas constantes.
- [x] 3.3 Documentar no `docs/guia-do-colaborador.md` o `about`, o contrato novo do `PATCH auth/profile`, o `about` no perfil público e no `mine`, e como rodar o teste real. Verificação: o texto bate com as decisões 1 a 6.

## 4. Verificação real (Parte A)

- [x] 4.1 (manual) O Higor roda o `teste_editar_perfil_real.py` e, de novo, o `teste_perfil_real.py` e o `teste_minhas_doacoes_real.py`. Verificação: todos os cenários OK, anotados aqui.
  - **Primeira rodada do `teste_editar_perfil_real.py`:** 11 de 13. O EP8 e a restauração falharam pelo mesmo motivo: o Xano trata `""` de uma entrada opcional como omitida, e o Sobre antigo ficava.
  - **Decisão do Higor:** o `PATCH` sempre grava o `about`. Com texto, grava o texto; vazio, nulo ou omitido gravam `""`. A tela sempre envia o formulário inteiro.
  - Spec, design, guia, EP8 e restauração foram atualizados. É preciso rodar de novo depois da 2.8.
  - **Segunda rodada, depois da 2.8:** `teste_editar_perfil_real.py` com 13 de 13 (EP8 e restauração OK), `teste_perfil_real.py` com 9 de 9 e `teste_minhas_doacoes_real.py` com 20 de 20.
  - A conta de teste ficou com um Sobre de teste da primeira rodada. O Higor vai apagá-lo pela tela no roteiro manual (9.2).

## 5. Sobre no perfil público e em Minhas doações (Parte B)

- [x] 5.1 Criar o componente `about_text` (decisão 7) e usá-lo no cartão de identificação do perfil público, com o parser e o estado lendo `donor.about` (decisão 11). Verificação: testes em `tests/test_donor_profile.py` do `about` lido, do `about` nulo virando vazio, do texto simples com quebras e de não mostrar nada com o Sobre vazio.
- [x] 5.2 Mostrar o Sobre e o botão “Editar perfil” no cartão da pessoa em `/minhas-doacoes` (decisão 12). Verificação: testes em `tests/test_my_donations.py` do `owner.about`, do link para `/perfil/editar` com 44 px e da lista de itens fora do escopo atualizada.
- [x] 5.3 Atualizar no `docs/design/README.md` as seções do perfil público e de “Minhas doações”. Verificação: o texto bate com as specs delta.

## 6. Cliente e estado da edição (Parte B)

- [x] 6.1 Criar em `doafacil/editar_perfil.py` o cliente da decisão 8. Verificação: testes em `tests/test_edit_profile.py` da URL e do token, do 200, 400, 401 e 429, de resposta inválida, de campos extras ignorados e do `about` nulo.
- [x] 6.2 Criar o `EditProfileState` (decisão 9): carregamento com proteção de login, prévia, contador, validação, salvar, `account_name` atualizado e o destino depois de salvar (dúvida 5). Verificação: testes de sem token sem requisição, do preenchimento, de cada validação sem requisição, do sucesso, do erro que mantém os valores, do 401 e do primeiro nome novo no cabeçalho.

## 7. Página da edição (Parte B)

- [x] 7.1 Montar a página `/perfil/editar` da decisão 10 e registrar a rota (decisão 13). Verificação: testes de componente:
  - do cabeçalho “Voltar a Minhas doações”;
  - da prévia sem e-mail, contadores e foto;
  - das seções e do contador com `aria-live`;
  - do e-mail só de leitura com a ajuda;
  - do quadro;
  - de “Cancelar” sem requisição;
  - do `auth-card-enter`.

  Também testes da rota e do `on_load`, e `reflex compile` sem erros.
- [x] 7.2 Escrever no `docs/design/README.md` a seção “Editar perfil”, com o frame `Group 7`, as diferenças aprovadas, o contraste do campo de e-mail e do quadro, e os itens que não entram. Verificação: o texto bate com a spec delta.

## 8. Documentação do frontend (Parte B)

- [x] 8.1 Atualizar no `docs/guia-do-colaborador.md` as seções 6 e 7 e a seção de “Minhas doações” com a edição do perfil. Verificação: o texto bate com as decisões 7 a 13.

## 9. Verificação final

- [x] 9.1 Rodar `python -m unittest discover -s tests`, `openspec validate editar-perfil --strict` e `reflex compile`, e mostrar o `git diff --stat`. Verificação: tudo passa.
- [x] 9.2 (manual) No navegador, em 1512 px e 360 px, conferir:
  - a entrada sem login (vai para `/login`);
  - “Editar perfil” em `/minhas-doacoes`;
  - o formulário preenchido e a prévia acompanhando a digitação;
  - o contador do Sobre;
  - o e-mail só de leitura;
  - salvar com sucesso, com o cabeçalho da home mostrando o nome novo;
  - salvar com erro de validação;
  - “Cancelar”;
  - o Sobre no perfil público e em “Minhas doações”, e nada com o Sobre vazio;
  - a cidade das doações antigas sem mudar;
  - nenhuma rolagem horizontal e o contraste.

  Verificação: os itens conferidos e anotados.

  - **Conferido pelo Higor no navegador, tudo OK:**
    - entrada sem login, “Editar perfil” em Minhas doações, formulário e prévia, contador do Sobre;
    - salvar com sucesso (com o nome novo no cabeçalho) e com erro, “Cancelar”;
    - o Sobre no perfil público e em Minhas doações (e nada quando vazio);
    - a cidade das doações antigas sem mudar, o celular sem rolagem horizontal e o contraste.
  - **Ajustes feitos durante o roteiro e conferidos de novo:**
    - o texto digitado e colado ficou escuro e opaco em Editar perfil, login, chat e cadastro de doação, inclusive com o tema escuro do sistema. A correção é a regra global de campos no `app.style`;
    - o e-mail ficou legível, com o cadeado, somente leitura e copiável.
