# Tarefas

O apply é feito em duas partes:

- **Parte A (Xano):** grupos 1 a 4, até o teste real e o push que apaga a task.
- **Parte B (frontend):** grupos 5 a 8.

O dry-run e o push são sempre feitos pelo Higor.

## 1. Preparação

- [ ] 1.1 (manual) Responder às dúvidas 1 a 5 do `design.md` e ajustar a spec, o design e estas tarefas se alguma resposta mudar o comportamento. Verificação: o `design.md` tem as respostas, e o `openspec validate perfil-credibilidade --strict` passa.
- [ ] 1.2 (manual) O Higor roda `xano workspace pull -d ./xano`. Verificação: o `git diff --ignore-all-space --ignore-cr-at-eol --stat -- xano` mostra só as divergências antigas e conhecidas.

## 2. Xano (Parte A)

- [ ] 2.1 Consultar no Xano Developer MCP:
  - o default de um `bool` opcional e o valor lido nas linhas antigas;
  - a comparação `== true` com `null`;
  - a sintaxe da task, com `starts_on`, `freq` e `ends_on`, e se ela pode rodar na hora pelo painel;
  - o `debug.log` dentro de uma task;
  - a leitura de `event_log` só com `user_id`, sem repetição.

  Verificação: as respostas anotadas no `design.md`.
- [ ] 2.2 Acrescentar `bool email_verified?=false` à tabela `user` (decisão 1) e `email_verified: true` ao `db.add user` do `signup_verify_POST.xs` (decisão 2). Verificação: validação no MCP, os `guid` mantidos e nenhuma outra mudança de lógica no `signup_verify`.
- [ ] 2.3 Acrescentar os contadores e o `email_verified` ao `profile_GET.xs`, ao `mine_GET.xs` (com o `owner.email`), ao `donor_GET.xs` e ao `detail_GET.xs`, com os nomes da decisão 3 e as contagens da decisão 4. Verificação:
  - validação no MCP e os `guid` mantidos;
  - o selo sempre como booleano;
  - nenhum e-mail no `donor` nem no `detail`;
  - o `total` e a paginação do `donor` sem mudança.
- [ ] 2.4 Escrever a `xano/task/marcar_email_verificado_inicial.xs` em modo contagem (`$aplicar = false`), com o critério, a idempotência e o log só com números (decisão 5). Verificação:
  - validação no MCP;
  - leitura do Higor;
  - nenhum e-mail, nome ou id no `debug.log`.
- [ ] 2.5 Mostrar ao Higor os arquivos e o `git diff -- xano` e parar antes do dry-run. Verificação: o diff tem só os arquivos desta change, além das divergências conhecidas.
- [ ] 2.6 (manual) O Higor roda o dry-run, revisa e faz o push. Depois faz o pull. Verificação:
  - no dry-run, o ADD_FIELD em `user`, 1 CREATE (a task) e 5 UPDATE (`signup_verify`, `auth/profile` GET, `mine`, `donor` e `detail`);
  - depois do pull, os arquivos só com o `guid` novo da task.
- [ ] 2.7 (manual) A task roda em modo contagem, e o Higor lê o log no Xano. Verificação: os números anotados aqui e conferidos (por exemplo, as contas de teste dos scripts entre as que seriam marcadas).
- [ ] 2.8 Trocar a task para `$aplicar = true` e mostrar o diff. O Higor roda o dry-run, faz o push e deixa a task rodar. Verificação:
  - no dry-run, só o UPDATE da task;
  - no log, `contas_marcadas` igual ao número contado na 2.7;
  - uma segunda execução, se houver, com `contas_marcadas = 0`.

## 3. Teste real e documentação do backend (Parte A)

