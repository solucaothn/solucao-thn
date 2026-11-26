# Design

## Contexto

Veja proposal.md, seção “Por quê”. Três fatos do código explicam as falhas.

- **Busca do cabeçalho:** o `<form>` da busca, em `explore_header()` (`doafacil/explorar.py`), tem `flex="1"`, que o navegador lê como `flex: 1 1 0%`. Num contêiner flex, a base (`flex-basis`) vence a largura (`width`). Por isso o `width: 100%` do celular não tem efeito: a busca não desce para a própria linha e fica espremida ao lado do logotipo. Em 360 px, o formulário fica com 60 px, o campo com 0 px e a página rola 56 px para o lado.
- **Carregando que não aparece:** o Reflex só manda o estado ao navegador num `yield` ou no fim do evento. Os eventos abaixo ligam o carregando e já chamam o Xano, sem `yield` no meio. Quando a resposta chega, o carregando já foi desligado. A change `chat-carregamento` corrigiu o mesmo problema em `load_chat`, `select_conversation` e `start_chat`, com um `yield` logo depois de ligar o estado.
  - `LoginState`: `login`, `signup`, `request_recovery_code`, `resend_recovery_code`, `verify_recovery_code` e `confirm_recovery_password`;
  - `DonationCreateState`: `publish` e `load_initial_data`;
  - `ChatState`: `send_message` (envio e edição), `refresh_conversations`, `load_older_messages` e `load_more_conversations`.
- **Mensagem duplicada:** como o `is_sending` nunca chega ao navegador, o “Enviar” não fica desativado. Os eventos de uma aba rodam um depois do outro, então um segundo Enter fica na fila com o mesmo texto. Ele roda quando o primeiro termina, já com `is_sending` falso.

## Objetivos e não objetivos

**Objetivos:**
- mostrar na tela o estado de andamento antes do pedido ao Xano, com o mesmo número de pedidos de hoje;
- desativar o envio do chat desde o acionamento.

**Não objetivos:**
- mudar o texto das mensagens de erro, a ordem das chamadas ao Xano, o cache público ou os limites de pedidos;
- reorganizar os módulos.

## Decisões

### 1. Base flex por largura de tela na busca do cabeçalho

O formulário passa a usar `flex=rx.breakpoints(initial="1 1 100%", md="1 1 0%")`, e o `style={"width": …}` sai. Abaixo de 992 px (o `md` do Reflex, a mesma quebra do `order`), a base de 100% faz a busca ir para a linha de baixo e ocupar a largura toda. A partir de 992 px, fica como hoje: a busca divide a linha com o logotipo e a conta, até 620 px.

- **Alternativa descartada:** `min_width="100%"` no celular, que também faria a busca descer. Mas aí seriam duas propriedades disputando o mesmo papel (a largura e a base), o que deixa o próximo ajuste mais difícil.

### 2. Um `yield` depois de ligar o estado, antes do pedido

Em cada evento da lista acima, o `yield` vem logo depois de ligar o carregando e depois das validações locais. Assim, uma validação que falha continua sem mandar estado intermediário.

- Os eventos que hoje são corrotinas (`send_message`, `refresh_conversations`, `load_older_messages` e `load_more_conversations`) passam a ser geradores. Quem devolvia um evento passa a emiti-lo com `yield`.
- O `_save_edit` deixa de ligar o `is_sending`. Quem liga é o `send_message`, antes do `yield`, tanto para o envio quanto para a edição. O `_save_edit` continua desligando o estado no `finally`.
- Nenhum pedido novo é criado. Só muda o momento em que a tela é atualizada.

### 3. Envio bloqueado pelo botão desativado

Com o `yield`, o “Enviar” (ou “Salvar”) chega desativado ao navegador enquanto o pedido ao Xano está em andamento.

- **Enter no campo:** o Enter envia o formulário pelo botão padrão. Pela especificação do HTML, se esse botão está desativado, o Enter não envia nada. O campo continua ativo, para não perder o foco.
- **No servidor:** a verificação de `is_sending` no começo do evento continua.
- **Alternativa descartada:** recusar no servidor um texto igual ao último enviado poucos segundos antes. Ela bloquearia quem manda “ok” duas vezes de propósito e muda uma regra do chat que a spec não pede.

### 4. Eventos “tentar de novo” que mostram o carregando

Seguem o padrão do `retry_profile` e do `retry_home_data`: um evento curto liga o carregando e devolve o evento de carga de sempre.

- **Detalhe:** `DonationDetailState.retry_donation` liga `view_state = "loading"` e devolve `load_donation`.
- **`/categorias`:** `CategoriesState.retry_categories` liga `loading` e devolve `load_categories`.
- **Gaveta da home:** o `HomeState.reload_categories` ganha a flag `categories_loading`, que é ligada com `yield` antes da busca e passada para a gaveta. Assim, a gaveta mostra “Carregando categorias...” durante o novo pedido.
- **Cadastro de doação:** o botão chama `load_initial_data`, que agora dá `yield` depois de ligar `is_loading_data` (decisão 2). Durante a nova tentativa aparece “Preparando seu cadastro...”.
- **Texto:** “Tentar de novo” em todos os botões. Frases como “Tente novamente.” dentro das mensagens de erro ficam como estão: são orientação, não rótulo de botão.

### 5. Termos em outra aba no aviso legal

O cadastro de doação recomeça vazio a cada entrada (spec `donation-creation`, “Reinício do formulário a cada nova entrada”). Um link para `/termos` na mesma aba faria a pessoa perder o que preencheu, fotos incluídas. Por isso o link usa `is_external=True`, que abre em outra aba com `rel="noopener noreferrer"`.

O texto novo fica “Ao clicar no botão abaixo, você declara que é maior de 18 anos e que leu e concorda com os Termos de uso.”, com “Termos de uso” como link.

### 6. Textos

| Onde | Antes | Depois |
|---|---|---|
| `/seguranca`, cartão | Doei em uma doação | Recebi uma doação (o par de “Criei uma doação”; o texto do cartão fala de quem recebe) |
| `/seguranca`, apresentação | a segurança e transparência | a segurança e a transparência |
| Verificação de e-mail | Olha também no spam. | Confira também a caixa de spam. |
| Home, Comece por aqui | Para você mesmo | Para você |
| Cadastro, etapa 5 | Como prefere ser contatado? | Como prefere que entrem em contato? |
| Ajuda, segurança | vá acompanhado | vá com alguém |

## Riscos e compromissos

- **[Enter antes do primeiro estado chegar]** Se a pessoa aperta Enter duas vezes mais rápido que a ida e volta do websocket (poucos milissegundos, antes da chamada ao Xano), o segundo evento já está na fila. → É o mesmo comportamento do `start_chat` desde a `chat-carregamento`. O intervalo que importa, o do pedido ao Xano (centenas de milissegundos ou mais), fica coberto.
- **[Testes que conferem a lista exata de eventos]** Vários testes comparam os eventos emitidos com `[]` ou com uma lista fixa. → Eles passam a contar com o `None` do envio de estado, e cada um ganha a verificação de que o carregando estava ligado antes do pedido.
- **[Captura de tela do README]** A imagem do passo 5 do cadastro mostra o título antigo. → O texto do README é atualizado, e a troca da imagem fica para a próxima atualização das capturas.
