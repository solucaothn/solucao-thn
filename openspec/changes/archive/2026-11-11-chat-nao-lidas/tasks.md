# Tarefas

O apply vem em duas partes. **Parte A (grupos 1 a 3):** Xano. **Parte B (grupos 4 a 7):** frontend e testes, sem tocar em `xano/`, iniciada só depois do push da parte A.

## 1. Parte A: preparar o workspace do Xano

- [x] 1.1 (manual) Mostrar `git status --short --branch` e pedir a confirmação explícita do Higor antes de `xano workspace pull -d ./xano`. Depois do pull, rodar `git diff --ignore-all-space --ignore-cr-at-eol` nos endpoints do chat e em `xano/table/chat_conversation.xs` e confirmar que só há diferença de formatação. Verificação: nenhuma mudança de conteúdo feita fora do repositório.

## 2. Parte A: tabela e endpoints

- [x] 2.1 Consultar no Xano Developer MCP a declaração de campo inteiro com padrão numa tabela e o `db.edit` de um campo só. Registrar a forma no `design.md` (decisão A5). Verificação: a decisão A5 aponta a construção validada.
- [x] 2.2 Em `xano/table/chat_conversation.xs`, acrescentar `donor_last_read_message_id` e `interested_last_read_message_id` (inteiros, padrão 0), sem mudar campos, índices nem o GUID. Verificação: o arquivo passa na validação do MCP e o GUID é o mesmo.
- [x] 2.3 Em `messages_GET.xs`, pedir os dois campos no `db.get chat_conversation` e, depois de montar `$messages`, avançar só o campo de leitura de quem lê até `($messages|last).id`, quando ele for maior que o atual (decisão A2), sem log e sem mudar a resposta. Verificação: o arquivo passa na validação do MCP e o GUID é o mesmo.
- [x] 2.4 Em `conversations_GET.xs`, pedir os dois campos e acrescentar `unread_count` em cada item, com a contagem da decisão A3. Verificação: o arquivo passa na validação do MCP e o GUID é o mesmo.
- [x] 2.5 Criar `xano/api/catalog/catalog/chat/unread_total_GET.xs` (`auth = "user"`, sem inputs), que devolve só `{unread_total}` (decisão A4). Verificação: o arquivo passa na validação do MCP.
- [x] 2.6 (manual) Rodar `xano workspace push -d ./xano --dry-run` e revisar. Verificação: aparecem só os dois endpoints alterados e o novo. **A mudança na tabela não aparece no dry-run**, e isso é esperado; ela é conferida na 2.8.
- [x] 2.7 (manual) O Higor faz o push real e avisa o grupo. Verificação: o push conclui sem erros.
- [x] 2.8 (manual) No painel do Xano, abrir a tabela `chat_conversation` e conferir que `donor_last_read_message_id` e `interested_last_read_message_id` existem, são inteiros com padrão 0 e que as linhas existentes ficaram com 0. Se os campos não aparecerem, criá-los pelo painel com esses nomes e tipos, e depois rodar `xano workspace pull -d ./xano` para alinhar o arquivo. Verificação: os dois campos aparecem no painel.
- [x] 2.9 (manual) Depois do push, rodar `xano workspace pull -d ./xano` para trazer o GUID do `unread_total_GET.xs` e conferir com `Select-String` que o arquivo agora tem `guid`. Verificação: o GUID está no arquivo e não há outras mudanças de conteúdo.

## 3. Parte A: teste real e documentação do backend

- [x] 3.1 Atualizar `scripts/teste_chat_real.py` com os cenários da decisão A7, mantendo os existentes, as pausas e a regra de não imprimir tokens, e-mails nem corpos. Verificação: `python -m py_compile scripts/teste_chat_real.py` passa.
- [x] 3.2 (manual) Rodar o script contra o Xano real. Verificação: todos os cenários OK.
- [x] 3.3 Atualizar a seção do chat em `docs/guia-do-colaborador.md`: campos de leitura, `unread_count`, `GET catalog/chat/unread_total`, a marcação de leitura dentro do `GET messages`, a ausência de “visto” e a conferência manual de schema no painel após mudanças em tabela existente. Verificação: o texto bate com a spec delta `donation-chat`.

## 4. Parte B: cliente e estado (`doafacil/chat.py`)

- [x] 4.1 Exigir `unread_count` (inteiro ≥ 0) no item da lista, criar `fetch_unread_total` e `format_unread`. Verificação: `tests/test_chat.py` cobre o parsing, os valores 0, 1, 99, 100 e 150 e o rótulo acessível no singular e no plural.
- [x] 4.2 Zerar o `unread_count` da conversa ao abri-la e forçar 0 na conversa aberta ao receber a lista. Verificação: testes do estado.
- [x] 4.3 Implementar `list_poll_tick` e `list_poll_if_visible` (30 s, aba visível, pausa compartilhada após um 429, página 1 no topo sem perder nem repetir as páginas já carregadas). Verificação: testes com a aba oculta, com a pausa ativa, com um 429 e com a mesclagem.
- [x] 4.4 Implementar `unread_total` e `load_unread_total`: sem token, nenhuma chamada; erro ou 401 deixam 0 sem aviso. Verificação: testes.

## 5. Parte B: interface

- [x] 5.1 Na lista de `/chat`: círculo `#007A42` com o número, “99+” e rótulo acessível, oculto com 0; segundo `rx.moment` de 30 s sempre montado na página. Verificação: testes de componente.
- [x] 5.2 Na home: acrescentar `ChatState.load_unread_total` ao `on_load` depois de `LoginState.load_account` e mostrar o contador no link “Mensagens”, só no ramo autenticado e só com total maior que 0. Verificação: testes do cabeçalho em `tests/test_login.py` e `tests/test_public_home.py`.
- [x] 5.3 Atualizar `docs/design/README.md` (seção “Chat”) com o contador da lista e do link e com o motivo da cor `#007A42`. Verificação: o texto bate com a spec `donation-chat-interface`.

## 6. Parte B: guia

- [x] 6.1 Atualizar “Tela do chat” no guia: contador por conversa, total na home (uma vez por carregamento), lista a cada 30 s e as requisições por minuto. Verificação: o texto bate com o `design.md`.

## 7. Verificação final

- [x] 7.1 Rodar `python -m unittest discover -s tests -v` e mostrar `git status` e `git diff --stat`. Verificação: todos os testes passam e, na parte B, nada muda em `xano/`.
- [x] 7.2 (manual) No navegador, com duas contas:
  - a interessada envia 3 mensagens;
  - a dona vê “3” na lista e no link “Mensagens” da home;
  - ao abrir a conversa, o contador some;
  - a lista se atualiza sozinha em até cerca de 30 s com a aba visível;
  - não há consultas com a aba oculta;
  - “99+” aparece com mais de 99 (pode ser simulado em teste);
  - a outra pessoa não vê nenhum “visto”.

  Verificação: todos os itens conferidos e anotados.

  Anotação do Higor no navegador:
  - o contador apareceu na lista e no link “Mensagens” da home, com 4 mensagens;
  - o contador sumiu ao abrir a conversa.

  O “99+”, a aba oculta e a ausência de “visto” também estão cobertos pelos testes automáticos da 7.1.
