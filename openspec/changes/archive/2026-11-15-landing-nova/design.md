# Design

## Context

O motivo e a comparação seção por seção estão no `proposal.md`. A referência é o frame `655:2691` do Figma (`l4MoQJUROh7b7gY3vCFTC0`), salvo em `docs/design/16-landing-nova.png` (1512 × 2946).

**Estado atual (`doafacil/doafacil.py`):**
- `index()` monta o cabeçalho inline, a primeira dobra (`donation_count_view` e `recent_donations_view`), a ilustração `/ilustracao-rodape.png`, `start_here_section()`, `institutional_section()`, `public_home_footer()` e o `chat_fab()`.
- `HomeState.load_home_data` busca em paralelo `catalog/donations/recent` e `catalog/donations/count`, cada um com o seu erro independente.
- A barra de busca é só visual: `visual_search_select` usa uma lista fixa de categorias (“Roupas”, “Móveis”…) e o botão não faz nada.
- Nenhum item do menu, cartão ou link do rodapé navega, como pede a spec atual.
- Não existe rota `/explorar` nem página de busca no frontend. O `GET catalog/donations` do Xano aceita `search` e `category_id`, mas não UF; ele fica para a próxima change.
- O `LoginState` guarda só `auth_token` e `account_name`, vindo do `auth/me`, que não traz foto.

**Xano:** `catalog/donations/count` é público e devolve `{count}` com as doações `disponível`. O status das concluídas é `concluída` (`STATUS_COMPLETED` em `minhas_doacoes.py`).

## Goals / Non-Goals

**Goals:**
- A home fica igual ao Figma, salvo as diferenças da decisão 7.
- Todos os links e cartões que têm destino passam a navegar, inclusive para rotas futuras.
- A busca já entrega os filtros em `/explorar`, no formato que a próxima change vai consumir.
- Os números são reais, com a mudança mínima no Xano.

**Non-Goals:**
- A listagem de Explorar doações e o filtro por UF no backend.
- As páginas `/como-funciona`, `/categorias`, `/quem-somos`, `/contato`, `/privacidade`, `/termos`, `/duvidas` e `/seguranca`.
- A foto de perfil no menu da conta.
- O cabeçalho das outras páginas, que continua como está.

## Decisions

### 1. “Pessoas alcançadas” = doações concluídas, no mesmo endpoint de contagem

- **Mudança no `catalog/donations/count`:** uma segunda consulta `db.query donation` com `status == "concluída"` e `return = {type: "count"}`. A resposta passa a `{count, completed}`.
  - É compatível: o site atual só lê `count`.
  - Não traz nenhum dado além das duas contagens.
- **No frontend:** `_fetch_donation_count` passa a devolver as duas contagens, validadas separadamente (inteiro não negativo e não booleano).
  - O `HomeState` ganha `completed_count` e `completed_error`.
  - Um `completed` ausente ou inválido vira erro só dessa estatística, e “Doações em circulação!” continua.
- **Alternativas descartadas:** um endpoint novo `catalog/stats` (mais um arquivo e mais uma requisição para o mesmo dado agregado) e contar contas cadastradas (mede cadastro, não alcance).
- **Push:** só o arquivo, com `-i` e dry-run antes, e o aceite é 1 item, a atualização da query `catalog/donations/count`:
  ```
  xano workspace push -d ./xano -i "api/catalog/catalog/donations/count_GET.xs" --dry-run
  ```
  Antes de escrever o `.xs`, consultar o Xano Developer MCP e validar o arquivo nele.

### 2. Busca: `/explorar?q=&categoria=&uf=` e uma página provisória

- **Parâmetros**, que a próxima change vai consumir:
  - `q`: o texto sem espaços nas pontas, omitido se vazio;
  - `categoria`: o id inteiro da categoria;
  - `uf`: a sigla em maiúsculas.

  Montados com `urllib.parse.urlencode`, só com os filtros escolhidos.
- **Na home:**
  - a barra vira um `rx.form`, então Enter no campo também busca;
  - o `on_submit` monta a URL e chama `rx.redirect`;
  - o seletor de categoria usa o id como valor e o nome como rótulo. As categorias vêm do `catalog/categories`, carregado no `load_home_data` em paralelo com o resto, e uma falha deixa só “Todas as categorias”;
  - a localização usa uma constante com as 27 UFs.
- **Página provisória** (`doafacil/explorar.py`, rota `/explorar`):
  - o `ExploreState.load_filters` lê `self.router.page.params`, valida cada parâmetro (decisão da spec `donation-explore`) e busca o nome da categoria no `catalog/categories`;
  - mostra o título, o aviso “em construção”, o resumo dos filtros e os links de volta;
  - o conteúdo tem a classe `page-fade-enter`.
