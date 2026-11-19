# Design

## Context

Os cabeçalhos de hoje:

| Cabeçalho | Onde | Conteúdo |
|---|---|---|
| Home (`doafacil.py`, `index`) | `/` | logotipo à esquerda; links (Explorar Doações, Como funciona, Categorias com gaveta) só em `rx.desktop_only` (≥ 992 px); `header_auth_controls()` (Entrar ou menu da conta, e Quero Doar) |
| `explore_header()` (`explorar.py`) | `/explorar`, `/categorias` | logotipo, busca (desce de linha em telas estreitas), `header_auth_controls()` |
| `logo_header()` (`cabecalho.py`) | páginas institucionais | só o logotipo centralizado; “Voltar ao início” fica abaixo, no conteúdo |
| `back_link_header()` (`chat.py`) | `/chat`, `/doacao/<id>` (via `back_home_header`), `/doacao/<id>/quem-doa`, `/minhas-doacoes`, `/minhas-doacoes/<id>/editar`, `/perfil/editar` | grade `1fr auto 1fr`: Voltar, logotipo e coluna vazia |
| Cabeçalho próprio (`cadastro_doacao.py`) | `/cadastro-doacao` | só o logotipo centralizado; a seta “Voltar” fica numa faixa abaixo (spec `donation-creation`) |
| `_header()` das telas de autenticação | `/login`, `/cadastro`, `/recuperar-senha`, `/verificar-email`, `/nova-senha` | só o logotipo (spec `user-account` e `password-recovery`) |

Outros pontos do código:
- A gaveta de categorias (`categorias.py`) é um `rx.dialog` posicionado à esquerda. O comentário dela registra por que o `rx.drawer` (Vaul) não foi usado.
- O total de não lidas fica em `ChatState.unread_total`, com `unread_total_text` e `unread_link_label`. Ele é consultado pelo `load_unread_total` só na home, na `/explorar`, na `/categorias` e nas institucionais. A spec proíbe essa consulta no detalhe.
- O `LoginState.load_account` (nome; foto uma vez por token) roda na home, na `/explorar`, na `/categorias` e nas institucionais. Nas outras páginas, o nome só aparece se veio de uma navegação anterior.
- O `chat.py` não importa `cabecalho.py`. As páginas com Voltar importam o `back_link_header` de `chat.py`.

## Goals / Non-Goals

**Goals:**
- Um painel de navegação único, usado por todas as páginas com navegação.
- Um cabeçalho centralizado único, que substitui o `logo_header`, o `back_link_header` e o cabeçalho do cadastro de doação.
- O desktop da home, da `/explorar` e da `/categorias` igual ao de hoje.

**Non-Goals:**
- Mudar os fluxos de autenticação.
- Atualizar o total de não lidas automaticamente.
- Mudar a gaveta de categorias da home.
- Criar uma página nova.

## Decisions

### 1. Painel: `rx.dialog` à esquerda, como a gaveta de Categorias

- **Componente e estado:** `nav_menu()` em `doafacil/navegacao.py`, com o estado `NavMenuState.open` e o evento `set_open`. Os itens fecham o painel no `on_click`. Isso é necessário para a âncora `/#como-funciona` funcionar estando já na home.
- **Gatilho:** `rx.el.button` com o ícone `menu`, `aria_label="Abrir menu"`, `aria_haspopup="dialog"` e 44 × 44 px.
- **Painel:**
  - largura `min(360px, 100vw)` e altura `100dvh`;
  - título “Menu” (`rx.dialog.title`) e botão “Fechar” (X, 44 px);
  - descrição só para leitor de tela.
- **Itens:** links de 48 px de altura, com ícone e texto em `#1F1F1F` e foco com `FOCUS_RING`.
  - Explorar doações (`compass`), Como funciona (`circle-help`), Categorias (`layout-grid`) e Quero Doar (`heart-handshake`), este com destaque verde.
  - **Com sessão:** um bloco com o avatar (`_account_avatar`) e o primeiro nome, um separador e os itens Minhas doações, Mensagens (com o selo `unread_badge` e `aria-label` = `unread_link_label`), Editar perfil e Sair (botão, `LoginState.logout`, depois fecha o painel).
  - **Sem sessão:** Entrar (`/login`).
