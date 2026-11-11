# Proposta

## Por quê

Hoje a entrada no chat é o link “Mensagens” do cabeçalho da home. No celular ele vira só um ícone espremido entre “Olá, <nome>” e “Sair”. O Figma da home põe essa entrada num botão flutuante no canto inferior direito, sempre ao alcance.

## O que muda

- **Botão flutuante “Mensagens”**, um componente reutilizável:
  - um círculo verde `#007A42` de 56 px com o ícone `message-circle` branco e sombra leve;
  - preso a 24 px das bordas inferior e direita no computador, e a 16 px no celular;
  - rótulo acessível “Mensagens”, ou “Mensagens, N não lidas” quando houver não lidas.
- **Contador de não lidas no canto do botão:**
  - fundo vermelho com número branco, com contraste AA;
  - “99+” acima de 99, oculto com 0;
  - usa o mesmo total e a mesma consulta única por carregamento que o link usa hoje, sem atualização automática.
- **Destino:** com login, o botão abre `/chat`. Sem login, vai para `/login`, sem consultar o Xano.
- **Onde aparece:**
  - só na home, por enquanto;
  - não aparece no detalhe da doação (`/doacao/<id>`), que já tem o botão “Chat” da própria doação; dois botões de chat confundiriam;
  - também não aparece em `/chat`, `/login`, `/cadastro`, `/verificar-email`, `/recuperar-senha`, `/nova-senha` e `/cadastro-doacao`.
- **Celular:** o botão não pode cobrir botões de ação de forma permanente. A home reserva um espaço no fim do rodapé, para que todo o conteúdo possa passar por cima dele na rolagem.
- **Movimento:** o realce ao passar o mouse respeita `prefers-reduced-motion`.
- **Cabeçalho:** o link “Mensagens” sai do cabeçalho da home. **BREAKING** (visual): o caminho para o chat muda de lugar.

## Fora do escopo

- Nada muda no Xano: o total continua vindo do `unread_total` existente.
- Não há atualização automática do contador fora de `/chat`.
- Depois do login, a pessoa continua indo para a home, como hoje; não há retorno automático ao `/chat`.
- As demais telas futuras só ganham o botão quando uma change pedir.
- O detalhe da doação continua como está: sem o botão e sem a consulta de não lidas.

## Capacidades

### Novas capacidades

Nenhuma.

### Capacidades modificadas

- `donation-chat-interface`: o requisito “Entrada no chat pelo cabeçalho da home” passa a descrever o botão flutuante, onde ele aparece, o destino com e sem login e o contador; o cabeçalho deixa de ter o link.

## Impacto

- **Código:**
  - `doafacil/chat.py`: o componente do botão e uma cor opcional no `unread_badge`;
  - `doafacil/doafacil.py`: tira o link do cabeçalho, põe o botão na home e reserva espaço no rodapé;
  - `assets/chat.css`: o realce e o `prefers-reduced-motion`, num arquivo que já é carregado.
- **Requisições:** nenhuma nova; a home continua com a mesma consulta única de não lidas.
- **Testes:** `tests/test_chat.py`, `tests/test_public_home.py` e `tests/test_login.py`.
- **Documentação:** `docs/design/README.md`, na seção do chat.
