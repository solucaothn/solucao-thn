# Tarefas

Os comandos `git` e `xano` são feitos pelo Higor. Esta change não mexe no Xano.

## 1. Painel e cabeçalho comum

- [x] 1.1 Criar `doafacil/navegacao.py` com o `NavMenuState` e o `nav_menu()` (decisão 1):
  - o ☰ com “Abrir menu”, 44 × 44 px e `aria-haspopup`;
  - o painel com o título “Menu” e o “Fechar”;
  - os itens para todos, com sessão (avatar, nome, Mensagens com o selo, Sair) e sem sessão (Entrar);
  - cada item fecha o painel.

  Verificação: os testes do painel em `tests/test_navegacao.py` passam.
- [x] 1.2 Criar `site_header(back=None, show_donate=True)` em `navegacao.py` e o parâmetro `show_donate` em `header_auth_controls` (decisão 2). Mover `back_link_header` e `back_home_header` de `chat.py` para `navegacao.py`, mantendo as assinaturas, e trocar os imports. O `logo_header` passa a usar o `site_header`. Verificação: os testes do cabeçalho em `tests/test_navegacao.py` passam, e a suíte inteira roda sem erro de import.

## 2. Páginas

- [x] 2.1 Home, `/explorar` e `/categorias` abaixo de 992 px (decisão 3): na barra, a conta e o ☰ em `mobile_and_tablet`; os controles completos em `desktop_only`. O desktop fica igual. Verificação: testes da home e da Explorar; os links da home continuam em `desktop_only`.
- [x] 2.2 Páginas com Voltar (`/chat`, detalhe, perfil de quem doa, Minhas doações, Editar doação, Editar perfil) e institucionais com o `site_header` (decisões 2 e 4). Verificação: cada página renderiza o ☰ e os controles do desktop, com o Voltar na mesma posição; os testes existentes de cabeçalho são ajustados e passam.
- [x] 2.3 `/cadastro-doacao` com `site_header(show_donate=False)`, mantendo a faixa da seta. Verificação: o teste confere a conta sem “Quero Doar” e a seta no lugar.
- [x] 2.4 Conta uma vez por sessão (decisão 5): o `_account_photo_token` vira `_account_token`, marcando o nome e a foto, e o `load_account` sai sem pedido quando a conta do token já foi carregada. Verificação: os testes do cache em `tests/test_cabecalho.py` passam:
  - duas cargas fazem um pedido;
  - um token novo carrega de novo;
  - o logout e o token rejeitado limpam o marcador;
  - uma falha passageira não grava o marcador;
  - a edição do perfil não faz pedido.
- [x] 2.5 `LoginState.load_account` no `on_load` das rotas da decisão 5, sem `load_unread_total` novo. Verificação: o teste das rotas confere o `on_load`, e o detalhe continua sem o `load_unread_total`.
- [x] 2.6 Confirmar que as telas de autenticação continuam sem o ☰ e sem os controles. Verificação: o teste passa.
- [x] 2.7 (rodada 1) Categorias com cache no servidor (decisão 8):
  - o `_fetch_categories` com cache de 1 h por endereço e sem guardar falhas;
  - o `fetch_categories` da Explorar passa por ele;
  - “Tentar de novo” na `category_list` (`/categorias` e gaveta da home, com o `HomeState.reload_categories`).

  Verificação: os testes do cache e do botão passam.
- [x] 2.8 (rodada 1) Cabeçalho centralizado com o contêiner, o padding e o logotipo da home, e o `/chat` como coluna de `100dvh` (decisão 9). Verificação: o teste confere o `HEADER_MAX_WIDTH`, o `HEADER_PADDING` e o logotipo de 72 px no `site_header` e no `logo_header`, e a altura do `/chat` sem o `calc(100vh - 64px)`.
- [x] 2.9 (rodada 2) Diagnóstico e ajustes (decisão 11):
  - o log temporário `doafacil/log_xano.py` (só com `DOAFACIL_LOG_XANO=1`), com testes de que não vaza token, query nem host;
  - “Tentar novamente” no erro do detalhe;
  - Minhas doações no contêiner do cabeçalho.

  Verificação: 678 testes OK e `reflex compile` OK.
