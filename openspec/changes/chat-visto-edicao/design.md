# Design

## Contexto

- **`chat_conversation`** já tem `donor_last_read_message_id` e `interested_last_read_message_id`, da `chat-nao-lidas`. Depois do pull, eles vêm como `int …?`, sem padrão, e os endpoints os leem com `?? 0`.
- **`chat_message`** tem `id`, `created_at`, `conversation_id`, `sender_id` e `text`. Não tem nada sobre edição.
- **`messages_GET`:**
  - já busca a conversa com os dois campos de leitura e marca a leitura de quem lê;
  - devolve as mensagens nos três modos (sem cursor, `before_message_id` e `after_message_id`), com `sent_by_me` e o primeiro nome.
- **`messages_POST`:** valida o tamanho antes de tudo e devolve 404 genérico para não participante e para doação concluída. Tem o limite de 10 envios em 60 s e registra `chat_message_sent`.
- **Frontend (`doafacil/chat.py`):**
  - `poll_if_visible` busca a cada 15 s, só com a aba visível, com `after_message_id`;
  - `_decorate_messages` monta os rótulos de dia e de horário;
  - o horário fica embaixo da bolha, em `#6b6b6b`;
  - um único `rx.form` com o campo `chat-message-input` envia com Enter ou com o botão.
- **Limite da plataforma:** 10 requisições por 20 s para a instância inteira.
- **Dry-run do Xano:** não mostra mudança de schema em tabela existente.

## Objetivos / Fora do escopo

**Objetivos:**
- “visto” nas próprias mensagens e edição por 15 minutos;
- a outra pessoa vê o ✓✓ e as edições sem nenhuma requisição HTTP a mais.

**Fora do escopo:** apagar mensagens, histórico de versões, horário da leitura e atualização em tempo real.

## Decisões: backend (parte A)

**A1. O “visto” vem do campo que já existe.**
- O `messages_GET` passa a responder `other_last_read_message_id`:
  - se quem consulta é `donor_id`, é `interested_last_read_message_id ?? 0`;
  - senão, é `donor_last_read_message_id ?? 0`.
- O valor vai em todos os modos, inclusive na atualização automática com `after_message_id`. Assim o ✓✓ das mensagens já exibidas se atualiza sem requisição a mais.
- **Só um número, em nível de página**, e não um `read` por mensagem, porque a atualização automática não reenvia as mensagens antigas. O frontend compara: uma mensagem própria com `id <= other_last_read_message_id` foi lida.
- **A lista, o total, o envio e a edição continuam sem nenhum dado de leitura da outra pessoa.**
- *Alternativa descartada: endpoint próprio para o “visto”.* Custaria 1 requisição a mais a cada 15 s por aba.

**A2. Campo `edited_at` em `chat_message`.**
- É um timestamp opcional, sem padrão e vazio até a primeira edição. A forma (`timestamp edited_at?`) será confirmada no MCP.
- Fica vazio nas mensagens antigas, e isso é o esperado: nenhuma delas foi editada.
- *Alternativa descartada: guardar o texto original.* Ninguém precisa dele, e seria mais um dado pessoal guardado.

**A3. Endpoint novo `PATCH catalog/chat/messages`** (`auth = "user"`; inputs `int message_id` e `text? message_text? filters=trim`, como no POST).

| Ordem | Checagem | Recusa |
|---|---|---|
| 1 | Texto com 1 a 1000 caracteres | 400, antes de qualquer consulta, como no envio |
| 2 | A mensagem existe e `sender_id == $auth.id` | 404 genérico “Conversa não encontrada.” |
| 3 | A conversa existe e a pessoa participa (defesa extra) | 404 genérico |
| 4 | A doação existe e está disponível ou reservada | 404 genérico, como no envio após a conclusão |
| 5 | `created_at >= now - 900 s` | 400 com “O prazo para editar esta mensagem terminou.” |

- **Texto igual ao atual:** responde 200 com a mensagem, sem gravar e sem log.
- **Texto diferente:** um `db.edit chat_message` com `text` e `edited_at: now`, seguido de `log_event` com `{user_id: $auth.id, action: "chat_message_edited"}`.
- **Resposta:** no mesmo formato de uma mensagem do GET (`id`, `conversation_id`, `sender_first_name`, `sent_by_me: true`, `text`, `created_at` e `edited_at`).
- **Sem limite próprio de edições** (veja as dúvidas). Valem o limite da plataforma e o prazo de 15 minutos por mensagem.
- **A ordem das checagens tem um motivo:** uma mensagem da outra pessoa, inexistente ou de doação concluída recebe sempre o 404, mesmo fora do prazo. O 400 do prazo só aparece para quem enviou, então não revela nada.

