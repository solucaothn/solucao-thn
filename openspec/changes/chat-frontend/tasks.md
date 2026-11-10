# Tarefas

O apply vem em duas partes. **Parte A (grupos 1 a 3):** Xano. **Parte B (grupos 4 a 8):** frontend e testes, sem tocar em `xano/`, iniciada só depois do push da parte A.

## 1. Parte A: preparar o workspace do Xano

- [ ] 1.1 (manual) Mostrar `git status --short --branch` e pedir a confirmação explícita do Higor antes de `xano workspace pull -d ./xano`. Depois do pull, mostrar `git status` e `git diff --stat` em `xano/`, preservando as alterações preexistentes e ignorando as diferenças só de LF/CRLF (guia, seção 10.1). Verificação: os quatro arquivos do chat estão iguais ao que foi publicado na change `chat-backend`.

## 2. Parte A: endpoints do chat

- [ ] 2.1 Consultar no Xano Developer MCP a sintaxe da inversão de lista e do `find` antes de escrever. Registrar a forma escolhida no `design.md` (decisão A4). Verificação: a decisão A4 aponta a construção validada.
- [ ] 2.2 Em `start_POST.xs`, pedir `title` no `db.get donation` e devolver `donation_title` e `donation_status`. Verificação: o arquivo passa na validação do MCP e o GUID não mudou.
- [ ] 2.3 Em `conversations_GET.xs`, buscar título e status com **uma** consulta `donation ... in`, protegida por `|count > 0`, e incluir `donation_title` e `donation_status` em cada item. Verificação: o arquivo passa na validação do MCP e o GUID não mudou.
- [ ] 2.4 Em `messages_GET.xs`:
  - acrescentar `int before_message_id?`, sem filtro, e a `precondition` 400 para os dois cursores juntos;
  - implementar os modos “últimas N” e `before_message_id` (ordem decrescente, invertida para crescente na resposta) e `after_message_id`;
  - devolver `has_older`, `has_newer`, `donation_title`, `donation_status` e `sent_by_me` em cada mensagem, sem `sender_id`.

  Verificação: o arquivo passa na validação do MCP e o GUID não mudou.
- [ ] 2.5 Em `messages_POST.xs`, acrescentar `sent_by_me: true` à resposta, mantendo a validação 400 antes do limite 429. Verificação: o arquivo passa na validação do MCP e o GUID não mudou.
- [ ] 2.6 (manual) Rodar `xano workspace push -d ./xano --dry-run` e revisar a saída inteira. Verificação: aparecem somente os quatro endpoints do chat; qualquer outro objeto interrompe a publicação.
- [ ] 2.7 (manual) O Higor faz o push real (`xano workspace push -d ./xano`) e avisa o grupo da mudança nos endpoints do chat. Verificação: o push conclui sem erros.

## 3. Parte A: teste real e documentação do backend

- [ ] 3.1 Atualizar `scripts/teste_chat_real.py` com os cenários da decisão A7, mantendo os existentes, as pausas e a regra de não imprimir tokens, e-mails nem corpos. Verificação: `python -m py_compile scripts/teste_chat_real.py` passa.
- [ ] 3.2 (manual) Rodar o script contra o Xano real. Verificação: todos os cenários OK, inclusive os novos.
- [ ] 3.3 Atualizar a seção “Chat da doação (backend)” de `docs/guia-do-colaborador.md` com os campos novos e os três modos do `GET messages`. Verificação: o texto bate com a spec delta `donation-chat`.

## 4. Parte B: cliente HTTP e estado do chat (`doafacil/chat.py`)

