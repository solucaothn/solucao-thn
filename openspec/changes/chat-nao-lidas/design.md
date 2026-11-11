# Design

## Contexto

- **`chat_conversation` hoje:** `id`, `created_at`, `donation_id`, `donor_id`, `interested_user_id` e `last_message_at`, com índice único em (`donation_id`, `interested_user_id`) e índices por participante e `last_message_at`. Nada sobre leitura.
- **`messages_GET`:** busca a conversa (com `donor_id` e `interested_user_id`), confere o participante e devolve as mensagens em ordem crescente nos três modos (sem cursor, `before_message_id` e `after_message_id`). Padrões já validados no Xano:
  - duas consultas separadas, sem `$input` nulo no `where`;
  - `foreach` com `|unshift` e `|push`;
  - `var.update` dentro de `conditional`.
- **`conversations_GET`:** já percorre os itens da página num `foreach` e faz consultas `in` protegidas por `|count > 0`.
- **Frontend:**
  - `ChatState(LoginState)` em `doafacil/chat.py`, com `_conversation_item`, `poll_tick` e `poll_if_visible` (15 s, aba visível) e a pausa `poll_paused_until` de 60 s após um 429;
  - a home chama `HomeState.load_home_data` (2 requisições) e `LoginState.load_account` (1) no `on_load`;
  - o link “Mensagens” fica no ramo autenticado do cabeçalho.
- **Limite da plataforma:** 10 requisições por 20 s para a instância inteira.
- **Dry-run do Xano:** não mostra mudança de schema em tabela existente.

## Objetivos / Fora do escopo

**Objetivos:** contador exato por conversa e total para a home, com o menor número de requisições HTTP possível e sem revelar à outra pessoa até onde se leu.

**Fora do escopo:** “visto” ou dois tiques, notificações, total atualizado sozinho na home, recálculo das conversas antigas.

## Decisões: backend (parte A)

**A1. Guardar “até onde li” em `chat_conversation`.** Dois campos inteiros com padrão 0: `donor_last_read_message_id` e `interested_last_read_message_id`. Uma conversa tem exatamente dois participantes fixos, então dois campos na própria linha bastam, sem tabela nem `join` extra.
- *Alternativa descartada: contadores* (`donor_unread_count` somado a cada envio e zerado na leitura). As leituras seriam mais baratas, mas o Xano não garante soma atômica: dois envios ao mesmo tempo podem perder uma unidade, e o número fica errado até a próxima leitura.
- *Alternativa descartada: tabela `chat_read`* (conversa, usuário, última lida). É mais flexível para grupos, que não existem aqui, e custa uma consulta a mais em cada leitura.

**A2. Marcar como lida dentro do `messages_GET`.**
- Passos:
  - o `db.get chat_conversation` passa a pedir também os dois campos novos;
  - depois de montar `$messages` (em qualquer modo), se houver mensagens, pega `($messages|last).id`;
  - se a pessoa autenticada é `donor_id` e esse id é maior que `donor_last_read_message_id`, faz `db.edit chat_conversation` só desse campo; o mesmo vale para `interested_user_id` e o outro campo.
- **Nunca volta atrás:** só grava se o id novo for maior que o atual. Carregar anteriores ou uma consulta sem mensagens novas não escreve nada.
- **Sem requisição HTTP a mais:** a tela já chama esse endpoint ao abrir a conversa e na atualização automática.
- **Sem evento de log:** a gravação de leitura não chama `log_event`.
- *Alternativa descartada: endpoint `POST mark_read`*, que custaria 1 requisição a mais a cada abertura e a cada mensagem nova.
- **Risco aceito:** um `GET` com efeito colateral. Ele só avança a leitura, então repetir a chamada não muda o resultado.

**A3. `unread_count` no `conversations_GET`.**
- A consulta da página passa a pedir os dois campos novos.
- No `foreach` que monta os itens, `my_last_read` é o campo de quem consulta.
- Para cada item, uma consulta `count` em `chat_message` com `conversation_id == item`, `sender_id != $auth.id` e `id > my_last_read`, em consulta única com condições simples, sem `$input` nulo.
- Custo: até 50 contagens no banco por requisição, mas **nenhuma requisição HTTP a mais**.

