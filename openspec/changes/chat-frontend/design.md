# Design

## Contexto

- **Backend publicado** (spec `donation-chat`), grupo Catalog, todos com Bearer:
  - `POST catalog/chat/conversations/start` (`donation_id`) → `conversation_id`, `donation_id`, `last_message_at`, `other_user_first_name`.
  - `GET catalog/chat/conversations` (`page`, `limit` opcionais; padrão 20, máximo 50) → `conversations[]`, `has_more`, `next_page`.
  - `GET catalog/chat/messages` (`conversation_id`, `after_message_id`, `limit`) → mensagens em ordem crescente **a partir da mais antiga**, `has_more`, `next_after_message_id`.
  - `POST catalog/chat/messages` → a mensagem criada. Erros: 400 (tamanho), 404 genérico (inclui doação concluída) e 429 com a mensagem “Limite de mensagens atingido…”.
- **O que falta para a tela:**
  - título e status da doação;
  - indicação de autoria das mensagens (hoje só vem `sender_first_name`, que pode coincidir entre as duas pessoas);
  - leitura que comece pelas mensagens recentes.
- **Lições anteriores no Xano:**
  - inputs opcionais `int x?` não podem ter `filters=min:1` (deram 400 quando omitidos); a validação fica na `precondition`;
  - consultas com `in` sobre uma lista são protegidas por `|count > 0`;
  - a plataforma limita a instância inteira a 10 requisições por 20 s e responde 429 com `ERROR_CODE_TOO_MANY_REQUESTS` e mensagem própria.
- **Frontend atual:**
  - o botão “Chat” do detalhe chama `show_chat_unavailable`;
  - a resposta pública do detalhe não contém `owner_id`, e a spec `donation-detail` proíbe o frontend de recebê-lo ou guardá-lo;
  - só a home tem cabeçalho logado;
  - os estados com sessão herdam de `LoginState`;
  - os clientes HTTP usam `httpx.AsyncClient`, testado com `MockTransport`.
- **Ambiente:**
  - `zoneinfo` não encontra `America/Sao_Paulo` no Windows sem `tzdata`;
  - `rx.moment` aceita `interval` e `on_change`.
- **Figma** (frame `chat-1`): lista com avatar, nome e prévia; cabeçalho “Nome - Online ●”; separador “Hoje”; bolhas com texto branco sobre cinza-claro e sobre verde-claro; campo “Digite aqui...” sem botão. Os textos do mockup não são usados.

## Objetivos / Fora do escopo

**Objetivos:**
- endpoints do chat com título, status, autoria e leitura pelas mensagens recentes;
- página `/chat` segura e leve para o Xano;
- botão “Chat” do detalhe ligado ao início da conversa;
- um caminho para quem doa chegar às conversas.

**Fora do escopo:**
- tabelas e endpoints fora do chat;
- tempo real e notificações;
- não lidas;
- prévia da última mensagem;
- foto e status “Online”;
- cabeçalho logado fora da home.

## Decisões: backend (parte A)

**A1. Contrato novo.**

| Endpoint | Muda |
|---|---|
| `POST conversations/start` | + `donation_title`, `donation_status` |
| `GET conversations` (cada item) | + `donation_title`, `donation_status` |
| `GET messages` | entrada + `before_message_id?`; resposta: `messages[]` (cada uma + `sent_by_me`), `donation_title`, `donation_status`, `has_older`, `has_newer`; saem `has_more` e `next_after_message_id` |
| `POST messages` | + `sent_by_me: true` |

O status volta exatamente como na tabela (`disponível`, `reservada`, `concluída`). O título é o mesmo já público no detalhe.

**A2. `start_POST`.** O `db.get donation` do início passa a pedir também `title`. A resposta usa `$donation.title` e `$donation.status`, lidos na mesma chamada que já existe, sem consulta extra.

**A3. `conversations_GET`.** Seguindo o padrão já usado para os nomes:
- juntar os `donation_id` da página;
- fazer **uma** consulta `donation` com `id in $donation_ids`, protegida por `|count > 0`, com `output = ["id", "title", "status"]`;
- associar cada doação ao seu item com `find`;
- se a doação não for encontrada, usar `donation_title` “Doação” e `donation_status` vazio. Isso não deve acontecer, porque o `DELETE` apaga as conversas junto.

**A4. `messages_GET`, três modos.**
- Novo input `int before_message_id?`, sem filtro. Uma `precondition` responde 400 se os dois cursores vierem juntos.
- **Sem cursor ou com `before_message_id`:**
  - consulta com `sort id desc` e `per_page = limite`, filtrando `id < before_message_id` quando ele existe;
  - em seguida, inverter a lista para a ordem crescente;
  - `has_older` = existe mensagem com `id` menor que o menor retornado (consulta de contagem);
  - `has_newer = false`.