**A4. As edições chegam à outra pessoa pela consulta que já existe.**
- **`server_time`:** o `messages_GET` grava `now` numa variável no início da pilha e o devolve como `server_time` em todos os modos.
- **`edited_since`:** um input novo opcional (`int edited_since?`), usado só junto com `after_message_id`. Com ele, uma consulta a mais no banco, não uma requisição HTTP a mais, busca as mensagens da conversa com:
  - `id <= after_message_id`;
  - `edited_at >= edited_since - 5000` (5 s de folga para uma edição gravada durante a consulta anterior);
  - ordem crescente e no máximo 100.
- **Resposta:** essas mensagens vão em `edited_messages`, no mesmo formato. Sem `edited_since`, ou fora do modo `after_message_id`, `edited_messages` vem vazia.
- **O horário vem só do servidor:** o frontend guarda o `server_time` da última resposta e o devolve como `edited_since`, então o relógio do navegador não entra na conta.
- **A folga pode repetir mensagens**, e isso não é problema: o frontend substitui pelo id.
- **Ao abrir a conversa, nada se perde:** a consulta sem cursor já traz o texto atual de todas as mensagens, com `edited_at`.
- **As consultas no XanoScript:**
  - a busca das editadas fica num `conditional` (`$input.edited_since != null`), sem `$input` nulo no `where`, como nos outros endpoints;
  - o nome do remetente das editadas é montado no mesmo laço que já existe, passando por ele as duas listas.

**A5. `messages_POST`** passa a pedir `edited_at` no `output` do `db.add` e a devolver esse campo, vazio, na resposta. A regra de envio não muda.

**A6. Sintaxe, GUID e schema.**
- **A confirmar no Xano Developer MCP:**
  - o timestamp opcional;
  - a comparação de `created_at` com `now|add_secs_to_timestamp:(-900|to_int)`;
  - a comparação de `edited_at` com um inteiro em milissegundos;
  - o `db.edit` com dois campos;
  - um `where` com um campo que pode estar vazio.
- **GUID:** o endpoint novo só ganha GUID depois do push e do pull.
- **Schema:** depois do push, conferir no painel que `chat_message` tem `edited_at`, vazio nas linhas antigas.

**A7. Teste real.** `scripts/teste_chat_real.py` ganha cenários que rodam também no modo rápido:
- `other_last_read_message_id` antes e depois de a outra pessoa ler (✓ e depois ✓✓);
- edição própria → 200 com `edited_at`;
- a outra pessoa recebe a mensagem em `edited_messages` ao consultar com `after_message_id` e `edited_since`;
- texto igual → 200 sem mudar `edited_at`;
- editar mensagem da outra pessoa → 404, e id inexistente → 404;
- texto vazio ou com 1001 caracteres → 400;
- edição sem token → 401.

**Cenários que não rodam sempre:**
- **Fora do prazo:** usa uma mensagem própria com mais de 15 minutos, se a conversa tiver uma de outra execução. Senão, o cenário é pulado com aviso.
- **Doação concluída:** entra no cenário 9, que é opcional.

## Decisões: frontend (parte B)

1. **Parsing.**
   - Cada mensagem passa a ter `edited_at`, inteiro ou vazio, campo obrigatório.
   - A página passa a ter `other_last_read_message_id` (inteiro ≥ 0), `server_time` (inteiro) e `edited_messages` (lista).
   - Cliente novo: `edit_message(client, token, message_id, text)`, com a mesma classificação de erros.
   - `fetch_messages` ganha o parâmetro `edited_since`.
2. **Estado.**
   - **Campos novos:** `other_last_read_id`, `last_server_time` e `editing_message_id`.
   - **`other_last_read_id`** recebe o maior valor entre o atual e o da resposta, para não piscar se duas abas lerem ao mesmo tempo. Volta a zero ao trocar de conversa.
   - **`_decorate_messages`** passa a marcar em cada mensagem:
     - `is_read`: própria e lida;
     - `edited`: tem `edited_at`;
     - `editable`: própria, enviada há menos de 15 minutos e fora de conversa somente leitura.
   - **Recálculo:** essas marcas são recalculadas a cada resposta da consulta automática, então o lápis some sozinho perto do fim do prazo. O backend é quem decide; um 400 esconde o lápis daquela mensagem na hora.
3. **Consulta automática.**
   - `poll_if_visible` manda `edited_since=last_server_time` quando já tem o valor.
   - Ao receber a resposta, aplica `edited_messages`, trocando `text` e `edited_at` das mensagens já exibidas pelo id. Também atualiza `other_last_read_id` e `last_server_time`.
   - A abertura da conversa e o “Carregar anteriores” também atualizam `other_last_read_id`.
   - Nenhuma requisição a mais.