- **Por que uma página provisória:** sem ela, “Buscar”, “Ver mais...”, “Explorar Doações” e “Para você mesmo” cairiam no 404 até a próxima change. Ela vai ser substituída, mas a rota e os parâmetros ficam.

### 3. Menu da conta com o `rx.menu` (Radix)

- **Gatilho:** um botão com o círculo da inicial (`avatar_initial` de `perfil_publico.py`), o primeiro nome com reticências e o ícone `chevron-down`.
  - Rótulo acessível: “Menu da conta de <nome>”.
  - Pelo menos 44 px de altura.
- **Itens:** “Minhas doações” (`/minhas-doacoes`), “Editar perfil” (`/perfil/editar`) e “Sair” (`LoginState.logout`).
- O Radix já cuida do teclado (setas, Enter e Esc) e do foco.
- **Sem foto:** o `auth/me` não traz a foto, e buscar no `auth/profile` seria uma requisição a mais em cada página. O Figma mostra só a inicial.
- **“Minhas doações”** sai do cabeçalho e passa a ficar só no menu. Três specs descreviam o cabeçalho antigo e ganham delta nesta change: `user-account` (“Identidade da sessão no cabeçalho da home”), `donation-management` (“Link ‘Minhas doações’ no cabeçalho da home”) e `donation-chat-interface` (“Entrada no chat pelo cabeçalho da home”). O texto de falha “Minha conta” continua, agora no gatilho do menu.
- **A página provisória `/explorar` não tem o botão flutuante do chat**, como as outras páginas de passagem. Ela entra na lista da spec `donation-chat-interface`.

### 4. Links e âncoras

| Origem | Destino |
|---|---|
| Menu “Explorar Doações”, “Ver mais...”, cartão “Para você mesmo”, rodapé “Doações” | `/explorar` |
| Menu “Como funciona” | `/como-funciona` (futura) |
| Menu “Categorias” | `/categorias` (futura) |
| Cartão “Ajude quem precisa”, rodapé “Criar doações” | `/cadastro-doacao` |
| Rodapé “Doações mais recentes” | `/#doacoes-recentes` (o `id` na seção de recentes) |
| Rodapé “Clique aqui para falar conosco” | `/contato` (futura) |
| Rodapé “Quem somos”, “Política de privacidade”, “Termos de uso”, “Dúvidas frequentes”, “Segurança e transparência” | `/quem-somos`, `/privacidade`, `/termos`, `/duvidas` e `/seguranca` (futuras) |

- As rotas ficam numa constante (`FUTURE_ROUTES`) em `doafacil.py`. Quando uma página futura for criada, basta registrar a rota, sem mudar o link.
- Os cartões de “Comece por aqui” viram `rx.link` em volta do cartão inteiro, com `_focus_visible` verde.

### 5. Cartões institucionais com placeholder trocável

- Cada cartão vira um quadrado (`aspect-ratio: 1`, até 245 px) com o texto embaixo (categoria e título em branco) e o ícone num círculo `#168447`, como no Figma.
- **Fundo:** uma constante `INSTITUTIONAL_CARDS` com `image: None` e um degradê. Com `image=None`, o cartão usa o degradê verde e cinza (o placeholder). Com o caminho de uma foto (por exemplo, `/landing/historias.jpg` em `assets/`), usa a foto, com um véu escuro embaixo para o texto manter o contraste AA.
- **As imagens do Figma não são baixadas nem usadas.** Quando chegarem as fotos próprias, basta pôr os arquivos em `assets/landing/` e preencher `image`.
- Fundo da seção: `#FFF6E8` (creme); título `#1F1F1F` em 700; texto de apoio em verde `#166B3B` (5,8:1 sobre o creme), alinhado à esquerda como no Figma.

### 6. Números da primeira dobra

- Bloco à esquerda, com dois pares número e rótulo, como nos nós `615:2341` a `615:2344` do Figma: o número em LINE Seed JP Bold 24 px e o rótulo em Regular 16 px, ambos em `#005723` (token `texto/primario`, 8,9:1 sobre o creme).
- Centralizado na altura dos cartões das recentes (`align="center"`), a pedido do grupo. No Figma, o bloco fica no topo.
- **Cartões das recentes:** quadrados de `clamp(220px, calc((100% - 60px) / 4), 260px)` (`RECENT_CARD_SIZE` em `cartoes_doacao.py`). O 100% é a largura do carrossel, então os 4 cartões dividem o espaço entre 220 e 260 px, a pedido do grupo (eram 280 px; no Figma, cerca de 214 px).
  - A linha dos números e do carrossel usa as bordas do conteúdo do cabeçalho: até 1200 px, com 16 px de margem no celular e 24 px a partir de 62em (`HEADER_MAX_WIDTH` e `HEADER_PADDING_X`).
  - Para os 4 caberem em 1512 px, a coluna dos números passou de 14rem para 11rem (176 px): 1200 − 48 − 176 − 32 = 944 px ≥ 4 × 220 + 3 × 20. O rótulo “Doações em circulação!” pode quebrar em duas linhas.
  - Quando não cabe nem com 220 px, o carrossel rola. Em 360 px, cada cartão tem 220 px (cerca de 61% da tela), sem rolagem da página.
  - O requisito “Cartões de doações recentes” da spec `public-home` ganhou delta por causa desse tamanho.