- **Com `after_message_id`:** como hoje: `id > after`, `sort id asc`, `has_newer` = contagem restante maior que o limite, `has_older = false`.
- `sent_by_me` = `$message.sender_id == $auth.id`, calculado no laço que já monta `sender_first_name`. O `sender_id` não vai na resposta.
- O `db.get donation` passa a pedir `title` e `status` para a resposta.
- **Sintaxe confirmada no Xano Developer MCP** (documentação `syntax/array-filters`, versão 2.7.1). A associação por chave usa `|find:$$.campo == valor`, a mesma forma já publicada em `conversations_GET` para os nomes.
- **Inversão revisada após o teste real.** A primeira versão invertia a lista com `$recent_messages|reverse`, e o teste real (3.2) recebeu 200 com 0 mensagens nos modos sem cursor e `before_message_id`, com título e status corretos. A causa mais provável é o `|reverse` aplicado ao resultado do `db.query`; era o único elemento novo nesse caminho. A versão atual monta a lista crescente com `foreach ($recent_messages)` e `var.update $messages { value = $messages|unshift:$recent_message }`, o mesmo padrão de `foreach` + `|push` já publicado no projeto. Além disso, o ramo decrescente foi dividido num `conditional`: sem `before_message_id`, o `where` filtra só por `conversation_id`; com ele, por `conversation_id && id < before_message_id`. Assim nenhum `where` compara um `$input` que possa ser nulo. A versão antiga (`9b94baa`) usava `$input.after_message_id == null || ...` no `where` e funcionava, mas a separação elimina essa suspeita sem custo.
- **Diagnóstico confirmado.** O histórico do Xano mostrou que, na versão com `|reverse` e `where` combinado, o `foreach` seguinte rodava 0 vezes. Campos de depuração temporários mostraram que a versão atual (duas consultas separadas e `foreach` + `|unshift`) devolve `debug_query_count = 2`, `debug_messages_count = 2` e 2 mensagens, sem `limit` e com `limit=100`. **Causa provável:** o `|reverse` aplicado ao resultado do `db.query` não produzia uma lista utilizável, e/ou o `where` combinado com `$input.before_message_id == null || ...` no ramo decrescente voltava vazio. As duas correções entraram juntas, então não dá para atribuir a falha a uma só. A forma atual evita as duas construções.

**A5. `messages_POST`.** A resposta ganha `sent_by_me: true`. Nada mais muda: a validação 400 continua antes do limite 429.

**A6. GUIDs e escopo.** Todos os GUIDs ficam como estão. O dry-run só pode mostrar esses quatro arquivos. Os arquivos `xano/` já modificados por quebra de linha **não entram**: o pull e a revisão seguem a seção 10.1 do guia.

**A7. Teste real.** `scripts/teste_chat_real.py` ganha cenários para:
- os campos novos nos quatro endpoints;
- `sent_by_me` verdadeiro e falso;
- últimas N (`limit=2` devolve as 2 últimas em ordem crescente);
- `before_message_id` devolvendo a página anterior com `has_older` correto;
- `after_message_id` devolvendo só as novas;
- os dois cursores juntos → 400.

As pausas para o limite da plataforma continuam.

## Decisões: frontend (parte B)

1. **Módulo novo `doafacil/chat.py`.** Reúne o cliente HTTP (funções com `httpx.AsyncClient` injetado), o `ChatState(LoginState)` e a página. A rota `/chat` é registrada em `doafacil.py` com `on_load=ChatState.load_chat`.
2. **Abrir uma conversa pelo endereço.** `/chat?conversa=<id>`, lido de `router.page.params`. Um ID inválido ou um 404 viram “Conversa não encontrada.”, com a lista mantida.
3. **Histórico sob demanda.** Abrir uma conversa faz **uma** consulta sem cursor (`limit=50`). “Carregar anteriores” aparece se `has_older` e consulta com `before_message_id` igual à mais antiga exibida, inserindo o resultado no topo. Não há teto nem leitura de todas as páginas.
4. **Atualização automática com `rx.moment`.**
   - O componente fica dentro de `rx.cond(conversa aberta)`, com `interval=15000` e `on_change=ChatState.poll_tick`.
   - O `poll_tick` consulta a visibilidade com `rx.call_script("document.visibilityState", callback=ChatState.poll_if_visible)`; só com a aba visível chama `GET messages` com `after_message_id` igual à última mensagem e acrescenta as novas sem duplicar.
   - Qualquer 429 nessa consulta grava `poll_paused_until` de agora + 60 s, sem aviso bloqueante.
   - A lista de conversas não é atualizada automaticamente; só ao abrir a página ou ao clicar em “Atualizar”.
5. **Envio com `rx.form`.**
   - Campo `rx.input` (`max_length=1000`, placeholder “Digite aqui...”) e botão “Enviar” (`type="submit"`): Enter envia nativamente.
   - O texto é aparado; se ficar vazio, nada é enviado.
   - Um `is_sending` evita o envio duplo.
   - O campo só é limpo após o sucesso.