- [x] 2.10 (rodada 3) Corrigir a causa: 429 do Xano, confirmado pelo log (decisão 12):
  - cache dos dados públicos por 60 s (contagem, recentes, busca e detalhe), limpo nas escritas;
  - total de não lidas no máximo a cada 60 s por pessoa, atualizado na hora no `/chat`;
  - nova tentativa única depois de 2 s no 429;
  - cancelamento sem erro.

  Verificação: `tests/test_cache_publico.py`, `tests/test_xano_http.py` e as classes de não lidas em `tests/test_chat.py` passam.
- [x] 2.11 (rodada 3) Cabeçalho do `/chat` na largura toda; seta do cadastro de doação na linha do logotipo; sem `rx.clear_selected_files`; `router.page` trocado por `router.url` (`doafacil/rotas.py`). Verificação: `tests/test_navegacao.py`, `tests/test_donation_creation.py` e `tests/test_rotas.py` passam.
- [x] 2.12 (rodada 4) Cabeçalho centralizado na largura toda (decisão 13): “Voltar” e controles a 32 px das bordas a partir de 992 px e a 16 px abaixo; logotipo centralizado com a altura e o padding vertical da home; o mesmo no `/chat`. Verificação: `tests/test_navegacao.py` (`HeaderContainerTests` e `test_chat_header_same_as_other_back_pages`) passa.

## 3. Documentação e verificação automatizada

- [x] 3.1 Atualizar o `docs/design/README.md`, com a tabela de diferenças da decisão 7 e a descrição do menu do celular, e o `docs/guia-do-colaborador.md`, com o `site_header` e o `nav_menu` para as páginas novas. Verificação: o texto bate com as specs delta.
- [x] 3.2 Rodar `python -m unittest discover -s tests`, `reflex compile` e `openspec validate navegacao-celular --strict`. Verificação: tudo passa, e os resultados ficam anotados aqui.
  - Resultados: 664 testes OK (18 novos em `tests/test_navegacao.py` e 4 do cache em `tests/test_cabecalho.py`), `reflex compile` OK e `openspec validate --strict` OK.
  - Rodada 1 do roteiro (2.7 e 2.8): 673 testes OK (7 de categorias em `tests/test_categories.py` e 2 de cabeçalho em `tests/test_navegacao.py`), `reflex compile` OK e `openspec validate --strict` OK.

## 4. Verificação manual e commit

- [x] 4.1 (manual, Higor) No navegador, a 360 px, 768 px e 1280 px. Verificação: os itens anotados aqui.
  - **Abaixo de 992 px:**
    - o ☰ aparece na home, na Explorar, nas institucionais, no detalhe, no chat, em Minhas doações, em Editar perfil e no cadastro de doação;
    - o painel abre, prende o foco (Tab circula dentro dele) e fecha com o X, com Esc e com clique fora, devolvendo o foco ao ☰;
    - “Como funciona” rola até a seção da home;
    - com e sem sessão aparecem os itens certos, e “Sair” encerra a sessão;
    - não há rolagem horizontal.
  - **1280 px:**
    - a home, a Explorar e a Categorias ficam iguais a antes;
    - as outras páginas mostram a conta e “Quero Doar” à direita, sem “Quero Doar” no cadastro de doação.
  - **Telas de autenticação:** continuam só com o logotipo.
  - Resultado (Higor):
    - o cabeçalho com Voltar fica na ponta esquerda e a conta e “Quero Doar” na direita, em todas as páginas;
    - o painel ☰ funciona a 360 px, com e sem sessão;
    - a navegação rápida não mostra “Não foi possível carregar”, e o log `[xano]` não tem 429 nem nova tentativa.
  - O log `[xano]` fica no código, desligado por padrão (`DOAFACIL_LOG_XANO=1` liga).
- [ ] 4.2 Montar a lista de caminhos para o commit; o Higor confere com o `git diff --stat`. Verificação: entram só os arquivos desta change.
