# Tarefas

O apply é feito em duas partes:

- **Parte A (Xano):** grupos 1 a 4, até o teste real e a remoção da function pelo painel.
- **Parte B (frontend):** grupos 5 a 8.

O dry-run e o push são sempre feitos pelo Higor.

## 1. Preparação

- [x] 1.1 (manual) Responder às dúvidas 1 a 5 do `design.md` e ajustar a spec, o design e estas tarefas se alguma resposta mudar o comportamento. Verificação: o `design.md` tem as respostas, e o `openspec validate perfil-credibilidade --strict` passa.
- [x] 1.2 (manual) O Higor roda `xano workspace pull -d ./xano`. Verificação: o `git diff --ignore-all-space --ignore-cr-at-eol --stat -- xano` mostra só as divergências antigas e conhecidas.
  - Pull feito pelo Higor. As divergências antigas são só de formatação (`signup_POST`, `signup_resend_POST`, `signup_verify_POST`, `send_confirmation_code`, `donation_photo` e `signup_pending`) e não são desta change. Os `guid` da `user` e dos cinco endpoints estão no lugar.

## 2. Xano (Parte A)

- [x] 2.1 Consultar no Xano Developer MCP:
  - o default de um `bool` opcional e o valor lido nas linhas antigas;
  - a comparação `== true` com `null`;
  - a sintaxe da task, com `starts_on`, `freq` e `ends_on`, e se ela pode rodar na hora pelo painel;
  - o `debug.log` dentro de uma task;
  - a leitura de `event_log` só com `user_id`, sem repetição.

  Verificação: as respostas anotadas no `design.md`.
  - Anotadas em “5a. Duas formas de rodar a marcação”, no `design.md`. Achado: remover objetos exige `push --sync --delete`, e por isso a remoção passa a ser pelo painel (4.2).
- [x] 2.2 Acrescentar `bool email_verified?=false` à tabela `user` (decisão 1) e `email_verified: true` ao `db.add user` do `signup_verify_POST.xs` (decisão 2). Verificação: validação no MCP, os `guid` mantidos e nenhuma outra mudança de lógica no `signup_verify`.
- [x] 2.3 Acrescentar os contadores e o `email_verified` ao `profile_GET.xs`, ao `mine_GET.xs` (com o `owner.email`), ao `donor_GET.xs` e ao `detail_GET.xs`, com os nomes da decisão 3 e as contagens da decisão 4. Verificação:
  - validação no MCP e os `guid` mantidos;
  - o selo sempre como booleano;
  - nenhum e-mail no `donor` nem no `detail`;
  - o `total` e a paginação do `donor` sem mudança.
- [x] 2.4 Escrever a function `xano/function/credibilidade/marcar_email_verificado_inicial.xs` (entrada `aplicar?=false`) e a task `xano/task/marcar_email_verificado_inicial.xs`, que chama a function com `aplicar: false`. Seguir o critério, a idempotência e o log só com números (decisões 5 e 5a). Verificação:
  - validação no MCP;
  - leitura do Higor;
  - nenhum e-mail, nome ou id no `debug.log`.
  - Como foi usada a Forma 2, a task nunca foi publicada, e o arquivo local `xano/task/marcar_email_verificado_inicial.xs` foi apagado.
- [x] 2.5 Mostrar ao Higor os arquivos e o `git diff -- xano` e parar antes do dry-run. Verificação: o diff tem só os arquivos desta change, além das divergências conhecidas.
- [x] 2.6 (manual) O Higor roda o dry-run, revisa e faz o push. Depois faz o pull. Verificação:
  - no dry-run, o ADD_FIELD em `user`, 2 CREATE (a function e a task) e 5 UPDATE (`signup_verify`, `auth/profile` GET, `mine`, `donor` e `detail`);
  - depois do pull, só o `guid` novo da function e o da task.

  Se a task for recusada, vale a Forma 2 da decisão 5a: o push sai sem a task (`-e "task/**"`), com 1 CREATE.
  - Usada a Forma 2: push com `-e "task/**"`, com o ADD_FIELD em `user`, 1 CREATE (a function) e os 5 UPDATE. Depois do pull, a function ganhou o `guid`.
- [x] 2.7 (manual) A rodada de contagem: a task roda com `aplicar: false` (Forma 1) ou o Higor roda a function no Run & Debug com `aplicar = false` (Forma 2) e lê as contagens. Verificação: os números anotados aqui e conferidos (por exemplo, as contas de teste dos scripts entre as de `a_marcar`, e `contas_marcadas = 0`).
  - Forma 2, no Run & Debug com `aplicar = false`: `eventos` 6, `contas_com_evento` 6, `a_marcar` 3, `conta_inexistente` 3 (eventos de contas já apagadas), `fora_da_data` 0 e `total_de_contas` 3.
- [x] 2.8 A rodada de aplicação. Na Forma 1, trocar a task para `aplicar: true`, com um novo `starts_on`, e mostrar o diff; o Higor roda o dry-run, faz o push e deixa a task rodar. Na Forma 2, o Higor roda a function com `aplicar = true`, sem push. Verificação:
  - na Forma 1, só o UPDATE da task no dry-run;
  - `contas_marcadas` igual ao `a_marcar` da 2.7;
  - uma nova contagem (`aplicar = false`) com `a_marcar = 0`.
  - Forma 2, com `aplicar = true`: `contas_marcadas` 3, igual ao `a_marcar` da 2.7, e `verificadas_no_fim` 3, igual ao `total_de_contas`. Assim, todas as contas estão marcadas e uma nova contagem daria `a_marcar = 0`.

## 3. Teste real e documentação do backend (Parte A)