- **“Categorias” no painel leva a `/categorias`, sem abrir a gaveta.**
  - **Alternativa descartada:** abrir a gaveta a partir do painel. Seriam dois dialogs empilhados, com dois focos presos e dois Esc.
  - A `/categorias` já existe “para o celular”, segundo o próprio comentário de `categorias.py`.
- **Quando aparece:** o painel e o ☰ ficam dentro de `rx.mobile_and_tablet` (< 992 px). Assim o desktop não muda nem no DOM visível.

### 2. Cabeçalho centralizado único: `site_header(back=None, show_donate=True)`

- **Estrutura:** em `navegacao.py`, uma grade `1fr auto 1fr`:
  - à esquerda, o Voltar recebido (ou nada);
  - no centro, o logotipo (link para `/`);
  - à direita, `desktop_only(header_auth_controls(show_donate))` e `mobile_and_tablet(nav_menu())`.
- **Funções que passam a usar `site_header`:**
  - `back_link_header(href, label, color)`: mantém a assinatura e o visual do Voltar (só a seta abaixo de `sm`), agora com a coluna da direita preenchida;
  - `back_home_header()`;
  - `logo_header()`.
- **Imports:** `back_link_header` e `back_home_header` mudam de `chat.py` para `navegacao.py`, porque `navegacao.py` importa `ChatState` e senão haveria import circular.
  - Os módulos que os importam passam a importar de `navegacao.py`: `minhas_doacoes`, `editar_perfil`, `perfil_doador`, `detalhe_doacao` e `institucional`.
  - O `_header()` do `chat.py` importa `navegacao` dentro da função.
- **Alturas:** o logotipo e a altura do cabeçalho não mudam (140 × 52 px nas páginas com Voltar, e o mesmo logotipo da home nas institucionais).
  - O `/chat` depende da altura de cerca de 64 px (`calc(100vh - 64px)`). Os controles têm 44 px e cabem nessa linha, então o chat não precisa de exceção.
- **`header_auth_controls(show_donate=True)`:** ganha o parâmetro. O cadastro de doação usa `show_donate=False`.
- **Cadastro de doação:** o cabeçalho próprio vira `site_header(show_donate=False)`. A seta da faixa abaixo continua como está (spec `donation-creation`).
- **Alternativa descartada:** usar nas páginas com Voltar o cabeçalho da home, com logotipo à esquerda. Mudaria o “Voltar na linha do logotipo, à esquerda” das specs do detalhe, de Minhas doações e de Editar perfil, e o Figma dessas telas.

### 3. Home, `/explorar` e `/categorias` abaixo de 992 px

- **Barra:** logotipo, o controle da conta (“Entrar” ou o menu da conta) e o ☰. O “Quero Doar” e os links passam para o painel.
- **Por quê:** em 360 px, com 16 px de margem de cada lado, não cabem o logotipo (100 px), o menu da conta (cerca de 72 px), o “Quero Doar” (cerca de 112 px), o ☰ (44 px) e os espaços. A soma passa de 380 px.
  - Manter a conta na barra preserva a identidade da sessão (foto ou inicial) à vista, como pedem as specs `public-home` e `user-account`.
  - O “Quero Doar” continua a um toque, no painel, com destaque.
- **Implementação:**
  - `header_auth_controls()` ganha a versão `mobile_header_controls()`, com a conta e o `nav_menu()` dentro de `rx.mobile_and_tablet`;
  - a versão completa fica em `rx.desktop_only`;
  - na `explore_header`, a busca continua descendo para a linha própria.
- **Alternativa descartada:** manter “Quero Doar” e mover a conta para o painel. A identidade da sessão sumiria da barra e mudaria mais requisitos (`user-account`, “Identidade da sessão no cabeçalho da home”).

