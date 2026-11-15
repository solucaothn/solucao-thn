# Design

## Context

O motivo está no `proposal.md`. As referências são os quadros do Figma `438:1426` (Explorar), `474:1650` (home com a gaveta de categorias) e `476:2478` (a lista de uma categoria), salvos em `docs/design/17-explorar.png`, `18-categorias-01.png` e `18-categorias-02.png`. As fotos são das doações de teste do grupo, sem marca d'água, e por isso não foram cobertas.

**Estado atual:**
- `doafacil/explorar.py` tem a página provisória e as funções que ficam: `build_explore_url`, `parse_explore_filters` e `fetch_categories`, com as exclusões do cadastro, além das 27 UFs.
- A home monta a busca e o menu (`NAV_LINKS`, com “Categorias” → `/categorias`) e o `account_menu()` em `doafacil/doafacil.py`.
- `doafacil/cartoes_doacao.py` tem o `_parse_donations` (valida os cartões e calcula o NOVO e a condição) e o `donation_grid_card`, que ocupa a célula da grade, já usado no perfil público.
- **Xano:**
  - `GET catalog/donations` aceita `search` e `category_id`, mas devolve qualquer status, sem foto, condição, UF nem paginação. Nenhum código do site o usa, mas pode haver outros consumidores;
  - `catalog/donations/recent` monta a URL pública da foto (`PUBLIC_BASE_URL` + `path`);
  - `catalog/donations/donor` pagina de 12 em 12, com `page_total` calculado por `ceil(total / 12)`;
  - a tabela `donation` tem `state` (texto, opcional, copiado do perfil), `category_id` e `status` (com índice).
- **XanoScript** (Xano Developer MCP, tópico `database`): `==?` ignora a condição quando o valor é nulo, e `includes` busca um trecho dentro do texto.

## Goals / Non-Goals

**Goals:**
- A `/explorar` real, com os filtros que a home já envia, “Carregar mais” e estado vazio.
- A gaveta e a página de categorias, com as categorias reais.
- Uma única mudança no Xano: um endpoint novo, só de leitura.

**Non-Goals:**
- As seções por categoria na `/explorar` sem filtro.
- Subcategorias.
- Outras ordenações.
- A gaveta fora da home.
- Mudar o `GET catalog/donations` antigo.

## Decisions

### 1. Parte A: `GET catalog/donations/search`, novo e público

- **Entradas:**
  - `text q? filters=trim`;
  - `int category_id?`;
  - `text state? filters=trim|upper`;
  - `int page?=1`.
- **Validação:** `page >= 1` e, quando informado, `state` com 2 letras; senão, `inputerror`.
- **Consulta:** `status == "disponível"`, com `category_id ==? $input.category_id` e `state ==? $input.state`.
  - O texto entra só quando `q` não está vazio: `(title includes q || description includes q)`.
  - O jeito de montar a condição opcional do texto (dois ramos de `conditional` ou um operador nulo-seguro para o `includes`) é conferido no MCP antes de escrever, e o arquivo é validado nele.
  - Ordem: `created_at` decrescente. Paginação: `paging: {page, per_page: 12, metadata: false}`.
- **Totais:** um `return = {type: "count"}` com as mesmas condições, e `page_total = ceil(total / 12)`, como no `donor`.
- **Resposta:** `{items, page, per_page: 12, total, page_total}`. Cada item tem `{id, created_at, title, photo, condition}`, com a foto montada como no `recent`. Sem dono, descrição, cidade nem e-mail.
- **Maiúsculas no texto:** se o `includes` diferenciar maiúsculas, compara `to_lower` dos dois lados. Um cenário do script real confere isso.
- **Alternativa descartada:** alterar o `GET catalog/donations` antigo. Mudaria o contrato de algo que pode ter outros consumidores e que hoje devolve doações de qualquer status.
- **Push:** só o arquivo novo, com dry-run antes. O aceite é 1 item, a criação da query `catalog/donations/search`:
  ```
  xano workspace push -d ./xano -i "api/catalog/catalog/donations/search_GET.xs" --dry-run
  ```

### 2. Estado da `/explorar`

- **`ExploreState`** guarda:
  - os filtros válidos (`search_text`, `category_id`, `category_label` e `state_label`);
  - `items` (os cartões já carregados) e `page`, `page_total` e `total`;
  - `loading`, `loading_more` e `error`.
