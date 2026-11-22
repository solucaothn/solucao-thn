# Design

## Context

- **Login:**
  - `LoginState.login` termina com `rx.redirect("/")`;
  - o `/login` tem o `on_load` `consume_password_reset_notice`;
  - o cadastro termina na verificação do e-mail (`verify_recovery_page` com `verification_flow="signup"`), que leva a `/login` com o aviso de conta confirmada.
- **Idas ao login:** há 39 `rx.redirect("/login")` ou `href="/login"`:
  - redirecionamentos por falta de sessão, ou por 401, em `cadastro_doacao.py`, `chat.py`, `detalhe_doacao.py`, `editar_perfil.py`, `minhas_doacoes.py` e `login.py`;
  - o “Entrar” do cabeçalho (`account_control`, com `on_click=rx.redirect("/login")`);
  - o “Entrar” do painel (`_nav_item("Entrar", "/login", …)`);
  - o `chat_fab` (`href=rx.cond(logged_in, "/chat", "/login")`).
- **Parâmetros da página:** `doafacil/rotas.py` já lê a URL atual pelo `router.url`.
- **404:** o Reflex 0.9.12 aceita uma página própria com `app.add_page(componente, route="404", title=…)`; o padrão está em inglês.
- **Títulos:** 14 `add_page` não têm `title`: home, login, cadastro, recuperar senha, verificar e-mail, nova senha, cadastro de doação, detalhe, quem doa, Minhas doações, editar doação, Editar perfil, chat e 404.
- **Favicon:** `assets/favicon.ico` é o do Reflex, e o `assets/logo.svg` (199 × 72) tem o símbolo à esquerda e o texto à direita, só em vetor.
- **Detalhe indisponível:** o `view_state == "not_found"` mostra só “Doação não encontrada” (`_detail_state_message`).
- **Chat vazio:** mostra `EMPTY_LIST_MESSAGE` (“Você ainda não tem conversas.”) sem link.
- **Larguras:**

  | Página | Contêiner do conteúdo |
  |---|---|
  | Minhas doações e Explorar | 1200 px (`HEADER_MAX_WIDTH`) com `HEADER_PADDING_X` dentro |
  | perfil de quem doa | 1396 px com padding fora |
  | detalhe | 1440 px com padding fora |
  | Editar perfil | 1236 px |

## Goals / Non-Goals

**Goals:**
- Um único jeito de ir ao login com origem, seguro contra open redirect.
- Títulos, favicon e 404 coerentes em todas as páginas.

**Non-Goals:**
- Guardar o `next` além da navegação, por exemplo depois de recarregar a página ou entre abas.
- Mudar a galeria ou a disposição do detalhe, além da largura do contêiner.

## Decisions

### 1. `next` seguro, em `doafacil/rotas.py`