### 4. Páginas com o logotipo centralizado abaixo de 992 px: só o ☰ à direita

Em 360 px, a grade `1fr auto 1fr` deixa cerca de 94 px para cada lateral com o logotipo de 140 px. A conta e o ☰ juntos (cerca de 124 px) não cabem, e o ☰ sozinho (44 px) cabe. A conta, “Entrar” e “Quero Doar” ficam no painel.

### 5. Carregamento da conta: uma vez por sessão

- **Limite do Xano:** o plano grátis aceita 10 pedidos a cada 20 s. Por isso o nome e a foto da conta são buscados **uma vez por sessão (por token)** e reaproveitados em todas as páginas.
- **Marcador:** o `LoginState._account_photo_token`, que já evitava pedir a foto de novo, vira `_account_token` e passa a marcar o nome e a foto juntos.
- **`load_account`:**
  - sem token, limpa o nome, a foto e o marcador, sem pedido;
  - com o marcador igual ao token e o nome preenchido, não faz pedido nenhum;
  - senão, faz o `GET auth/me` (nome) e o `GET auth/profile` (foto) e, se o nome vier, grava o marcador.
  - Uma falha passageira mostra “Minha conta” e não grava o marcador, então a próxima página tenta de novo.
- **Quando busca de novo:**
  - **login:** o token é novo, então o marcador não bate;
  - **logout:** limpa o marcador;
  - **token rejeitado:** no próprio `load_account` ou nas outras páginas, que apagam o token; sem token, o marcador é limpo;
  - **edição do perfil:** o Editar perfil já grava o nome e a foto novos direto no estado (`account_name` e `account_photo`). O valor fica atualizado sem um pedido a mais, e o marcador continua valendo.
- **Efeito na home e nas páginas que já chamavam `load_account`:** elas deixam de pedir o nome a cada carregamento.
- **Páginas que ganham o `LoginState.load_account` no `on_load`:**
  - `/doacao/[id]` e `/doacao/[id]/quem-doa`;
  - `/minhas-doacoes` e `/minhas-doacoes/[id]/editar`;
  - `/chat`;
  - `/cadastro-doacao`.
  - Em `/perfil/editar`, só se o `load_profile` não preencher o nome da conta.
- **Custo:** nenhum pedido a mais depois da primeira carga da sessão. Uma página aberta direto pelo endereço numa aba nova faz a carga uma vez, e as seguintes reaproveitam.
- **Total de não lidas:** nenhuma página passa a consultá-lo. O painel mostra o valor que já estiver no estado (`ChatState.unread_total`).
  - Em páginas abertas diretamente, sem passar pela home, ou no detalhe, “Mensagens” aparece sem número.
  - O `/chat` atualiza o total quando a pessoa lê as conversas.

### 6. Testes

- **`tests/test_navegacao.py` (novo):**
  - **Painel:**
    - o ☰ tem `aria-label` “Abrir menu”, 44 px e `aria-haspopup`;
    - o painel tem o título “Menu”, o “Fechar” e os itens na ordem da spec, com os `href`;
    - com sessão aparecem a conta e “Mensagens” com o selo; sem sessão, “Entrar” e nada da conta;
    - “Categorias” vai para `/categorias`;
    - cada item fecha o painel;
    - a largura é `min(360px, 100vw)`.
  - **Cabeçalho:**
    - o `site_header` tem Voltar à esquerda, logotipo no centro e, à direita, `desktop_only` com os controles e `mobile_and_tablet` com o ☰;
    - `show_donate=False` tira o “Quero Doar”.
  - **Páginas:** cada página da lista da spec renderiza o ☰.
    - As telas de autenticação não o renderizam.
    - O desktop da home continua com os links em `desktop_only`.
  - **`on_load`:** as rotas da decisão 5 incluem o `load_account`, e o detalhe continua sem o `load_unread_total`.