- [x] 3.1 Escrever `scripts/teste_perfil_credibilidade_real.py`, que não imprime nomes, e-mails, ids nem corpos de resposta. Os cenários:
  - PC1 a PC4: os tipos e os nomes dos campos novos nas quatro respostas;
  - PC5: os contadores iguais entre o `auth/profile`, a `mine` e, para uma doação disponível da própria conta, o `donor` e o `detail`;
  - PC6: o `owner.email` da `mine` igual ao e-mail do `auth/profile`, comparado sem imprimir;
  - PC7: nenhum e-mail no `donor` nem no `detail`;
  - PC8: a conta de teste, criada pelo `signup_verify`, com o selo verdadeiro;
  - PC9: um `PATCH auth/profile` com `email_verified: false` não muda o selo;
  - PC10: o 401 sem token no `profile` e na `mine`.

  Verificação: `py_compile` e a leitura do script pelo Higor.
- [x] 3.2 Ajustar as chaves esperadas no PP1 (`teste_perfil_real.py`), no MD2 (`teste_minhas_doacoes_real.py`) e no EP2, no EP3 e no EP11 (`teste_editar_perfil_real.py`). Verificação: `py_compile` dos três.
  - Feito, com estes detalhes:
    - o PP2 e o MD2b também conferem os tipos novos;
    - o EP3 não muda, porque a resposta do PATCH continua sem o selo e sem os contadores;
    - o MD3a passou a tirar só o `owner.email` antes de procurar `@` e chaves proibidas;
    - o FP3 (`teste_foto_perfil_real.py`) também compara as chaves exatas do perfil e foi ajustado.
  - O `py_compile` passou nos cinco scripts.
- [x] 3.3 Documentar no `docs/guia-do-colaborador.md`:
  - o campo `email_verified`;
  - o critério e o histórico da marcação inicial, só com as contagens;
  - os campos novos de cada resposta;
  - como rodar o teste real.

  Verificação: o texto bate com as decisões 1 a 5.

## 4. Verificação real e limpeza (Parte A)

- [x] 4.1 (manual) O Higor roda o `teste_perfil_credibilidade_real.py` e, de novo, os três scripts ajustados. Verificação: todos os cenários OK, anotados aqui.
  - Resultados:

    | Script | Cenários OK |
    |---|---|
    | `teste_perfil_credibilidade_real.py` | 10/10 |
    | `teste_perfil_real.py` | 9/9 |
    | `teste_minhas_doacoes_real.py` | 20/20 |
    | `teste_editar_perfil_real.py` | 13/13 |
    | `teste_foto_perfil_real.py` | 13/13 |
- [x] 4.2 (manual) O Higor apaga a function **no painel do Xano**, sem `push --sync --delete` (decisão 5a). A task não existe, porque foi usada a Forma 2. Depois ele faz o pull, e o arquivo local da function sai. Verificação: depois do pull, a function não volta, e o `git diff --stat -- xano` não mostra outra remoção.
  - O Higor apagou a function pelo painel. O código dela foi copiado para o apêndice do `design.md`, e o arquivo local e a pasta `xano/function/credibilidade/` foram apagados.

## 5. Componentes e leitura (Parte B)

- [x] 5.1 Criar o `verified_badge` e o `donation_counts` em `doafacil/perfil_publico.py` (decisão 6) e fazer “Minhas doações” usar o `donation_counts`. Verificação:
  - testes do selo (verdadeiro mostra o ícone `aria-hidden` e o texto; falso não renderiza nada);
  - testes do singular e do plural;
  - o contraste do selo medido em teste (AA).
- [x] 5.2 Ler o `email_verified` e os contadores nos parsers e estados da prévia (`auth/profile`), de “Minhas doações” (com o e-mail), do perfil público e do detalhe. Verificação: testes de cada parser (verdadeiro, falso, tipo inválido e contador negativo ou não inteiro) e de cada estado.

## 6. Telas (Parte B)

- [x] 6.1 Mostrar o e-mail e o selo no cartão de “Minhas doações”, seguindo o frame `Group 6` lido no Figma. Verificação: testes de componente com e sem selo e com um e-mail longo, sem estourar a largura.
- [x] 6.2 Mostrar os contadores e o selo na prévia de `/perfil/editar`, sem o e-mail. Verificação: testes de componente, com o teste atual “prévia sem contadores” atualizado.
- [x] 6.3 Mostrar os contadores e o selo no perfil público e no cartão “Quem doa” do detalhe. Verificação:
  - testes de componente;
  - nenhum e-mail renderizado;
  - o cartão “Quem doa” continua como link único com o mesmo rótulo.

## 7. Documentação (Parte B)

- [x] 7.1 Atualizar no `docs/design/README.md` o “Minhas doações” (o e-mail e o selo), o “Editar perfil” (a prévia), o perfil público e o detalhe, tirando as menções “sem selo”. Atualizar também o `docs/guia-do-colaborador.md` com os componentes. Verificação: o texto bate com as specs delta.

## 8. Verificação final

- [x] 8.1 Rodar `python -m unittest discover -s tests`, `openspec validate perfil-credibilidade --strict` e `reflex compile`, e mostrar o `git diff --stat`. Verificação: tudo passa.
- [ ] 8.2 (manual) No navegador, em 1512 px e 360 px, conferir:
  - o selo e os contadores na prévia, em “Minhas doações” (com o e-mail), no perfil público e no “Quem doa”, vistos também por outra conta, sem o e-mail fora de “Minhas doações”;
  - uma conta sem selo, sem nenhum espaço no lugar dele;
  - nenhuma rolagem horizontal e o contraste.

  Verificação: os itens conferidos e anotados.
