# Tarefas

Os comandos `git` e `xano` são rodados pelo Higor. O agente edita os arquivos, valida o XanoScript no Xano Developer MCP e revisa as saídas. O push ao Xano usa só `-i` com o caminho exato e dry-run antes, nunca `--sync` nem `--delete`.

## 1. Parte A — Xano: busca pública

- [x] 1.1 Consultar o Xano Developer MCP (filtros opcionais, `includes` e paginação) e criar `xano/api/catalog/catalog/donations/search_GET.xs` conforme a decisão 1. Validar no MCP. Verificação: a validação passa, e só esse arquivo do `xano/` foi criado ou alterado.
  - **Feito:** o texto é comparado sem diferenciar maiúsculas, com `(($db.donation.title|to_lower) includes $search)` (e o mesmo na descrição), onde `$search` é o `q` em minúsculas. O `includes` só é aceito na forma de operador; `|includes:` não passa no validador.
  - A UF usa `($db.donation.state|to_upper) ==? $state`, com o `state` da entrada já em maiúsculas (`filters=trim|upper`), por causa das doações antigas.
  - A categoria usa `==?`, e o texto é opcional por dois ramos de `conditional`.
  - O arquivo é válido no MCP.
- [x] 1.2 (manual, Higor) Rodar `xano workspace push -d ./xano -i "api/catalog/catalog/donations/search_GET.xs" --dry-run` e colar a saída. Verificação: só 1 item, a criação da query `catalog/donations/search` (GET, grupo Catalog). Senão, parar. A saída fica anotada aqui.
- [x] 1.3 (manual, Higor) Fazer o push real com o mesmo comando, sem `--dry-run` e sem `--force`. Verificação: o push conclui, e `GET catalog/donations/search` responde sem token, anotado aqui.
- [x] 1.4 Escrever `scripts/teste_explorar_real.py` com EX1 a EX6 (decisão 7): só leitura, sem login, imprimindo só cenário, status, contagens e OK/FALHOU. Verificação: `py_compile` e, rodado pelo Higor depois da 1.3, OK anotado aqui. Se o EX3 falhar, ajustar o `includes` com `to_lower` e repetir a 1.1 a 1.3.
  - **Resultado (Higor):** o push mostrou só `CREATE catalog/donations/search GET`, e o CLI gravou o `guid` no arquivo. O `teste_explorar_real.py` deu 6/6 OK, inclusive o EX3 (a busca não diferencia maiúsculas).

## 2. Cabeçalho compartilhado

- [x] 2.1 Criar `doafacil/cabecalho.py` e mover para ele o `account_menu()`, mais o `header_auth_controls()` com “Entrar” ou o menu e “Quero Doar” (decisão 3), sem mudar o visual da home. Verificação: os testes da home, do login e de Minhas doações continuam passando sem alteração de comportamento.

## 3. `/explorar` real

- [x] 3.1 Reescrever o `ExploreState` (decisão 2): filtros, busca da página 1 em paralelo com as categorias, `load_more` sem duplicar, erros e título. Verificação: testes em `tests/test_explore.py` para sem filtros, cada filtro e combinações, categoria desconhecida, parâmetros inválidos, “Carregar mais” (acrescenta, some no fim e não dispara duas vezes), falha na primeira página e ao carregar mais, e o título composto.
- [x] 3.2 Reescrever a `explore_page()` (decisões 3 e 4): o cabeçalho com busca e UF que refletem a URL, “Voltar ao início”, “Ver categorias”, o título, o chip da categoria, a grade com `donation_grid_card`, “Carregar mais”, o estado vazio com “Limpar filtros”, o `role="status"`, o `page-fade-enter` só no conteúdo estático e o botão flutuante do chat. Verificação: testes de componente para os `href`, o `on_submit` mantendo a categoria, o chip, o estado vazio, os 44 px, a grade com `minmax(min(100%, 220px), 1fr)` e a ausência de larguras fixas maiores que 360 px.

## 4. Categorias