- [ ] 4.1 Criar as funções do cliente (`start_conversation`, `list_conversations`, `fetch_messages` com `before`/`after`, `send_message`) com `httpx.AsyncClient` injetado, URL a partir de `XANO_API_URL`, Bearer, validação estrita das respostas (descartar campos inesperados) e erros classificados para 400, 401, 404, 429 do chat e 429 da plataforma. Verificação: `tests/test_chat.py` cobre URLs, parâmetros, respostas válidas e malformadas e cada erro com `httpx.MockTransport`, incluindo os dois corpos de 429; a suíte passa.
- [ ] 4.2 Criar os auxiliares: inicial do avatar (“?” para nome vazio ou “Usuário”) e rótulo do dia (“Hoje”, “Ontem”, dd/mm/aaaa) com UTC−3 fixo. Verificação: testes com horários perto da meia-noite UTC.
- [ ] 4.3 Criar o `ChatState(LoginState)` com `load_chat`: sem token, `/login` sem chamadas; carrega a lista; abre `?conversa=` com uma consulta sem cursor; trata 401 limpando a sessão. Verificação: testes do estado com o cliente simulado.
- [ ] 4.4 Implementar `select_conversation`, `load_older_messages` (“Carregar anteriores”, com `before_message_id`, inserindo no topo sem duplicar e escondendo o botão sem `has_older`), `load_more_conversations` e `back_to_list`. Verificação: testes de cada handler.
- [ ] 4.5 Implementar `send_message`: aparar o texto, ignorar o vazio, `is_sending`, limpar no sucesso, os textos da decisão 6 e somente leitura após um 404. Verificação: testes para cada status, para o vazio sem chamada e para o texto mantido nas falhas.
- [ ] 4.6 Implementar `poll_tick` e `poll_if_visible`: sem chamada com a aba oculta, sem conversa aberta ou com a pausa ativa; `after_message_id` igual à última mensagem; sem duplicar; pausa de 60 s após qualquer 429. Verificação: testes de cada condição.

## 5. Parte B: página `/chat`

- [ ] 5.1 Montar a página: cabeçalho com logo, “Voltar ao início”, lista (avatar, primeiro nome, título), cabeçalho da conversa (nome e título), “Carregar anteriores”, bolhas por `sent_by_me`, separadores de dia, formulário com “Digite aqui...” e “Enviar”, aviso de somente leitura, estados vazios e de erro, layout responsivo e `page-fade-enter`. O `rx.moment` de 15 s fica dentro do `rx.cond` da conversa aberta. Registrar a rota em `doafacil/doafacil.py`. Verificação: os testes de componente confirmam os textos fixos, a classe de animação, o `rx.moment` condicionado, `max_length=1000` e a ausência de `rx.html`; a suíte passa.
- [ ] 5.2 Documentar a tela em `docs/design/README.md` (seção “Chat”): o que segue o Figma e as diferenças aprovadas (sem foto, sem “Online”, sem prévia, botão “Enviar”, cores com contraste AA, título da doação, “Carregar anteriores”, textos neutros). Verificação: o texto bate com a spec `donation-chat-interface`.

## 6. Parte B: botão “Chat” do detalhe

- [ ] 6.1 Substituir `show_chat_unavailable` por `start_chat` (decisão 11) e remover `CHAT_UNAVAILABLE_MESSAGE`. Verificação: ajustar `tests/test_donation_detail.py` (o teste atual espera a mensagem antiga) e cobrir sem login, 200 com redirecionamento, 404 com a mensagem neutra, 401 e erro de rede; a suíte passa.

## 7. Parte B: link “Mensagens” e guia

- [ ] 7.1 Acrescentar “Mensagens” (`href="/chat"`) ao ramo autenticado do cabeçalho da home, como ícone com `aria_label` no celular. Verificação: um teste confirma o link só no ramo autenticado; a suíte passa.
- [ ] 7.2 Atualizar `docs/guia-do-colaborador.md`: tirar “Interface do chat” de “O que ainda falta”, registrar a tela em “O que já está pronto” e explicar a atualização automática (15 s, aba visível, pausa de 60 s após um 429) e os dois textos de 429. Verificação: o texto bate com o `design.md`.

## 8. Verificação final

- [ ] 8.1 Rodar `python -m unittest discover -s tests -v` e mostrar `git status` e `git diff --stat`. Verificação: todos os testes passam e, na parte B, nada muda em `xano/`.
- [ ] 8.2 (manual) No navegador, com duas contas:
  - iniciar a conversa pelo “Chat” do detalhe;
  - enviar com o botão e com Enter;
  - ver a mensagem chegar na outra aba em até cerca de 15 s;
  - confirmar no DevTools que não há consultas com a aba oculta;
  - usar “Carregar anteriores” numa conversa com mais de 50 mensagens;
  - ver o HTML aparecer literal;
  - ver o 429 do chat com o texto próprio;
  - ver o somente leitura numa doação concluída;
  - ver a mensagem neutra quando a dona clica em “Chat”;
  - testar em 360 px, com `prefers-reduced-motion` e pelo link “Mensagens” da home.

  Verificação: todos os itens do roteiro conferidos e anotados.
