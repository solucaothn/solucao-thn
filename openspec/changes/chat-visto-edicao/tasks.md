# Tarefas

O apply vem em duas partes. **Parte A (grupos 1 a 3):** Xano. **Parte B (grupos 4 a 7):** frontend e testes, sem tocar em `xano/`, iniciada só depois do push da parte A.

## 1. Parte A: preparar o workspace do Xano

- [ ] 1.1 (manual) Mostrar `git status --short --branch` e pedir a confirmação explícita do Higor antes de `xano workspace pull -d ./xano`. Depois do pull, rodar `git diff --ignore-all-space --ignore-cr-at-eol` nos endpoints do chat e em `xano/table/chat_message.xs` e confirmar que só há diferença de formatação. Verificação: nenhuma mudança de conteúdo feita fora do repositório.

## 2. Parte A: tabela e endpoints

- [ ] 2.1 Consultar no Xano Developer MCP as construções da decisão A6 e registrar a forma validada no `design.md`. Verificação: a A6 aponta as construções validadas.
- [ ] 2.2 Em `xano/table/chat_message.xs`, acrescentar `edited_at` (timestamp opcional, sem padrão), sem mudar campos, índices nem o GUID. Verificação: o arquivo passa na validação do MCP e o GUID é o mesmo.
- [ ] 2.3 Em `messages_GET.xs`, implementar as decisões A1 e A4, sem mudar a marcação de leitura nem os três modos:
  - `server_time` no início;
  - `other_last_read_message_id`;
  - `edited_at` em cada mensagem;
  - o input `edited_since` e a lista `edited_messages`.

  Verificação: o arquivo passa na validação do MCP e o GUID é o mesmo.
- [ ] 2.4 Em `messages_POST.xs`, devolver `edited_at` (decisão A5), sem mudar a regra de envio. Verificação: o arquivo passa na validação do MCP e o GUID é o mesmo.
- [ ] 2.5 Criar `xano/api/catalog/catalog/chat/messages_PATCH.xs` com as checagens, a resposta e o log da decisão A3. Verificação: o arquivo passa na validação do MCP.
- [ ] 2.6 (manual) Rodar `xano workspace push -d ./xano --dry-run` e revisar. Verificação: aparecem só os dois endpoints alterados e o novo. **A mudança na tabela não aparece no dry-run**, e isso é esperado; ela é conferida na 2.8.
- [ ] 2.7 (manual) O Higor faz o push real e avisa o grupo. Verificação: o push conclui sem erros.
- [ ] 2.8 (manual) No painel do Xano, abrir `chat_message` e conferir que `edited_at` existe, é timestamp e está vazio nas linhas antigas. Se não aparecer, criá-lo pelo painel com esse nome e tipo e rodar `xano workspace pull -d ./xano`. Verificação: o campo aparece no painel.
- [ ] 2.9 (manual) Depois do push, rodar `xano workspace pull -d ./xano` para trazer o GUID do `messages_PATCH.xs`. Verificação: o GUID está no arquivo, e o `git diff --ignore-all-space --ignore-cr-at-eol` não mostra outras mudanças de conteúdo.

## 3. Parte A: teste real e documentação do backend

- [ ] 3.1 Atualizar `scripts/teste_chat_real.py` com os cenários da decisão A7, nos dois modos, mantendo os existentes, as pausas e a regra de não imprimir tokens, e-mails nem textos. Verificação: `python -m py_compile scripts/teste_chat_real.py` passa.
- [ ] 3.2 (manual) Rodar o script contra o Xano real. Verificação: todos os cenários OK, com os opcionais pulados com aviso quando faltar dado.
- [ ] 3.3 Atualizar a seção do chat em `docs/guia-do-colaborador.md` com:
  - `edited_at`, o `PATCH catalog/chat/messages` e as regras de edição;
  - `other_last_read_message_id`, `edited_since`, `edited_messages` e `server_time`;
  - o log `chat_message_edited`;
  - a decisão aprovada de mostrar o “visto”, que substitui o “sem visto”.

  Verificação: o texto bate com a spec delta `donation-chat`.

## 4. Parte B: cliente e estado (`doafacil/chat.py`)

- [ ] 4.1 Fazer o parsing da decisão 1 do frontend: `edited_at` em cada mensagem, `other_last_read_message_id`, `server_time` e `edited_messages`. Criar `edit_message` e o parâmetro `edited_since` em `fetch_messages`. Verificação: `tests/test_chat.py` cobre respostas válidas e malformadas, a requisição do PATCH e a classificação de erros.
- [ ] 4.2 Calcular `is_read`, `edited` e `editable` em `_decorate_messages`, com `other_last_read_id` que só aumenta e volta a zero ao trocar de conversa. Verificação: testes com uma mensagem própria lida e outra não lida, uma da outra pessoa, uma editada, uma com 14 e outra com 16 minutos, e com a conversa somente leitura.
- [ ] 4.3 Na consulta automática, mandar `edited_since`, aplicar `edited_messages` pelo id, atualizar `other_last_read_id` e `last_server_time` e recalcular as marcas. Verificação: testes da primeira consulta sem `edited_since`, de uma edição recebida, de uma repetida, do ✓✓ atualizado e de nenhuma requisição a mais.
- [ ] 4.4 Implementar `start_edit`, `cancel_edit` e o caminho de edição no `send_message` com os textos de erro da decisão 5. Implementar também `toggle_message_selection`, para o toque no celular. Verificação: testes de salvar, cancelar sem requisição, texto igual, 400 com o lápis escondido, 404, 429, texto vazio ou longo sem requisição e troca de conversa durante a edição.

## 5. Parte B: interface

- [ ] 5.1 Na bolha, implementar o “visto” da decisão 4 e o “(editada)” na linha do horário. Verificação: testes de componente.
- [ ] 5.2 Implementar o lápis da decisão 6: classes, `aria-label`, `data-selected`, `assets/chat.css` registrado em `stylesheets` e o lápis só nas mensagens editáveis. Implementar também o modo de edição do campo, com “Editando mensagem”, “Salvar” e “Cancelar”. Verificação: testes de componente e do CSS (hover, foco e seleção).
- [ ] 5.3 Atualizar `docs/design/README.md` (seção “Chat”) com o “visto”, as cores, o lápis no hover e no toque, o modo de edição e o “(editada)”. Verificação: o texto bate com a spec `donation-chat-interface`.

## 6. Parte B: guia

- [ ] 6.1 Atualizar “Tela do chat” no guia: o “visto”, a edição, como as edições chegam à outra pessoa sem requisição a mais e os textos de erro. Verificação: o texto bate com o `design.md`.

## 7. Verificação final

- [ ] 7.1 Rodar `python -m unittest discover -s tests -v` e mostrar `git status` e `git diff --stat`. Verificação: todos os testes passam e, na parte B, nada muda em `xano/`.
- [ ] 7.2 (manual) No navegador, com duas contas:
  - a interessada envia uma mensagem e vê ✓ cinza;
  - a dona abre a conversa e, em até cerca de 15 s, a interessada vê ✓✓ verde;
  - a interessada edita a mensagem pelo lápis (hover no computador, toque no celular) e vê “(editada)”;
  - a dona vê o texto novo e “(editada)” em até cerca de 15 s;
  - “Cancelar” não muda nada;
  - o lápis não aparece em mensagem da outra pessoa nem depois de 15 minutos.

  Verificação: todos os itens conferidos e anotados.