- **Título** (nó `615:2345`): LINE Seed JP Bold 36 px, altura de linha normal, `#2A2A2A`, centralizado, com `min(1376px, 100%)` de largura e 16 px de margem lateral, quebrando em duas linhas em 1512 px. Abaixo disso, `clamp(1.5rem, 2.4vw, 2.25rem)`.
- A coluna da contagem tem 11rem (era 14rem), como descrito acima; a spec do carrossel foi atualizada no delta.
- Carregando: “Carregando...”. Erro: a mensagem curta de cada estatística, sem número.

### 7. Diferenças aprovadas em relação ao Figma

| No Figma | Na implementação | Motivo |
|---|---|---|
| “Estado: Ótimo” nos cartões | “Condição: Ótimo” | termo do domínio e spec atual |
| “COMECE POR AQUI” quase invisível (branco sobre creme) | verde `#166B3B` (6,1:1) | contraste AA; o `#168447` dá só 4,4:1 sobre o creme, e por isso o “Ver mais...” e os links de `/explorar` também usam `#166B3B` |
| “Linkes rápidos” | “Links rápidos” | erro de digitação |
| “Desapego em grupo” com seta | “Em breve”, sem seta | a funcionalidade não existe |
| fotos com marca d'água “shutterstock” | placeholder em degradê | direitos de imagem |
| sem “Projeto acadêmico DoaFácil” | a linha continua | exigida pela spec do rodapé |
| 6 cartões de recentes no quadro | até 4, como hoje | spec atual; “Ver mais...” leva ao resto |
| cartões de recentes com cerca de 214 px | entre 220 e 260 px, dividindo o carrossel | pedido do grupo: textos legíveis e os 4 cabendo em 1512 px |
| linha dos números e cartões quase até a borda | mesmas bordas do conteúdo do cabeçalho (até 1200 px) | pedido do grupo: alinhar ao logo e ao “Quero Doar” |
| números no topo da linha | centralizados na altura dos cartões | pedido do grupo |

As diferenças entram na seção da home do `docs/design/README.md`.

### 8. Testes

Os testes ficam em `tests/test_public_home.py`, com os testes que hoje exigem “sem navegação” atualizados:

- as duas contagens, cada uma com o seu erro;
- a URL da busca com cada combinação de filtros (texto vazio, só UF, todos);
- os `href` do menu, dos cartões, do rodapé e do “Ver mais...”;
- o menu da conta com e sem sessão;
- os textos e o placeholder dos cartões institucionais;
- as larguras fixas que poderiam passar de 360 px.

A página provisória ganha `tests/test_explore.py`, com a validação dos parâmetros, o nome da categoria e o resumo.

## Risks / Trade-offs

- **[Links para rotas futuras levam ao 404]** → aceito pelo grupo. As rotas ficam centralizadas para o registro posterior, e o guia lista as pendentes.
- **[Mais uma requisição na home (categorias)]** → em paralelo com as outras, com timeout de 10 s; a falha não afeta o resto.
- **[A página provisória parecer funcionalidade quebrada]** → o aviso “em construção” e o resumo deixam claro que os filtros chegaram, e não há resultado fictício.
- **[O push do `count_GET.xs` levar outra coisa]** → `-i` com o caminho exato e o aceite de 1 item no dry-run.
- **[Tirar “Minhas doações” do cabeçalho atrapalhar quem já usa]** → o link continua no menu da conta, a um clique.

## Migration Plan

1. O Xano primeiro: editar e validar o `count_GET.xs`, depois o dry-run e o push (o Higor roda). O site atual continua funcionando, porque só lê `count`.
2. O frontend, a página provisória, os testes e a documentação.
3. A verificação no navegador em 1512 px e 360 px e o script real.
4. **Rollback:** o frontend volta pelo `git`. No Xano, o campo `completed` pode ficar, porque nenhum consumidor quebra com ele.