- **`tests/test_cabecalho.py` (cache da conta):**
  - duas cargas com o mesmo token fazem um pedido de nome e um de foto;
  - um token novo carrega de novo;
  - o logout e o token rejeitado limpam o marcador;
  - uma falha passageira não grava o marcador;
  - a edição do perfil atualiza o nome e a foto sem pedido.
- **Ajustes:** os testes de cabeçalho existentes (`test_cabecalho.py`, `test_institucional.py`, `test_my_donations.py`, `test_chat.py`, `test_donation_detail.py` e outros) que conferem a coluna vazia ou o cabeçalho só com o logotipo.

### 7. Diferenças com o Figma (para o `docs/design/README.md`)

| Tela | No Figma | Na implementação | Motivo |
|---|---|---|---|
| todas, abaixo de 992 px | não desenhado | botão ☰ e painel lateral com a navegação e a conta | o Figma não tem telas de celular |
| home, Explorar e Categorias, abaixo de 992 px | “Quero Doar” no cabeçalho (desktop) | “Quero Doar” no painel; a barra fica com o logotipo, a conta e o ☰ | não cabem em 360 px |
| institucionais | só o logotipo centralizado | logotipo centralizado e, à direita, “Entrar” ou a conta e “Quero Doar” (desktop) ou ☰ | acesso à conta e ao cadastro de doação em qualquer página |
| detalhe, perfil de quem doa, chat, Minhas doações, Editar doação e Editar perfil | Voltar, logotipo e lado direito vazio | o mesmo, com os controles do site à direita | idem |
| cadastro de doação | só o logotipo | logotipo e a conta à direita, sem “Quero Doar” | é a própria página do “Quero Doar” |
| painel | não existe | “Mensagens” no painel, com o total de não lidas | no celular não há outro caminho para o chat nas páginas sem botão flutuante |

### 8. Categorias guardadas no servidor (rodada 1 do roteiro)

- **Problema:** na rodada 1, a `/categorias` às vezes mostrou a falha e depois voltou a funcionar, porque navegar rápido estoura o limite de 10 pedidos a cada 20 s do Xano.
  - Hoje as mesmas categorias são buscadas em cada carregamento da home (seletor da busca e gaveta), da `/categorias`, da Explorar com filtro de categoria, do cadastro de doação e da edição de doação.
- **Decisão:** o `_fetch_categories` de `cadastro_doacao.py` guarda a lista num cache do processo do Reflex, por endereço do Xano, durante 1 hora (`CATEGORY_CACHE_SECONDS`).
  - Todos os pontos acima passam por ele. O `fetch_categories` da Explorar só acrescenta os ícones.
  - Falhas não ficam guardadas, então a próxima página ou o “Tentar de novo” buscam de novo.
  - Cada chamada recebe uma cópia da lista, para nenhuma página alterar a lista guardada.
- **Por que no processo e não por sessão:** as categorias são iguais para todos e não são dados pessoais. Guardar no processo atende ao “uma vez por sessão” com folga, porque cada sessão faz no máximo um pedido por hora, e normalmente nenhum.
  - Um cache por sessão (num estado do Reflex) exigiria `get_state` em cada estado que usa categorias, e os testes atuais chamam esses eventos com estados falsos.
  - A validade de 1 hora deixa uma categoria nova criada no Xano aparecer sem reiniciar o servidor.
- **“Tentar de novo”:** a `category_list` ganha `on_retry`, um botão de 44 px abaixo da mensagem de falha.
  - Na `/categorias`, ele chama `CategoriesState.load_categories`.
  - Na gaveta da home, chama `HomeState.reload_categories`, um evento novo que só busca as categorias.
- **Testes:** `clear_category_cache()` limpa o cache nos testes que usam a busca real com cliente falso.
- **Outras listas conferidas:**
  - As UFs e as condições são fixas no código e não fazem pedidos.
  - O nome e a foto da conta já são buscados uma vez por sessão (decisão 5).
  - Ficam com um pedido por carregamento:
    - o total de não lidas, com sessão, na home, na Explorar, na Categorias e nas institucionais;
    - a contagem e as recentes da home.
  - Esses dados mudam com o uso e a spec pede o valor de cada carregamento, por isso não foram guardados.