- [x] 4.1 Criar `doafacil/categorias.py` com `CATEGORY_ICONS`, `category_list()`, `CategoriesState` e `categories_page()`, e registrar `/categorias` (fora do `FUTURE_ROUTES`) com o botão flutuante (decisão 5). Verificação: `tests/test_categories.py` com os ícones por nome (com e sem acento, e o genérico), os links para `/explorar?categoria=<id>`, a falha com o link “Explorar doações”, a página com título, “Voltar ao início” e `page-fade-enter`, e os 44 px.
- [x] 4.2 Criar a `categories_drawer()` e trocar o item “Categorias” do menu da home pelo gatilho da gaveta, reaproveitando o `HomeState.categories`. Conferir se o `rx.drawer` prende o foco e fecha com Esc; senão, usar um `rx.dialog` à esquerda (risco no design). Verificação: testes do gatilho (rótulo, teclado e foco visível), do título “Categorias”, do botão “Fechar” e de que escolher uma categoria fecha e navega. Os testes da home que esperavam o link `/categorias` são atualizados.
  - **Feito com `rx.dialog`** à esquerda (decisão 5), autorizado pelo Higor. O `rx.drawer` do Reflex é o Vaul, que embrulha o mesmo Dialog do Radix e acrescenta arrastar e deslizar. O Dialog puro prende o foco, fecha com Esc e com clique fora e devolve o foco, como o visualizador de fotos do detalhe.

## 5. Documentação e verificação

- [x] 5.1 Atualizar o `docs/design/README.md` (as telas 17 e 18, com as referências e a tabela de diferenças da decisão 8) e o `docs/guia-do-colaborador.md` (o endpoint `search`, a `/explorar` real, as categorias, o `cabecalho.py`, o `/categorias` saindo das rotas futuras e o script real). Verificação: o texto bate com as specs delta e o design.
- [x] 5.2 Rodar `python -m unittest discover -s tests`, `reflex compile` e `openspec validate explorar-categorias --strict`. Verificação: tudo passa, e os resultados ficam anotados aqui.
  - Resultados: 576 testes OK, `reflex compile` OK e `openspec validate --strict` OK.
- [x] 5.3 (manual) No navegador, em 1512 px e 360 px, com e sem sessão, comparando com `docs/design/17-explorar.png` e `18-*.png`:
  - a `/explorar` sem filtros, com cada filtro vindo da home e com a busca do próprio cabeçalho (inclusive mantendo a categoria);
  - o chip da categoria e “Limpar filtros”;
  - o “Carregar mais” até o fim;
  - uma busca sem resultados;
  - a gaveta “Categorias” na home (abrir, Esc, X, clique fora, escolher);
  - a `/categorias` e o “Ver categorias”;
  - o botão do chat nas duas páginas;
  - nenhuma rolagem horizontal.

  Verificação: os itens anotados aqui.
  - **1ª rodada (Higor):** quatro problemas, todos corrigidos.
    1. **Erro grave:** “Cannot read properties of undefined (reading 'toUpperCase')” no menu da conta. A inicial era calculada no navegador com o nome ainda indefinido. Agora vem do servidor (`HeaderState.account_initial` em `cabecalho.py`): sem nome, não há inicial, e aparece o ícone de pessoa. Vale para a home, a `/explorar` e a `/categorias`. Teste: `tests/test_cabecalho.py`.
    2. **“Categorias”** tinha altura e estilo de botão. Virou um `<button>` HTML puro, com cor, fonte, tamanho, peso e alinhamento iguais aos links “Explorar Doações” e “Como funciona”, sem fundo nem borda. Teste em `tests/test_categories.py`.
    3. **Logo da `/explorar`:** agora com o mesmo tamanho da home (100/190 px, 72 px de altura).
    4. **Seletor de UF:** estava em azul-claro. Agora está em `#333333` (11,3:1 sobre o `#EFEFEF` da busca), com o esquema cinza.
  - **2ª rodada (Higor):** OK.
    - Na home, os 3 links do menu iguais e alinhados.
    - O menu da conta sem erro, recarregando várias vezes.
    - Na `/explorar`, o logo do tamanho da home e o “SP” legível.
    - A gaveta OK.
  - **Depois da 2ª rodada:**
    - A `explorar.py` passou a usar `self.router.url` (`query_parameters` e `path`) no lugar do `router.page`, obsoleto desde o Reflex 0.8.1, sem mudar o comportamento.
    - O aviso “no dispatch function for substate(s) … header_state”, visto uma vez com a aba antiga aberta depois de reiniciar, é da aba velha: o `HeaderState` é um subestado novo, que o JavaScript compilado antes não conhecia. Recarregar resolve, e não há o que corrigir.
- [ ] 5.4 Montar a lista de caminhos para o commit; o Higor roda o `git diff --stat` e confere. Verificação: entram só o `search_GET.xs`, os módulos e testes desta change, o script, os docs, os 3 PNGs e `openspec/changes/explorar-categorias/`.