4. **“Visto”** embaixo da bolha, na linha do horário: `12:41 (editada) ✓✓`.
   - **✓ (enviada):** ícone `check` em `#6b6b6b`, com o rótulo acessível “Enviada”.
   - **✓✓ (lida):** ícone `check-check` em `#007A42`, com o rótulo acessível “Lida”.
   - **Contraste:** o `#007A42` sobre o creme `#FFF6E8` fica em torno de 5:1, acima do 3:1 pedido para ícones.
   - **Fora da bolha, e não dentro como no WhatsApp,** porque o horário já fica embaixo dela.
   - **Nas mensagens da outra pessoa** não aparece nada.
5. **Edição no próprio campo de baixo.** É a opção mais simples: um só campo, o mesmo `form` e o mesmo Enter, sem um campo por bolha dentro do `foreach`.
   - **Começar:** o lápis chama `start_edit(id)`, que guarda `editing_message_id` e preenche o campo com `rx.set_value(MESSAGE_INPUT_ID, texto)`.
   - **Aviso e botões:** acima do campo aparece “Editando mensagem”; o botão “Enviar” vira “Salvar” e aparece “Cancelar”.
   - **Salvar:** o `on_submit` do form vê `editing_message_id` e chama a edição, e não o envio. A bolha é trocada pela resposta e o campo volta vazio ao modo de envio.
   - **Cancelar, trocar de conversa ou abrir uma conversa somente leitura** encerram a edição sem chamar o backend.
   - **Erros:**
     - 400 com texto válido: “Não foi possível editar. O prazo de 15 minutos terminou.”;
     - 404: “Não foi possível editar esta mensagem.”, e o campo volta ao modo de envio;
     - 429 e tamanho: os mesmos textos do envio.
6. **Lápis no hover e no toque.**
   - A linha da bolha ganha a classe `chat-bubble-row`, e o lápis, um `rx.icon_button` com `aria_label="Editar mensagem"`, ganha a classe `chat-edit-btn`.
   - Um CSS novo, `assets/chat.css`, registrado em `stylesheets`, controla a visibilidade:
     - por padrão, o lápis fica com `opacity: 0; pointer-events: none`;
     - em `@media (hover: hover)`, `.chat-bubble-row:hover .chat-edit-btn` o mostra;
     - `.chat-edit-btn:focus-visible` o mostra, para quem usa teclado;
     - `.chat-bubble-row[data-selected="true"] .chat-edit-btn` também o mostra.
   - **Toque no celular:** tocar na bolha alterna `selected_message_id` no estado, que vai para `data-selected` e mostra o lápis daquela mensagem.
   - **O lápis só existe nas mensagens com `editable`.**
   - **`prefers-reduced-motion`:** o CSS não tem transição; se algum dia tiver, desliga com essa preferência.

## Riscos / Trade-offs

- **Privacidade da leitura (decisão aprovada pelo Higor):** quem envia passa a saber até onde a outra pessoa leu. Só o id da última lida é revelado, sem horário, e só dentro da conversa.
- **Consulta das editadas:** 1 consulta a mais no banco a cada consulta automática, limitada a 100 mensagens. Como só se edita até 15 minutos depois do envio, o resultado quase sempre vem vazio.
- **Aba oculta por muito tempo:** o `edited_since` antigo traz todas as edições desde então, ainda limitadas pelo prazo de 15 minutos e por 100 itens. Quem reabre a conversa recebe o texto atual de tudo.
- **Edições da mesma mensagem em duas abas:** a última gravação vence.
- **Lápis um pouco atrasado:** `editable` é recalculado a cada resposta da consulta automática (15 s) e na abertura. Perto do fim do prazo, o lápis pode aparecer alguns segundos a mais; o backend recusa com 400 e a tela esconde o lápis.
- **“Visto” lido pela pessoa errada:** a dona com várias pessoas interessadas vê o ✓✓ de cada conversa separadamente, pelo campo daquela conversa.

## Dúvidas em aberto

1. **Doação concluída na edição:** 404 genérico, como no envio (proposto), ou 400?
2. **Limite de edições:** não há limite próprio (proposto), confiando no prazo de 15 minutos e no limite da plataforma. A alternativa é contar edições, o que exigiria guardar cada uma.
3. **Onde se edita:** no campo de baixo (proposto, mais simples) ou dentro da própria bolha?
4. **Posição do “visto”:** na linha do horário, fora da bolha (proposto), ou dentro da bolha, como no WhatsApp?
5. **Texto igual:** não grava, não marca “(editada)” e não gera log (proposto).