### 9. Cabeçalho centralizado no mesmo contêiner da home (rodada 1 do roteiro)

- **Problema:** na rodada 1, o cabeçalho das páginas com Voltar e o das institucionais ficaram colados nas bordas, com o “Voltar” encostado à esquerda e o “Quero Doar” encostado à direita e no topo.
  - A grade ocupava a tela toda, com padding de 4 × 16 px.
  - O `/chat` também cortava o topo do logotipo.
- **Decisão:** todos os cabeçalhos centralizados passam pela mesma casca (`_header_shell`). A casca usa as mesmas medidas da home e da Explorar:
  - uma faixa branca de largura total;
  - dentro dela, a grade `1fr auto 1fr` com no máximo `HEADER_MAX_WIDTH` (1200 px), centralizada;
  - padding `HEADER_PADDING` (12 × 16 px abaixo de 992 px e 12 × 24 px a partir daí; no Reflex 0.9.12 o `md` vale 62em);
  - o logotipo da home (`LOGO_WIDTH`, 72 px de altura).
- **Altura:** o cabeçalho fica com a altura da home (72 + 24 px).
- **`/chat`:**
  - **Causa:** a área de mensagens tinha `calc(100vh - 64px)`, mas o cabeçalho já passava de 64 px. A página ficava alguns pixels maior que a tela, e a rolagem até a última mensagem descia a janela inteira, cortando o topo do logotipo.
  - **Correção:** a página passa a ser uma coluna com `height: 100dvh` (mínimo de 520 px). O cabeçalho mantém a altura natural, e a área de mensagens ocupa o resto (`flex: 1` e `min-height: 0`). Assim a altura da área não depende de um número fixo.

### 10. Aviso “no dispatch function” (rodada 1 do roteiro)

- **Origem:** o aviso vem do `.web/utils/state.js` do Reflex. Ele aparece quando chega do backend uma atualização de um estado que o frontend aberto não conhece, isto é, quando o bundle da aba é mais antigo que o backend.
- **Conferência:** no frontend compilado nesta change, todos os 19 subestados do backend, inclusive o `NavMenuState`, têm a sua função de dispatch.
- **Quando aparece:** só no desenvolvimento, quando o `reflex run` recarrega por mudança de arquivo (principalmente ao criar um estado novo) com a aba aberta. Recarregar a aba resolve. Em uso normal, com o frontend compilado junto com o backend, ele não aparece.

### 11. Diagnóstico das falhas ao navegar (rodada 2 do roteiro)

- **Problema:** na rodada 2, a home, a `/categorias` e o detalhe falharam ao navegar, mesmo com o cache de categorias.
- **Log temporário:** antes de corrigir, ligamos um log temporário para ver a causa real.
  - `doafacil/log_xano.py` envolve o `httpx.AsyncClient.send` do servidor e escreve, no terminal do Reflex, cada chamada com:
    - o método e o caminho, sem host nem query;
    - o status e a categoria do erro (LIMITE para 429, ERRO_SERVIDOR, ERRO_CLIENTE, TIMEOUT ou CONEXAO);
    - o tempo em ms;
    - quantas chamadas estavam em andamento.
  - Não mostra token, cabeçalhos, corpos nem a query.
  - Só liga com `DOAFACIL_LOG_XANO=1`.
  - Sai quando a causa for corrigida.
- **Detalhe:** a falha ganha “Tentar novamente”, como a `/categorias`.
- **Minhas doações:** o conteúdo passa a usar o contêiner do cabeçalho (1200 px com `HEADER_PADDING_X` dentro, como a Explorar), e não mais 1396 px com padding fora. Assim ele começa na linha do “Voltar” e termina na do “Quero Doar”.
- **A correção da causa** depende do log e entra como decisão nova.

### 12. Menos pedidos ao Xano (rodada 3: causa confirmada pelo log)

