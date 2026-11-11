# Design

## Contexto

O link “Mensagens” mora no cabeçalho autenticado da home ([doafacil.py](../../../doafacil/doafacil.py)), dentro do `rx.cond(LoginState.auth_token, ...)`. Ele leva a `/chat`, usa `ChatState.unread_link_label` como rótulo e mostra o `unread_badge` verde quando `ChatState.unread_total > 0`. O total vem de `ChatState.load_unread_total`, que está no `on_load` da home, faz uma consulta por carregamento e não consulta nada sem token. O detalhe da doação usa `back_home_header()` e já tem o botão “Chat” da própria doação.

## Objetivos / Fora do escopo

**Objetivos:**
- Ter um componente único de botão flutuante, reutilizável pelas próximas telas.
- Mostrá-lo na home, com o mesmo total e a mesma consulta do link.
- Tirar o link do cabeçalho.

**Fora do escopo:**
- O detalhe da doação (decisão 3).
- Mudanças no Xano.
- Atualização automática do contador.
- Retorno ao `/chat` depois do login.

## Decisões

1. **Componente `chat_fab()` em `doafacil/chat.py`**, ao lado do `unread_badge`. É lá que estão o `ChatState` e os rótulos (`messages_link_label`).
   - `rx.link` com `position: fixed`, `bottom`/`right` de `rx.breakpoints(initial="16px", md="24px")`, 56×56 px, `border_radius: 999px`, fundo `#007A42`, `rx.icon("message-circle")` branco de 26 px e sombra `0 4px 12px rgba(0, 0, 0, 0.2)`.
   - `z_index: 20`, acima do conteúdo da página.
   - `href = rx.cond(LoginState.auth_token, "/chat", "/login")`. Sem login não há consulta: o `load_unread_total` já sai sem token.
   - `aria_label = rx.cond(LoginState.auth_token, ChatState.unread_link_label, "Mensagens")`, para que o rótulo nunca mostre um total antigo de quem saiu.
   - `class_name="chat-fab"`.
2. **Contador:** o `unread_badge` ganha um parâmetro opcional `background`, com o verde atual como padrão, para não mudar a lista de conversas.
   - No botão, o fundo é vermelho `#C62828`; o branco sobre ele dá 5,6:1, acima do AA.
   - Fica em `position: absolute`, a `-4px` do topo e da direita, com borda branca de 2 px para se destacar do verde.
   - `aria-hidden`, porque o total já está no rótulo do link.
   - Só aparece com login e `ChatState.unread_total > 0`. O “99+” já vem de `format_unread`.
3. **Sem botão no detalhe (mudança de decisão do Higor):** o detalhe da doação já tem o botão “Chat” da própria doação, e dois botões de chat confundem. Por isso o detalhe não chama `chat_fab()`, o `on_load` de `/doacao/[id]` continua só com `DonationDetailState.load_donation`, sem a consulta de não lidas, e a página não ganha espaço extra no fim.
4. **Onde entra:**
   - `index()` põe `chat_fab()` como último filho da página;
   - as demais páginas, inclusive o detalhe, não chamam o componente. Uma tela futura só o ganha quando o Higor pedir; nesse caso, ela também precisa do `ChatState.load_unread_total` no `on_load` e do espaço no fim.
5. **Espaço no fim (celular):** a constante `CHAT_FAB_CLEARANCE` vale `rx.breakpoints(initial="88px", md="104px")`, que é o botão mais as duas margens.
   - Na home, vira o `padding-bottom` do rodapé, que hoje é de 32 px.
   - Assim, com a página rolada até o fim, nenhum botão fica sob o círculo. Durante a rolagem, o conteúdo passa por baixo, como em qualquer botão flutuante.
6. **Realce e movimento** em `assets/chat.css`, que já está em `stylesheets`, para não mexer na configuração do app:
   - `.chat-fab` tem `transition` de `transform` e `box-shadow` de 150 ms;
   - o `:hover` e o `:focus-visible` sobem 2 px e reforçam a sombra;
   - o `:focus-visible` tem contorno `2px solid #1F1F1F` com `outline-offset: 3px`;
   - em `@media (prefers-reduced-motion: reduce)`, `transition: none` e `transform: none`;
   - o botão não tem animação de entrada, como o cabeçalho, conforme a regra de animação do projeto.
7. **Cabeçalho:** o `rx.link` “Mensagens” sai do cabeçalho autenticado. O `unread_badge` continua importado em `doafacil.py` só se ainda for usado; caso contrário, o import sai.

## Riscos / Trade-offs

- **O botão cobre conteúdo durante a rolagem.** Isso é próprio de botão flutuante. O espaço no fim garante que nada fique coberto de vez.
- **O contador pode ficar desatualizado** enquanto a página está aberta, como já acontece hoje no link.

## Dúvidas

Nenhuma bloqueante. Suposições registradas:
- Depois do login, a pessoa vai para a home, como hoje.
- O vermelho do contador é `#C62828`.
