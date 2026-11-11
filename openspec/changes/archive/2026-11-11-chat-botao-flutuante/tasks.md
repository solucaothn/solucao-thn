# Tarefas

Só frontend: nada muda em `xano/` e não há comandos xano.

## 1. Componente

- [x] 1.1 Adicionar o parâmetro opcional `background` ao `unread_badge`, com o verde atual como padrão (decisão 2). Verificação: os testes de `tests/test_chat.py` da lista de conversas continuam passando.
- [x] 1.2 Criar `chat_fab()` e `CHAT_FAB_CLEARANCE` em `doafacil/chat.py` (decisões 1, 2 e 5):
  - destino `/chat` ou `/login` e rótulo pelo login;
  - contador vermelho só com total maior que zero;
  - 56 px, 16/24 px das bordas, sombra e `class_name="chat-fab"`.

  Verificação: testes de componente do destino, do rótulo, do contador, das cores e das posições.
- [x] 1.3 Acrescentar ao `assets/chat.css` o realce, o foco visível e o `prefers-reduced-motion` do `.chat-fab` (decisão 6). Verificação: teste que lê o CSS.

## 2. Páginas

- [x] 2.1 Tirar o link “Mensagens” do cabeçalho da home, pôr `chat_fab()` na home e reservar o espaço no rodapé (decisões 4, 5 e 7). Verificação: os testes do cabeçalho de `tests/test_login.py` e `tests/test_public_home.py` são atualizados e passam, sem “Mensagens” no cabeçalho, com o botão na página.
- [x] 2.2 Manter o detalhe da doação sem o botão (decisão 3, mudança de decisão do Higor): sem `chat_fab()`, sem espaço extra no fim e com o `on_load` de `/doacao/[id]` só com `DonationDetailState.load_donation`. Verificação: `git diff` vazio em `doafacil/detalhe_doacao.py` e `tests/test_donation_detail.py`, e o teste do `on_load` original passando.
- [x] 2.3 Garantir que o detalhe da doação, `/chat`, `/login`, `/cadastro`, `/verificar-email`, `/recuperar-senha`, `/nova-senha` e `/cadastro-doacao` não têm o botão. Verificação: teste que renderiza cada página e não encontra `chat-fab`.

## 3. Documentação

- [x] 3.1 Atualizar a seção do chat de `docs/design/README.md`: o botão flutuante, o contador vermelho, as páginas onde aparece e o fim do link no cabeçalho. Verificação: o texto bate com a spec delta.

## 4. Verificação

- [x] 4.1 Rodar `python -m unittest discover -s tests`, `openspec validate chat-botao-flutuante --strict` e `reflex compile`, e mostrar `git diff --stat`. Verificação: tudo passa e nada muda em `xano/`.
- [x] 4.2 (manual) No navegador, na home, com e sem login, em 1512 px e 360 px:
  - o botão no canto, com contador e “99+”;
  - o destino `/chat` ou `/login`;
  - o rótulo no leitor de tela;
  - nada coberto no fim da página e sem rolagem horizontal;
  - o realce com e sem `prefers-reduced-motion`;
  - o botão não aparece no detalhe da doação nem nas demais páginas excluídas.

  Verificação: os itens conferidos e anotados.

  Conferido pelo Higor: o botão aparece só na home, com o contador vermelho; sem login, vai para `/login`; não aparece no detalhe nem nas outras páginas; o celular está OK.