- **Causa:** o log `[xano]` do Higor confirmou 429 LIMITE. O plano grátis aceita 10 pedidos a cada 20 s para o site inteiro, e na apresentação várias pessoas vão navegar ao mesmo tempo.
- **Cache dos dados públicos** (`doafacil/cache_publico.py`): cache do processo, igual para todos, por 60 s (`PUBLIC_CACHE_SECONDS`).
  - **O que é guardado:**
    - contagem e recentes da home, pela URL;
    - cada página da busca, pela URL e pelos filtros e página;
    - o detalhe, pela URL com o id.
  - **Regras:**
    - só dados públicos: o detalhe guardado é o já interpretado, sem os campos privados que a resposta possa trazer, e nenhum desses pedidos leva token;
    - uma falha não fica guardada;
    - cada chamada recebe uma cópia.
  - **Invalidação:** `invalidate_donations()` limpa tudo depois de publicar, editar, mudar status ou apagar com sucesso, dentro das próprias funções de escrita (`_publish_donation`, `update_donation`, `change_status` e `delete_donation`). Assim nenhum caminho de escrita fica de fora.
  - **Alternativa descartada:** cache por sessão. Não ajuda quando várias pessoas abrem a mesma página, que é o caso da apresentação.
- **Total de não lidas** (`ChatState.load_unread_total`): no máximo uma consulta a cada 60 s por pessoa (`UNREAD_REFRESH_SECONDS`, com `_unread_checked_at` e `_unread_checked_token` no estado da sessão). Entre as consultas, as páginas mostram o último valor.
  - O `/chat` atualiza o total na hora e sem pedido a mais:
    - com a lista inteira numa página, o total vira a soma dos contadores;
    - com mais páginas, o marcador é limpo e a próxima página consulta de novo;
    - abrir uma conversa desconta as não lidas dela.
  - Uma falha zera o total, como a spec já pedia, e a próxima página tenta de novo.
- **Nova tentativa no 429 e cancelamento** (`doafacil/xano_http.py`): o `httpx.AsyncClient.send` do servidor é envolvido uma vez.
  - **429:** espera 2 s (`RETRY_DELAY_SECONDS`) e tenta uma vez de novo. Se ainda der 429, a resposta volta para quem chamou, que mostra a sua mensagem de falha.
  - **`CancelledError`:** quando a pessoa navega e o Reflex cancela o evento, o erro segue adiante sem virar mensagem (nenhum handler o captura). O log mostra “CANCELADA”, e não “FALHOU”.
  - **Instalação:** pelo lifespan do app (`app.register_lifespan_task(xano_http.lifespan)`), só quando o servidor sobe. Os testes importam o app sem o wrapper, e cada 429 dos testes continua sendo um pedido só.
  - **Alternativa descartada:** trocar cada `httpx.AsyncClient(...)` por um cliente com transporte próprio. São dezenas de pontos, e vários testes substituem o cliente.
- **Log `[xano]`:** continua só com `DOAFACIL_LOG_XANO=1`, até o Higor confirmar. A nova tentativa aparece como “(nova tentativa)”.
- **Cabeçalho do `/chat`:** largura toda (`full_width=True`), com as margens do cabeçalho. O “Voltar” fica no canto esquerdo e a conta e “Quero Doar”, no direito, alinhados aos painéis do chat, que ocupam a tela toda.
- **Cadastro de doação:** a seta “Voltar ao início” passa para a linha do logotipo, no mesmo `back_link_header` das outras páginas (sem “Quero Doar”). A faixa própria abaixo do cabeçalho sai, o que muda o requisito “Posição da seta de retorno” da spec `donation-creation`.
  - O corte do logotipo não foi reproduzido sem o navegador:
    - nenhum CSS, `transform`, `autofocus` ou rolagem do cadastro desloca o cabeçalho;
    - o app usa o `ScrollRestoration` do react-router.
  - Com o cabeçalho igual ao de Minhas doações, que não tem o corte, o problema deve sumir. Se continuar, o Higor manda um print.