**A4. Endpoint novo `GET catalog/chat/unread_total`** (`auth = "user"`, sem inputs).
- Consulta as conversas da pessoa (`donor_id == $auth.id || interested_user_id == $auth.id`, sem paginação), com `output` de `id`, `donor_id` e os dois campos de leitura.
- Para cada conversa, faz a mesma contagem da A3 e soma.
- Responde só `{unread_total: <int>}`.
- *Alternativa descartada:* pôr o total no `auth/me`. É um endpoint compartilhado do grupo Authentication, fora do chat.
- *Alternativa descartada:* a home chamar o `GET conversations` e somar. A resposta é mais pesada e o total sai errado acima de 50 conversas.

**A5. Sintaxe e GUID.**
- Confirmar no Xano Developer MCP a declaração de campo inteiro com padrão em tabela (por exemplo `int donor_last_read_message_id?=0`, no mesmo estilo de `timestamp created_at?=now`) e o `db.edit` de um campo só.
- O endpoint novo não tem GUID antes do primeiro push. Depois do push, um pull traz o GUID, que vai num commit próprio, como foi feito na `chat-backend`.

**A6. Conferência manual do schema.** O dry-run não mostra mudança de schema em tabela existente. Depois do push, conferir no painel do Xano que `chat_conversation` tem os dois campos, do tipo inteiro e com padrão 0, e que as linhas existentes ficaram com 0.

**A7. Teste real.** `scripts/teste_chat_real.py` ganha cenários para:
- `unread_count` e `unread_total` da dona depois de a interessada enviar;
- zerar ao ler;
- mensagens próprias que não contam;
- carregar anteriores sem voltar a leitura;
- o 401 do total.

## Decisões: frontend (parte B)

1. **Cliente e parsing.** `unread_count` passa a ser campo obrigatório do item da lista (inteiro ≥ 0). Função nova `fetch_unread_total(client, token)` com a mesma classificação de erros.
2. **Formato do número.** Função pura `format_unread(n)`: 0 vira "" (sem contador), 1 a 99 viram o número, acima de 99 vira "99+". Rótulo acessível: “1 mensagem não lida” ou “N mensagens não lidas”.
3. **Contador na lista.** Círculo `#007A42` com texto branco, que tem contraste AA, à direita do item. O `#00A859` do avatar não atinge 4,5:1 com texto branco em fonte pequena. Ao abrir uma conversa, o estado zera o `unread_count` dela na hora; ao receber a lista, força 0 na conversa aberta.
4. **Lista a cada 30 s.**
   - Um segundo `rx.moment` (`interval=30000`) fica sempre montado em `/chat`, com `on_change=ChatState.list_poll_tick`.
   - O tick faz a mesma checagem de `document.visibilityState` e de `poll_paused_until` que as mensagens; um 429 em qualquer das duas consultas pausa as duas por 60 s.
   - Ao receber a página 1, os itens dela entram no topo, na ordem nova, e as conversas já carregadas de páginas seguintes ficam abaixo, sem repetir.
   - O total de requisições por minuto está no Impacto da proposta.
5. **Total na home.**
   - `ChatState.unread_total: int` e `ChatState.load_unread_total`, acrescentado ao `on_load` da home depois de `LoginState.load_account`.
   - Sem token, não chama nada. Qualquer erro, inclusive 401 (o `load_account` já trata o token recusado), deixa o total em 0, sem aviso.
   - O `on_load` também roda ao voltar para a home por navegação dentro do site, então o total se renova ao sair de `/chat` e voltar.
6. **Contador no link “Mensagens”.** Mesmo círculo da lista, ao lado do ícone, também no celular. Rótulo acessível no link: “Mensagens, N não lidas”.

## Riscos / Trade-offs

- **Conversas antigas.** Os campos novos começam em 0, então depois do push todas as mensagens já existentes da outra pessoa contam como não lidas, até a conversa ser aberta. No ambiente acadêmico só há dados de teste; recalcular a leitura das conversas antigas exigiria uma rotina à parte no Xano (veja as dúvidas).
- **Custo do total.** O `unread_total` faz uma contagem por conversa da pessoa. Com dezenas de conversas, isso é aceitável; com centenas, valeria trocar por contadores ou por uma consulta agregada.
- **Duas abas.** Duas abas da mesma pessoa lendo ao mesmo tempo podem gravar uma leitura um pouco mais antiga por cima da outra, porque a escrita lê antes de gravar. Algumas mensagens voltariam a contar como não lidas até a próxima leitura. É raro e se corrige sozinho.
- **Leitura que escreve.** Cada abertura de conversa com mensagem nova grava uma linha. Consultas sem mensagens novas não gravam nada.
