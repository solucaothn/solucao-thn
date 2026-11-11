# Proposta

## Por quê

Quem envia uma mensagem no chat não sabe se a outra pessoa já leu e não consegue corrigir um erro de digitação. Os aplicativos de mensagem resolvem os dois casos com o “visto” (✓ e ✓✓) e com a edição por pouco tempo depois do envio. O backend já guarda até onde cada participante leu (`chat-nao-lidas`), então o “visto” não precisa de dado novo.

## O que muda

### Decisão aprovada pelo Higor: o chat passa a mostrar o “visto”

A regra atual de `donation-chat` diz que nenhuma resposta revela até onde a outra pessoa leu (cenário “Sem confirmação de leitura para a outra pessoa”). **Esta change revoga essa regra**, por decisão do Higor: a leitura de mensagens passa a informar até qual mensagem a **outra** pessoa leu, só para mostrar o “visto” nas mensagens de quem consulta.

### Backend (Xano)

- **“Visto”:** o `GET messages` passa a devolver `other_last_read_message_id`, o id da última mensagem que a outra pessoa leu. O dado já existe em `chat_conversation`.
- **Edição:**
  - endpoint novo `PATCH catalog/chat/messages` (`message_id`, `message_text`);
  - só quem enviou pode editar, até 15 minutos depois do envio, com a doação disponível ou reservada, com 1 a 1000 caracteres;
  - mensagem de outra pessoa, inexistente ou de doação concluída recebe o 404 genérico; fora do prazo ou com texto inválido, 400;
  - o log registra `chat_message_edited` só com `user_id` e a ação.
- **`chat_message` ganha `edited_at`** (timestamp, vazio até a primeira edição). As mensagens passam a trazer `edited_at` na leitura, no envio e na edição.
- **A edição chega à outra pessoa sem requisição a mais:**
  - a atualização automática que já existe (`after_message_id`, a cada 15 s) passa a mandar também `edited_since`;
  - a resposta traz, em `edited_messages`, as mensagens já exibidas que foram editadas desde então, e `server_time`, o horário do servidor para a próxima consulta.

### Frontend (Reflex)

- **“Visto” nas próprias mensagens:**
  - embaixo da bolha, junto do horário, ✓ cinza quando enviada e ✓✓ verde quando a outra pessoa leu;
  - o ✓✓ se atualiza junto com a atualização automática que já existe;
  - nas mensagens da outra pessoa não aparece nada.
- **Edição:**
  - no computador, um lápis aparece ao passar o mouse sobre a bolha; no celular, ao tocar na bolha;
  - o lápis só aparece nas próprias mensagens dentro dos 15 minutos e fora de conversa somente leitura;
  - ao editar, o texto vai para o campo de baixo e aparece “Editando mensagem”, com “Salvar” e “Cancelar”;
  - a mensagem editada mostra “(editada)” ao lado do horário.
- **Para a outra pessoa:** a edição aparece na atualização automática seguinte, em até cerca de 15 s com a conversa aberta.

## Ordem do apply

Duas partes, como na `chat-nao-lidas`.

- **Parte A, Xano:**
  - pull com confirmação e edição dos arquivos;
  - validação no Xano Developer MCP e dry-run;
  - conferência manual de `edited_at` no painel, porque o dry-run não mostra mudança de schema em tabela existente;
  - push feito pelo Higor e teste real no `scripts/teste_chat_real.py`.
- **Parte B, frontend e testes:** só depois do push, sem tocar em `xano/`.

## Fora do escopo

- Apagar mensagens, histórico de versões e editar mensagens da outra pessoa.
- “Visto” com horário, “digitando…”, “Online” e notificações.
- “Visto” na lista de conversas e na home.
- Atualização em tempo real: tudo continua vindo das consultas automáticas que já existem.

## Capacidades

### Novas capacidades

Nenhuma.

### Capacidades modificadas

- `donation-chat`:
  - “Leitura autorizada e paginada” passa a devolver o “visto”, `edited_at`, `edited_messages` e `server_time`; o cenário “Sem confirmação de leitura para a outra pessoa” é substituído;
  - “Envio de mensagens em texto simples” passa a devolver `edited_at`;
  - “Registro de eventos sem dados pessoais” ganha `chat_message_edited`;
  - requisito novo: “Edição das próprias mensagens”.
- `donation-chat-interface`:
  - requisitos novos “Confirmação de leitura nas próprias mensagens” e “Edição de mensagem”;
  - “Atualização automática limitada” passa a trazer o “visto” e as edições na mesma consulta.

## Impacto

- **Xano:**
  - tabela `xano/table/chat_message.xs` (campo `edited_at`);
  - `messages_GET.xs` e `messages_POST.xs`;
  - endpoint novo `xano/api/catalog/catalog/chat/messages_PATCH.xs`.
- **Código:** `doafacil/chat.py` (cliente, estado e página) e um CSS novo, `assets/chat.css`, registrado em `stylesheets` no `doafacil/doafacil.py`.
- **Testes:** `tests/test_chat.py` e `scripts/teste_chat_real.py`.
- **Documentação:** seção do chat em `docs/guia-do-colaborador.md` e seção “Chat” em `docs/design/README.md`.
- **Carga no Xano:**
  - o “visto” e a chegada das edições não custam nenhuma requisição a mais;
  - cada edição salva custa 1 requisição, como um envio.