- **“refs.__clear_selected_files is not a function”:** o `rx.clear_selected_files` chama uma função que só o `UploadFilesProvider` registra. O Reflex só monta esse provider quando alguma página usa `rx.selected_files`, e o projeto não usa: os uploads mandam os arquivos direto pelo `on_drop`, sem seleção guardada.
  - As 6 chamadas (2 no cadastro e 4 no Editar perfil) sempre falhavam no navegador e não limpavam nada, então foram retiradas.
- **“Cannot read properties of null (reading 'useContext')”:** o projeto tem uma única cópia do `react` e do `react-dom` (19.2.8), então não é React duplicado. O erro aparece quando um hook roda com o React do módulo ainda nulo, o que acontece quando o Vite reexecuta módulos no hot reload.
  - Em uso normal, com o frontend compilado, ele não deve aparecer. Se aparecer depois de abrir uma aba nova sem editar arquivos, o Higor manda a pilha do erro.
- **`router.page` → `router.url`:** o `doafacil/rotas.py` lê o id pelo caminho da URL (`path_segment_after`), em detalhe, perfil de quem doa e Editar doação. O `/chat` usa `router.url.query_parameters`. Um teste garante que não sobrou `router.page` no código.

### 13. Cabeçalho centralizado na largura toda (rodada 4 do roteiro)

- **Pedido do Higor:** o cabeçalho com o logotipo centralizado passa a ocupar a largura toda da tela em todas as páginas que o usam:
  - detalhe, perfil de quem doa e `/chat`;
  - Minhas doações, Editar doação e Editar perfil;
  - cadastro de doação e institucionais.
- **O que substitui:** o contêiner de 1200 px da decisão 9 e o `full_width` só do `/chat` da decisão 12.
- **Medidas:**
  - a grade `1fr auto 1fr` não tem largura máxima;
  - o padding é `CENTERED_HEADER_PADDING`: 12 × 16 px abaixo de 992 px e 12 × 32 px a partir daí;
  - o “Voltar” fica a 16 px ou 32 px da borda esquerda, e a conta e “Quero Doar” (ou o ☰), à mesma distância da borda direita;
  - o logotipo fica centralizado na tela, com os 72 px e o padding vertical de 12 px da home.
- **O que não muda:**
  - home, `/explorar` e `/categorias` continuam com o contêiner de 1200 px e 24 px a partir de 992 px;
  - no celular, a linha continua com a seta, o logotipo e o ☰.
- **Conteúdo das páginas:** continua com a largura de cada página. O conteúdo de Minhas doações segue no contêiner de 1200 px da decisão 11.

## Risks / Trade-offs

- **[Dados públicos até 60 s atrasados para as outras pessoas]** → Quem fez a mudança vê na hora, pela invalidação. Para os outros, um atraso de até 1 minuto na contagem, na busca ou no detalhe é aceitável num catálogo de doações.
- **[Cache de processo com vários workers]** → Cada worker tem o seu. O número de pedidos cai do mesmo jeito; uma invalidação feita num worker não limpa os outros, que expiram em 60 s.

- **[Nome desatualizado se for mudado fora do site, por exemplo no painel do Xano]** → Ele só se atualiza no próximo login. É aceitável, porque o site é o único lugar de edição do perfil.
- **[Total de não lidas desatualizado no painel]** → O número é o último carregado. Fica explícito na spec, e não há consulta nova, de acordo com a regra do detalhe.
- **[Sair do cadastro de doação pelo menu perde o que foi preenchido]** → O logotipo já levava à home; o menu é mais um caminho. Fica fora do escopo um aviso de dados não salvos.
- **[Mudança de imports do `back_link_header`]** → Os testes de cada página pegam o import quebrado, e o `reflex compile` também.
- **[Dois dialogs na home: gaveta e painel]** → Nunca ficam abertos juntos: a gaveta só existe no desktop e o painel só abaixo de 992 px.

## Migration Plan

Mudança só no frontend. O rollback é reverter pelo `git`.