- [ ] 3.1 Escrever `scripts/teste_perfil_credibilidade_real.py`, que não imprime nomes, e-mails, ids nem corpos de resposta. Os cenários:
  - PC1 a PC4: os tipos e os nomes dos campos novos nas quatro respostas;
  - PC5: os contadores iguais entre o `auth/profile`, a `mine` e, para uma doação disponível da própria conta, o `donor` e o `detail`;
  - PC6: o `owner.email` da `mine` igual ao e-mail do `auth/profile`, comparado sem imprimir;
  - PC7: nenhum e-mail no `donor` nem no `detail`;
  - PC8: a conta de teste, criada pelo `signup_verify`, com o selo verdadeiro;
  - PC9: um `PATCH auth/profile` com `email_verified: false` não muda o selo;
  - PC10: o 401 sem token no `profile` e na `mine`.

  Verificação: `py_compile` e a leitura do script pelo Higor.
- [ ] 3.2 Ajustar as chaves esperadas no PP1 (`teste_perfil_real.py`), no MD2 (`teste_minhas_doacoes_real.py`) e no EP2, no EP3 e no EP11 (`teste_editar_perfil_real.py`). Verificação: `py_compile` dos três.
- [ ] 3.3 Documentar no `docs/guia-do-colaborador.md`:
  - o campo `email_verified`;
  - o critério e o histórico da marcação inicial, só com as contagens;
  - os campos novos de cada resposta;
  - como rodar o teste real.

  Verificação: o texto bate com as decisões 1 a 5.

## 4. Verificação real e limpeza (Parte A)

- [ ] 4.1 (manual) O Higor roda o `teste_perfil_credibilidade_real.py` e, de novo, os três scripts ajustados. Verificação: todos os cenários OK, anotados aqui.
- [ ] 4.2 Apagar a `xano/task/marcar_email_verificado_inicial.xs`. O Higor roda o dry-run, faz o push e depois o pull. Verificação: no dry-run, só o DELETE da task; depois do pull, a task não volta.

## 5. Componentes e leitura (Parte B)

- [ ] 5.1 Criar o `verified_badge` e o `donation_counts` em `doafacil/perfil_publico.py` (decisão 6) e fazer “Minhas doações” usar o `donation_counts`. Verificação:
  - testes do selo (verdadeiro mostra o ícone `aria-hidden` e o texto; falso não renderiza nada);
  - testes do singular e do plural;
  - o contraste do selo medido em teste (AA).
- [ ] 5.2 Ler o `email_verified` e os contadores nos parsers e estados da prévia (`auth/profile`), de “Minhas doações” (com o e-mail), do perfil público e do detalhe. Verificação: testes de cada parser (verdadeiro, falso, tipo inválido e contador negativo ou não inteiro) e de cada estado.

## 6. Telas (Parte B)

- [ ] 6.1 Mostrar o e-mail e o selo no cartão de “Minhas doações”, seguindo o frame `Group 6` lido no Figma. Verificação: testes de componente com e sem selo e com um e-mail longo, sem estourar a largura.
- [ ] 6.2 Mostrar os contadores e o selo na prévia de `/perfil/editar`, sem o e-mail. Verificação: testes de componente, com o teste atual “prévia sem contadores” atualizado.
- [ ] 6.3 Mostrar os contadores e o selo no perfil público e no cartão “Quem doa” do detalhe. Verificação:
  - testes de componente;
  - nenhum e-mail renderizado;
  - o cartão “Quem doa” continua como link único com o mesmo rótulo.

## 7. Documentação (Parte B)

- [ ] 7.1 Atualizar no `docs/design/README.md` o “Minhas doações” (o e-mail e o selo), o “Editar perfil” (a prévia), o perfil público e o detalhe, tirando as menções “sem selo”. Atualizar também o `docs/guia-do-colaborador.md` com os componentes. Verificação: o texto bate com as specs delta.

## 8. Verificação final

- [ ] 8.1 Rodar `python -m unittest discover -s tests`, `openspec validate perfil-credibilidade --strict` e `reflex compile`, e mostrar o `git diff --stat`. Verificação: tudo passa.
- [ ] 8.2 (manual) No navegador, em 1512 px e 360 px, conferir:
  - o selo e os contadores na prévia, em “Minhas doações” (com o e-mail), no perfil público e no “Quem doa”, vistos também por outra conta, sem o e-mail fora de “Minhas doações”;
  - uma conta sem selo, sem nenhum espaço no lugar dele;
  - nenhuma rolagem horizontal e o contraste.

  Verificação: os itens conferidos e anotados.
