# Proposta

## Por quê

O backend do chat já está publicado no Xano, mas ninguém consegue usá-lo: o botão “Chat” do detalhe da doação ainda mostra “O chat ainda não está disponível.” e não existe tela de mensagens. Para a tela ficar utilizável, os endpoints também precisam de dados que hoje não devolvem:
- o título e o status da doação;
- a indicação de quais mensagens são da própria pessoa;
- as mensagens mais recentes primeiro, já que hoje a leitura começa pela mais antiga.

## O que muda

### Backend (Xano, só os endpoints do chat)

- `start`, `conversations` e `messages` (GET) passam a devolver `donation_title` e `donation_status`. O status já é público no detalhe da doação e aqui só é mostrado a participantes.
- Cada mensagem do `GET messages` e a resposta do `POST messages` trazem `sent_by_me`, calculado a partir da sessão, sem expor identificadores de usuário.
- O `GET messages` passa a ter três modos, sempre em ordem cronológica na resposta:
  - sem cursor, devolve as **últimas N** mensagens;
  - com `before_message_id`, a página anterior;
  - com `after_message_id`, as mensagens novas, usadas pela atualização automática.
- `scripts/teste_chat_real.py` é atualizado para cobrir os novos campos e a paginação.

### Frontend (Reflex)

- **Página `/chat`, só para quem está logado** (sem sessão, vai para `/login`):
  - lista de conversas à esquerda, com o primeiro nome da outra pessoa, o título da doação e um círculo verde com a inicial;
  - mensagens à direita, com “Carregar anteriores”;
  - campo “Digite aqui...” com o botão “Enviar”; Enter também envia;
  - nas telas estreitas, a lista e a conversa aparecem uma de cada vez.
- **Botão “Chat” do detalhe:** inicia ou reabre a conversa e abre `/chat?conversa=<id>`. Se a doação não aceitar conversa, inclusive quando é da própria pessoa, mostra uma mensagem neutra. O detalhe não sabe quem é a dona.
- **Atualização automática:** só com uma conversa aberta e a aba visível, no mínimo a cada 15 s, pedindo só as mensagens novas. Não há tempo real.
- **Texto e erros:**
  - texto sempre literal, nunca HTML;
  - mensagens amigáveis para 400 e 404;
  - 429 com textos separados para o limite do chat e para o limite da plataforma;
  - doação concluída: campo desativado, com aviso de somente leitura.
- **Link “Mensagens” no cabeçalho logado da home.** O histórico do Git mostra que só o Higor mexeu nesse cabeçalho, a última vez em 28/10/2026.
- **Animação:** a página tem animação de entrada (`page-fade-enter`), e os textos de exemplo são neutros. As mensagens do mockup do Figma não são usadas.

## Ordem do apply

O apply vem em duas partes. A **parte A** é o Xano: pull com confirmação, edição, validação no Xano Developer MCP, dry-run revisado, push feito pelo Higor e teste real. A **parte B**, frontend e testes, só começa depois do push e não toca em `xano/`.

## Fora do escopo

- Tabelas, outros endpoints e o `DELETE` de doações. Só os quatro endpoints do chat mudam.
- Tempo real, notificações, não lidas, foto de perfil, status “Online”, prévia da última mensagem, apagar ou editar mensagens.
- Cabeçalho logado em outras páginas além da home.

## Capacidades

### Novas capacidades

- `donation-chat-interface`: a página de mensagens (acesso, lista, conversa, histórico sob demanda, envio, somente leitura, atualização automática e entrada pelo cabeçalho da home).

### Capacidades modificadas

- `donation-chat`: os requisitos “Elegibilidade para iniciar conversa”, “Envio de mensagens em texto simples”, “Leitura autorizada e paginada” e “Listagem das conversas da pessoa” passam a devolver título, status e autoria. A leitura ganha os modos “últimas N”, `before_message_id` e `after_message_id`.
- `donation-detail`: no requisito “Fluxo de contato do doador”, o botão “Chat” deixa de mostrar “O chat ainda não está disponível.” e passa a iniciar ou abrir a conversa.

## Impacto

- **Xano:** `xano/api/catalog/catalog/chat/conversations/start_POST.xs`, `conversations_GET.xs`, `messages_GET.xs` e `messages_POST.xs`. A resposta do `GET messages` muda de forma: saem `has_more` e `next_after_message_id` e entram `has_older` e `has_newer`. Nenhum frontend consome esse endpoint hoje; só o script de teste real, que é atualizado junto.
- **Código:**
  - novo módulo `doafacil/chat.py`;
  - `doafacil/detalhe_doacao.py` (botão “Chat”);
  - `doafacil/doafacil.py` (rota `/chat` e link “Mensagens”).
- **Testes:** novo `tests/test_chat.py`; ajustes em `tests/test_donation_detail.py` e nos testes do cabeçalho; `scripts/teste_chat_real.py`.
- **Documentação:** `docs/design/README.md` (seção do chat) e a seção do chat em `docs/guia-do-colaborador.md` (parâmetros novos e telas).
- **Carga no Xano:** cerca de 4 requisições por minuto por aba com conversa aberta, mais o envio; abrir uma conversa custa uma consulta.
- **Sem novas dependências.**