- **`load_filters`** (no `on_load`):
  - lê `self.router.page.params` com `parse_explore_filters`;
  - busca, em paralelo, as categorias (para o nome) e a página 1;
  - preenche `items` com `_parse_donations`.
- **`load_more`:** se não estiver carregando e `page < page_total`, pede `page + 1` e acrescenta os cartões, sem repetir ids. Numa falha, mantém os cartões e mostra o erro com “Tentar de novo”.
- **Categoria desconhecida:** se o id não está nas categorias, o título usa “Categoria” sem nome e a busca vai com o id, o que no Xano dá 0 resultados (estado vazio). Se o serviço de categorias falhar, a busca acontece mesmo assim, e o título omite o nome.
- **Título:** composto a partir dos filtros (por exemplo, “Categoria “Roupas”” · “Resultados para “cadeira”” · “em SP”). Sem filtros: “Adicionadas recentemente”.

### 3. Cabeçalho da `/explorar` e componentes compartilhados

- **Módulo novo `doafacil/cabecalho.py`**, com `account_menu()` (movido de `doafacil.py`, sem mudança visual) e `header_auth_controls()` (“Entrar” ou o menu da conta, e “Quero Doar”).
  - A home e a `/explorar` importam dali.
  - Assim, `explorar.py` não precisa importar `doafacil.py`, o que criaria um import circular.
- **Cabeçalho da `/explorar`, como no Figma:**
  - logotipo (link para `/`);
  - um `rx.form` com o campo “Buscar” (`name="q"`), o seletor de UF (`name="uf"`, com “Todas” e as 27 siglas) e a lupa (`type="submit"`);
  - os controles de conta.
  - O `on_submit` usa `build_explore_url`, mantendo a `categoria` do estado.
- **Filtro removível:** quando há categoria, um chip “Categoria: Roupas ×” abaixo do título, um link para `build_explore_url(q, None, uf)`.
- **“Voltar ao início”**, com o ícone `chevron-left` e 44 px.
- **“Ver categorias”**, link para `/categorias`. É o caminho do celular, onde o menu da home não aparece.
- **Botão flutuante:** o `chat_fab()` e o `ChatState.load_unread_total` no `on_load`, como na home, com o espaço livre no fim da página.

### 4. Grade e cartões

- O `donation_grid_card`, que já ocupa a célula, é reaproveitado.
- A grade é um `rx.grid` com `grid-template-columns: repeat(auto-fill, minmax(min(100%, 220px), 1fr))` e gap de 20 px, dentro do mesmo contêiner do cabeçalho (até 1200 px, com margens de 16 e 24 px).
  - Em 1200 px, cabem 4 ou 5 colunas.
  - Em 360 px, uma coluna de cerca de 328 px, que o `min(100%, ...)` impede de passar da tela.
- A `/explorar` não tem limite de 4 cartões: cada página traz 12.

### 5. Categorias: gaveta e página

- **Módulo novo `doafacil/categorias.py`:**
  - **`CategoriesState`**, com `categories`, `loading` e `error`, carregado com `fetch_categories`;
  - **`category_list()`**: cada item é um link para `/explorar?categoria=<id>`, com o ícone do `CATEGORY_ICONS` (pelo nome em minúsculas, sem acento: `eletronicos` → `smartphone`, `brinquedos` → `bike`, `livros` → `book-open`, `roupas` → `shirt`, `moveis` → `house`; outro → `tag`), o nome e um `chevron-right` decorativo. Cada item tem pelo menos 44 px;
  - **`categories_drawer()`**: um **`rx.dialog`** preso à esquerda (`position: fixed`, `left: 0`, `height: 100dvh`, largura `min(500px, 100vw)`). O Dialog do Radix prende o foco, fecha com Esc ou clique fora e devolve o foco ao gatilho. Tem o título “Categorias” e o botão “Fechar” (X). Ao escolher, fecha (`close_drawer`) e navega.
    - Na implementação, o `rx.drawer` (Vaul) foi trocado pelo `rx.dialog`, como o Higor autorizou. O Vaul embrulha o mesmo Dialog, mas acrescenta arrastar e deslizar, que aqui não servem, e não dava para conferir o foco dele no Reflex 0.9 sem o navegador;
  - **`categories_page()`**, na rota `/categorias`: o cabeçalho da `/explorar` (decisão 3), “Voltar ao início”, o título “Categorias” e a lista, com `page-fade-enter` e o botão flutuante.
