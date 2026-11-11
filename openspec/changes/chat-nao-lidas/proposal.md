# Proposta

## Por quê

O chat já funciona, mas quem abre `/chat` ou a home não sabe se chegou mensagem nova sem abrir cada conversa. Quem doa, que pode ter várias pessoas interessadas, precisa ver de longe onde há mensagens esperando resposta, como nos aplicativos de mensagem.

## O que muda

### Backend (Xano)

- `chat_conversation` ganha dois campos inteiros, `donor_last_read_message_id` e `interested_last_read_message_id` (padrão 0): até qual mensagem cada participante leu.
- O `GET messages` passa a marcar a conversa como lida para quem lê, avançando o campo dessa pessoa até a mensagem mais nova devolvida. Não há requisição extra: a tela já faz essa leitura ao abrir a conversa e na atualização automática.
- O `GET conversations` devolve `unread_count` em cada item: mensagens **da outra pessoa** posteriores à última lida.
- Novo endpoint leve `GET catalog/chat/unread_total` devolve só o total de não lidas da pessoa, para o cabeçalho da home.
- Nenhuma resposta revela até onde a **outra** pessoa leu (não há “visto”).

### Frontend (Reflex)

- **Lista de `/chat`:** cada conversa com mensagens não lidas mostra um círculo verde com o número; acima de 99 aparece “99+”. Zero não mostra nada. A conversa aberta não mostra contador.
- **Lista atualizada sozinha:** no máximo a cada 30 s, só com a aba visível, compartilhando a pausa de 60 s após um 429.
- **Cabeçalho da home:** o link “Mensagens” mostra o total de não lidas, consultado uma vez ao carregar a home, só com login.

## Ordem do apply

Duas partes, como na `chat-frontend`. **Parte A, Xano:** pull com confirmação, edição, validação no Xano Developer MCP, dry-run, **conferência manual dos campos novos no painel** (o dry-run não mostra mudança de schema em tabela existente), push feito pelo Higor e teste real. **Parte B, frontend e testes:** só depois do push, sem tocar em `xano/`.

## Fora do escopo

- Confirmação de leitura para a outra pessoa (“visto”, dois tiques), notificações, som, contador na aba do navegador.
- Contador em outras páginas além da home e de `/chat`; atualização automática do total na home.
- Recalcular a leitura das conversas antigas: depois da publicação, as mensagens já existentes da outra pessoa contam como não lidas até a conversa ser aberta (veja as dúvidas no `design.md`).

## Capacidades

### Novas capacidades

Nenhuma.

### Capacidades modificadas

- `donation-chat`: “Leitura autorizada e paginada” passa a marcar a conversa como lida; “Listagem das conversas da pessoa” passa a devolver `unread_count`; requisito novo “Total de mensagens não lidas”.
- `donation-chat-interface`: “Lista de conversas” ganha o contador; “Atualização automática limitada” passa a incluir a lista a cada 30 s; “Entrada no chat pelo cabeçalho da home” ganha o total.

## Impacto

- **Xano:** `xano/table/chat_conversation.xs` (dois campos novos), `messages_GET.xs`, `conversations_GET.xs` e o endpoint novo `xano/api/catalog/catalog/chat/unread_total_GET.xs`.
- **Código:** `doafacil/chat.py` (cliente, estado e página) e `doafacil/doafacil.py` (carregar o total na home e mostrar no link).
- **Testes:** `tests/test_chat.py`, testes do cabeçalho da home e `scripts/teste_chat_real.py`.
- **Documentação:** seção do chat em `docs/guia-do-colaborador.md` e seção “Chat” em `docs/design/README.md`.
- **Carga no Xano:**
  - **`/chat` com uma conversa aberta:** cerca de 6 requisições por minuto por aba (4 das mensagens e 2 da lista).
  - **`/chat` sem conversa aberta:** cerca de 2 por minuto.
  - **Home:** 1 a mais ao carregar, só com login.
  - **Marcar como lida:** nenhuma a mais.