6. **Mensagens de erro.**

   | Situação | Texto |
   |---|---|
   | 400 | “A mensagem precisa ter entre 1 e 1000 caracteres.” |
   | 404 no envio | “Não foi possível enviar. Esta conversa não está mais disponível para novas mensagens.” (e a conversa passa a somente leitura) |
   | 429 do chat (`message` contém “Limite de mensagens atingido”) | “Você enviou muitas mensagens em pouco tempo. Aguarde um minuto.” |
   | 429 da plataforma (`code` `ERROR_CODE_TOO_MANY_REQUESTS` com outra mensagem, ou corpo não reconhecido) | “O site está com muitos acessos agora. Tente de novo em instantes.” |

   A classificação do 429 fica numa função pura, testada com os dois corpos reais.
7. **Texto literal.** Mensagens, nomes e títulos são renderizados com `rx.text`. É proibido usar `rx.html`, `dangerouslySetInnerHTML` ou markdown. Um teste confere que a página não usa `rx.html`.
8. **Somente leitura.** Vem de `donation_status == "concluída"`, ou de um 404 no envio: campo e botão desativados e o aviso da spec. Doação reservada continua enviando.
9. **Identidade visual.**
   - **Avatar:** círculo `#00A859`, 36 px, com a inicial em branco; nome vazio ou “Usuário” usa “?”.
   - **Bolhas da própria pessoa** (`sent_by_me`): à direita, em `#007A42`, com texto branco.
   - **Bolhas da outra pessoa:** à esquerda, em `#E9ECEF`, com texto `#1F1F1F`.
   - **Cores do Figma:** o texto branco sobre cinza-claro e sobre verde-claro do Figma não atinge o contraste AA. A diferença fica registrada no README de design.
   - **Separadores de dia:** com fuso fixo UTC−3. O Brasil não tem horário de verão desde 2019, e isso evita a dependência `tzdata`.
   - **Fundo e layout:** fundo creme na área de mensagens; cabeçalho branco com logo; seta “Voltar ao início” como no cadastro de doação.
10. **Layout responsivo.** Em `md` ou mais: lista de 280 px e conversa ao lado. Abaixo disso, o estado `mobile_view` mostra a lista ou a conversa, com “Voltar às conversas”.
11. **Botão “Chat” do detalhe.** O `DonationDetailState.start_chat` substitui `show_chat_unavailable`:
    - sem token, vai para `/login`;
    - em 200, `rx.redirect(f"/chat?conversa={id}")`;
    - em 404, “Não é possível conversar sobre esta doação pelo chat.”;
    - em 401, limpa a sessão e vai para `/login`;
    - nos demais casos, uma mensagem simples;
    - um `is_starting_chat` evita clique duplo.

    O detalhe **não sabe** quem é a dona: a resposta pública não traz `owner_id`, e a spec proíbe guardá-lo. Pela decisão do grupo, nesse caso o botão continua visível e a dona recebe a mensagem neutra.
12. **Link “Mensagens” no cabeçalho da home.** Fica no ramo autenticado, antes de “Olá, nome”, com o mesmo estilo verde e negrito do menu. No celular, aparece como ícone `message-circle` com `aria_label="Mensagens"`.
13. **Animação.** `page-fade-enter` no contêiner principal, que monta antes dos dados. O cabeçalho fica fora da animação, e as mensagens que chegam depois não ganham animação própria.
14. **Textos neutros.**
    - Lista vazia: “Você ainda não tem conversas.”
    - Nenhuma conversa aberta: “Escolha uma conversa para ver as mensagens.”
    - Conversa sem mensagens: “Ainda não há mensagens. Escreva a primeira.”
    - Erro de carga: “Não foi possível carregar as conversas. Tente novamente.”

## Pendência de debug (resolvida)

- O debug temporário do `messages_GET.xs` foi removido: as variáveis `$debug_query_count` e `$debug_messages_count`, os campos de mesmo nome na resposta e o comentário. A impressão desses números também saiu do modo rápido do `scripts/teste_chat_real.py`. **A remoção só vale no Xano depois do dry-run e do push.**

## Riscos / Trade-offs

- **Mudança de forma do `GET messages`.** `has_more` e `next_after_message_id` deixam de existir. O único consumidor é o script de teste real, atualizado na mesma parte.
- **Sintaxe XanoScript da inversão e do `find`.** Confirmada no MCP (decisão A4).
- **Arquivos `xano/` com quebra de linha alterada.** O pull pode trazer de novo diferenças só de LF/CRLF. O dry-run e o commit incluem só os quatro arquivos do chat.
- **Limite da plataforma.** Várias abas somam requisições. Os 15 s, a pausa de 60 s e a ausência de atualização da lista mantêm a carga baixa, sem garantia com muitos usuários.
- **Status visível aos participantes.** Aprovado pelo grupo: o status já é público no detalhe da doação. A resposta do envio continua sem revelá-lo.
- **`rx.moment` como timer.** O uso com `interval` precisa ser confirmado no navegador. Se falhar, a alternativa é um `rx.script` mínimo, o que exigiria revisar a decisão 4.