- **`safe_next(value) -> str`:** devolve o caminho se ele for seguro, ou "" se não for. Para ser seguro, o valor tem que:
  - ser texto, com até 512 caracteres;
  - começar com `/`, mas não com `//`;
  - não ter `\`, espaços nem caracteres de controle (`< 0x20`, `0x7F`);
  - não ter esquema nem host no `urlsplit`;
  - não ser uma tela de autenticação (`/login`, `/cadastro`, `/recuperar-senha`, `/verificar-email` e `/nova-senha`, com ou sem query).
- **`current_path(router) -> str`:** o `router.url.path` mais a query, quando houver.
- **`login_url(next_path) -> str`:** `"/login?next=" + quote(next, safe="/")` quando o `next` for seguro, e `"/login"` quando não for.
- **`login_redirect(state)`:** atalho para `rx.redirect(login_url(current_path(state.router)))` nos handlers. Sem `router`, como nos estados falsos dos testes, vira `"/login"`.
- **Alternativa descartada:** guardar a origem no estado da sessão. O `next` na URL sobrevive a um novo carregamento do `/login` e não depende do estado da página anterior.

### 2. Onde o `next` entra

- **Handlers que hoje fazem `rx.redirect("/login")`:** passam a usar o `login_redirect(self)` (ou `state`). Isso vale para a falta de sessão e para o 401: depois de entrar de novo, a pessoa volta à mesma página.
  - Exceções, que continuam indo ao `/login` puro:
    - o `login.py` dentro do fluxo de autenticação (verificação e nova senha);
    - os redirecionamentos de páginas que só existem com sessão e não fariam sentido como volta, por exemplo depois de apagar a conta.
- **Links e botões que não estão num handler:**
  - computed var `LoginState.login_href` (`@rx.var`), igual a `login_url(current_path(self.router))`;
  - o “Entrar” do cabeçalho passa a `rx.redirect(LoginState.login_href)`;
  - o “Entrar” do painel passa a `href=LoginState.login_href`;
  - o `chat_fab` sem sessão passa a `href=LoginState.login_href`.
- **Login:** `LoginState.login` lê o `next` do `router.url` no envio e redireciona para `safe_next(next) or "/"`.
- **Cadastro de conta:**
  - o link “Criar conta” do `/login` vira `/cadastro?next=…` (computed var `signup_href`);
  - o `signup` guarda o `next` seguro numa variável de backend, `_auth_next`;
  - a verificação do e-mail leva a `login_url(_auth_next)`;
  - o link “Entrar” do `/cadastro` mantém o `next`.

### 3. Página 404 (`doafacil/nao_encontrada.py`)

- **Estrutura:** o `site_header()` (cabeçalho comum de largura toda, sem “Voltar”) e um conteúdo centralizado em `page-fade-enter`, com:
  - o `h1` “Página não encontrada”;
  - a frase “O endereço pode ter mudado ou não existe mais.”;
  - os dois links de 44 px: “Voltar ao início”, em verde cheio, e “Explorar doações”, com contorno;
  - o fundo creme.
- **Registro:** `app.add_page(not_found_page, route="404", title="Página não encontrada | DoaFácil", on_load=LoginState.load_account)`. A conta é carregada uma vez por sessão, sem pedido a mais.

### 4. Títulos e favicon

- **Títulos dos `add_page`:**

  | Página | Título |
  |---|---|
  | home | “Início” |
  | login | “Entrar” |
  | cadastro | “Criar conta” |
  | recuperar senha | “Recuperar senha” |
  | verificar e-mail | “Confirmar e-mail” |
  | nova senha | “Nova senha” |
  | cadastro de doação | “Quero Doar” |
  | detalhe | “Doação” |
  | quem doa | “Quem doa” |
  | Minhas doações | “Minhas doações” |
  | editar doação | “Editar doação” |
  | Editar perfil | “Editar perfil” |
  | chat | “Mensagens” |
  | 404 | “Página não encontrada” |

  - Um teste percorre o `app._unevaluated_pages` e exige `“… | DoaFácil”` em todas.
- **`scripts/gerar_favicon.py`:**
  1. renderiza o `assets/logo.svg` com o PyMuPDF em alta resolução, com fundo transparente;
  2. recorta o símbolo por manchas de tinta conectadas: parte da maior (mão e folha) e junta as que ficam ao menos metade dentro da caixa dele (coração, brilhos). Não dá para cortar por um vão entre colunas, porque a ponta da folha passa por cima do “d”;
  3. centraliza o recorte num quadrado: sem respiro no .ico e no PNG de 32 px (na aba o símbolo vazado ficaria pequeno), com 8% de respiro no apple-touch-icon (o iOS arredonda os cantos).
- **Arquivos gravados:**
  - `assets/favicon.ico`, nos tamanhos 16, 32 e 48;
  - `assets/favicon-32.png`;
  - `assets/apple-touch-icon.png`, de 180 px, com fundo branco, porque o iOS não aceita transparência.
- **Uso no app:** o Reflex já usa o `favicon.ico`. O `rx.App(head_components=[…])` acrescenta `<link rel="icon" type="image/png" sizes="32x32" href="/favicon-32.png">` e `<link rel="apple-touch-icon" sizes="180x180" href="/apple-touch-icon.png">`.
- **Dependência:** o `pymupdf` não entra no `requirements.txt`, porque o site não precisa dele. Ele vai para um `requirements-dev.txt` novo, com um comentário de que só o script usa, e o topo do script explica como instalar. Os 3 arquivos são gerados uma vez e entram prontos no commit. O teste dos arquivos não depende do PyMuPDF.
- **Teste dos arquivos:**
  - o `.ico` tem os 3 tamanhos;
  - os PNGs têm 32 e 180 px;
  - o de 180 px é opaco;
  - o símbolo ocupa boa parte do quadrado: menos de 40% de pixels transparentes no de 32 px.

### 5. Doação indisponível

- O `_detail_state_message` ganha ações opcionais.
- No estado `not_found`, aparecem:
  - a frase “Ela pode ter sido reservada, concluída ou removida por quem doou.”;
  - os links “Ver outras doações” (`/explorar`) e “Voltar ao início” (`/`), com 44 px.
- O título “Doação não encontrada” continua, como as specs atuais exigem, e o texto não diz qual caso aconteceu.

### 6. Chat vazio

- No ramo da lista vazia, depois do `EMPTY_LIST_MESSAGE`, entra o link “Explorar doações” (`/explorar`), em verde, com 44 px e foco visível.

### 7. Contêiner do conteúdo

- **Mesma regra de Minhas doações:** `max_width=HEADER_MAX_WIDTH`, `padding_x=HEADER_PADDING_X` dentro do contêiner e `box_sizing="border-box"`. O padding vertical continua no contêiner de fora.
  - **Perfil de quem doa:** o `CONTENT_MAX_WIDTH` deixa de ser 1396 px.
  - **Detalhe:** os 1440 px saem da grade e dos estados de carregando, não encontrada e erro, e o `padding` horizontal da grade passa a ser o `HEADER_PADDING_X`.
  - **Editar perfil:** os 1236 px saem.
- **Galeria:** a grade do detalhe (`gridTemplateAreas` e colunas) não muda; só fica mais estreita. Um teste confere que as áreas e as colunas são as mesmas de antes.

### 8. Testes

- **`tests/test_acabamento.py` (novo):**
  - `safe_next` com casos aceitos e recusados:
    - `https://x.com`, `//x.com`, `/\\x.com`, `javascript:`, `/login?next=…`, espaços, controle e mais de 512 caracteres são recusados;
  - `login_url` e `login_redirect`;
  - login com `next` seguro e com `next` inválido;
  - o `next` atravessando o cadastro;
  - títulos de todas as páginas;
  - favicon e `head`;
  - página 404;
  - doação indisponível e chat vazio;
  - contêiner das três páginas.
- **Ajustes:** os testes existentes que conferem `rx.redirect("/login")` exato passam a conferir `/login` mais o `next` da página, ou `/login` puro onde o estado falso não tem `router`.

## Risks / Trade-offs

- **[Open redirect]** → `safe_next` só aceita caminho interno e é testado com os vetores comuns (`//`, `\`, esquemas, controle e espaços).
- **[`next` com dados na query]** → A query da origem pode ter o texto de uma busca (`/explorar?q=…`). Ela volta ao próprio site e não é registrada em log.
- **[Muitos pontos de redirecionamento]** → O helper concentra a regra, e um teste procura `rx.redirect("/login")` sobrando nos módulos de páginas com sessão. As exceções do fluxo de autenticação são listadas no próprio teste.
- **[PyMuPDF]** → Fica só no `requirements-dev.txt`, e o Higor instala quando for gerar o favicon de novo. O site e os testes não dependem dele.

## Migration Plan

Mudança só no frontend. O rollback é reverter pelo `git`.