- **Na home:** o item “Categorias” do `NAV_LINKS` vira o gatilho da gaveta (um botão com o mesmo visual dos links), e a gaveta carrega as categorias ao abrir. A home já busca as categorias para a barra de busca, e a gaveta reaproveita o `HomeState.categories`, sem requisição extra.
- **A rota `/categorias` deixa de ser futura:** sai do `FUTURE_ROUTES` e é registrada no `app`.

### 6. Erros e acessibilidade

- Mensagens curtas e sem número fictício.
- O resultado da busca (“N doações encontradas”, ou o estado vazio) é anunciado com `role="status"`.
- O foco fica visível em `#168447` no branco e em `#166B3B` no creme, as mesmas regras de contraste da landing.

### 7. Verificação

- **Testes:**
  - `tests/test_explore.py`, reescrito: filtros, título, “Carregar mais” (acrescenta sem duplicar e some no fim), estado vazio com “Limpar filtros”, falha, cabeçalho, chip da categoria, grade e 360 px;
  - `tests/test_categories.py`, novo: ícones, links, falha, gaveta e página;
  - ajustes em `tests/test_public_home.py` (“Categorias” abre a gaveta) e `tests/test_chat.py` (o botão na `/explorar`).
- **Script real** `scripts/teste_explorar_real.py`, que só lê e não pede login:

  | Cenário | O que confere |
  |---|---|
  | EX1 | a busca sem filtros traz itens só com os campos do cartão e totais coerentes |
  | EX2 | uma categoria do backend filtra |
  | EX3 | `q` sem diferenciar maiúsculas (o título de uma doação da EX1, em maiúsculas) |
  | EX4 | a página além do total vem vazia |
  | EX5 | `state` inválido e `page=0` dão 400 |
  | EX6 | a resposta não tem campos pessoais |

### 8. Diferenças em relação ao Figma

| No Figma | Na implementação | Motivo |
|---|---|---|
| “Estado: Ótimo” | “Condição: Ótimo” | termo do domínio |
| gaveta com “Móveis” | categorias do Xano, sem Alimentos e Móveis | as mesmas exclusões do cadastro |
| seta de “expandir” em cada categoria | seta de “ir” (`chevron-right`) | não há subcategorias |
| `/explorar` sem filtro com “Da categoria “Roupas”” | só “Adicionadas recentemente” | decisão do grupo (fora do escopo) |
| grade fixa de 5 × 245 px | grade flexível, de 220 px para cima | responsivo; uma coluna em 360 px |
| “Voltar ao inicio” | “Voltar ao início” | acento |
| cabeçalho da Explorar sem “Entrar” | “Entrar” ou o menu da conta, como na home | consistência da sessão |
| sem link para categorias na Explorar | “Ver categorias” | caminho no celular |

## Risks / Trade-offs

- **[O `includes` diferenciar maiúsculas]** → `to_lower` nos dois lados, conferido pelo cenário EX3.
- **[`state` gravado com outro formato nas doações antigas]** → o filtro compara em maiúsculas. Doações sem UF não aparecem com o filtro de UF, o que é esperado. O EX2 e uma busca por UF no roteiro manual conferem.
- **[Mover o `account_menu` quebrar a home]** → a mudança é só de lugar, e os testes da home continuam valendo.
- **[A gaveta (Vaul) no Reflex 0.9]** → resolvido com o `rx.dialog` à esquerda (decisão 5). O roteiro manual confere o foco, o Esc e o clique fora.
- **[O estado da Explorar persistir na sessão]** → a busca do cabeçalho só mantém a categoria na própria `/explorar` (pelo `router.page.path`), porque na `/categorias` o estado pode ser antigo.
- **[Muitos resultados]** → 12 por página e “Carregar mais”, sem carregar tudo.

## Migration Plan

1. Parte A: escrever e validar o `search_GET.xs` no MCP; o Higor faz o dry-run e o push; o script real (EX1 a EX6).
2. Frontend: `cabecalho.py`, a `/explorar`, as categorias, testes e docs.
3. O roteiro manual em 1512 px e 360 px.
4. **Rollback:** o frontend volta pelo `git`. O endpoint novo não tem consumidores além do site e pode ficar.
