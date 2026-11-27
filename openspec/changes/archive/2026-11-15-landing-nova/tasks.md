# Tarefas

Os comandos `git` e `xano` são rodados pelo Higor. O agente edita os arquivos, valida o XanoScript no Xano Developer MCP e revisa as saídas. O push ao Xano usa só `-i` com o caminho exato e dry-run antes, nunca `--sync` nem `--delete`.

## 1. Xano: contagem de concluídas

- [x] 1.1 Consultar o Xano Developer MCP e editar `xano/api/catalog/catalog/donations/count_GET.xs` para responder `{count, completed}`, com a segunda contagem de `status == "concluída"` (decisão 1). Validar o arquivo no MCP. Verificação: a validação passa, e só esse arquivo do `xano/` mudou.
- [x] 1.2 (manual, Higor) Rodar `xano workspace push -d ./xano -i "api/catalog/catalog/donations/count_GET.xs" --dry-run` e colar a saída. Verificação: só 1 item, a atualização da query `catalog/donations/count`. Senão, parar. A saída fica anotada aqui.
  - **Resultado (Higor):** o dry-run foi aceito e o push foi feito.
- [x] 1.3 (manual, Higor) Fazer o push real com o mesmo comando, sem `--dry-run` e sem `--force`. Verificação: o push conclui, e a home atual continua mostrando “Doações em circulação”, anotado aqui.
  - **Resultado (Higor):** `GET catalog/donations/count` responde `{count: 8, completed: 0}`, e um novo push responde “No changes to push”.
- [x] 1.4 Escrever `scripts/teste_landing_real.py`, que só lê: `catalog/donations/count` sem token traz `count` e `completed` inteiros e não negativos, e `catalog/categories` traz uma lista. Verificação: `py_compile`, o `--help` e, rodado pelo Higor depois da 1.3, OK anotado aqui.
  - **Resultado (Higor):** 2/2 OK (`count=8`, `completed=0`).

## 2. Estatísticas e cabeçalho

- [x] 2.1 No `HomeState`, ler `completed` da contagem, com `completed_count` e `completed_error` independentes, e mostrar os dois números no layout da decisão 6. Verificação: testes em `tests/test_public_home.py` para as duas contagens válidas, `completed` ausente ou inválido (só essa estatística com erro) e a falha do serviço (as duas com erro, sem número fictício).
- [x] 2.2 Transformar o menu do cabeçalho em links (`/explorar`, `/como-funciona` e `/categorias`) e criar o menu da conta com o `rx.menu`: inicial, primeiro nome com reticências, “Minhas doações”, “Editar perfil” e “Sair” (decisão 3). Centralizar as rotas futuras em `FUTURE_ROUTES`. Verificação: testes dos `href`, do menu com e sem sessão, do rótulo acessível, dos 44 px e de “Minha conta” na falha da consulta. Os testes antigos de “Olá, nome” e “Sair” no cabeçalho são atualizados.

## 3. Doações recentes, “Comece por aqui” e busca

- [x] 3.1 Colocar o `id="doacoes-recentes"` na seção, o título “Doações mais recentes:” e o link “Ver mais...” para `/explorar`, visível também com a lista vazia ou com erro. Verificação: testes do `id`, do texto e do `href` nos três estados.
- [x] 3.2 Transformar “Para você mesmo” (`/explorar`) e “Ajude quem precisa” (`/cadastro-doacao`) em links inteiros com foco visível, manter “Desapego em grupo” com “Em breve” e deixar a etiqueta “COMECE POR AQUI” em `#166B3B` (o `#168447` dá só 4,4:1 sobre o creme). Verificação: testes dos `href`, do cartão sem link e do contraste da etiqueta.
- [x] 3.3 Transformar a barra em `rx.form`: categorias do `catalog/categories` (carregadas no `load_home_data`, com “Todas as categorias” e queda segura na falha), as 27 UFs e o redirecionamento para `/explorar` com `q`, `categoria` e `uf` só quando escolhidos (decisão 2). Verificação: testes da URL com cada combinação (nada, só texto com espaços nas pontas, só UF, os três), da falha das categorias e de que a lista fixa antiga sumiu.

## 4. Seção institucional e rodapé

- [x] 4.1 Refazer os cartões institucionais (decisão 5): quadrados, com ícone em círculo verde, categoria e os títulos novos, sem “Saiba mais”, com placeholder em degradê via `INSTITUTIONAL_CARDS` (`image: None`), fundo creme e o texto de apoio em `#166B3B`. Verificação: testes dos textos, da ausência de “Saiba mais” e de imagens externas, e do contraste do texto.
- [x] 4.2 Transformar os itens do rodapé em links com os destinos da decisão 4 e foco visível, mantendo “Projeto acadêmico DoaFácil”. Verificação: testes de cada `href`. O teste antigo “sem navegação” é atualizado.

## 5. Página provisória `/explorar`

- [x] 5.1 Criar `doafacil/explorar.py` com o `ExploreState.load_filters` e a página (spec `donation-explore`), e registrar a rota `/explorar` em `doafacil.py`, sem o botão flutuante do chat. Verificação: `tests/test_explore.py` com os filtros válidos, a categoria desconhecida, a `categoria` não numérica, a UF inválida, a página sem filtros, os links de saída, o `page-fade-enter` e a ausência de lista de doações.

## 6. Documentação e verificação final

- [x] 6.1 Atualizar o `docs/design/README.md`, na seção da home, com a referência `16-landing-nova.png` e a tabela de diferenças aprovadas (decisão 7), e o `docs/guia-do-colaborador.md`: a contagem com `completed`, as rotas futuras pendentes, a página provisória `/explorar` e o script real. Verificação: o texto bate com as specs delta e o design.
- [x] 6.2 Rodar `python -m unittest discover -s tests`, `reflex compile` e `openspec validate landing-nova --strict`. Verificação: tudo passa, e os resultados ficam anotados aqui.
  - Resultados: 551 testes OK, `reflex compile` OK e `openspec validate --strict` OK.
  - O cálculo de contraste mostrou que o `#168447` dá só 4,4:1 sobre o creme. A etiqueta “COMECE POR AQUI”, o “Ver mais...” e os links de `/explorar` passaram a usar `#166B3B` (6,1:1), e o design (decisão 7) foi atualizado.
- [x] 6.3 (manual) No navegador, em 1512 px e 360 px, com e sem sessão, conferir:
  - a home comparada com `docs/design/16-landing-nova.png`;
  - os dois números reais;
  - o menu da conta pelo mouse e pelo teclado;
  - cada link do menu, dos cartões, do “Ver mais...” e do rodapé (as rotas futuras dão “não encontrada”);
  - a busca com e sem filtros chegando a `/explorar` com o resumo certo;
  - nenhuma rolagem horizontal fora do carrossel;
  - o foco visível.

  Verificação: os itens anotados aqui.
  - **1ª rodada (Higor), parcial:** OK no menu da conta (Minhas doações, Editar perfil e Sair), nos números 8 e 0, no “Ver mais...” e na busca Roupas + SP chegando a `/explorar`.
  - **Ajuste depois da 1ª rodada:** o título passou a seguir o nó `615:2345` do Figma (Bold 36 px, altura normal, `#2A2A2A`, 1376 px, `clamp` abaixo disso). Os números passaram a seguir os nós `615:2341` a `615:2344` (24 px e 16 px, `#005723`).
  - **Ajustes pedidos pelo grupo:**
    - os números centralizados na altura dos cartões;
    - os cartões das recentes entre 220 e 260 px (`clamp`);
    - a linha dos números e do carrossel nas bordas do cabeçalho (até 1200 px), com a coluna dos números em 11rem.
  - **2ª rodada (Higor):** roteiro OK. Em 1512 px: cabeçalho, título como no Figma, números alinhados, os 4 cartões cabendo, “Ver mais...”, “Comece por aqui”, busca chegando a `/explorar` com os filtros, cartões institucionais, rodapé e menu da conta. Em 360 px, sem rolagem horizontal.
- [x] 6.4 Montar a lista de caminhos para o commit; o Higor roda o `git diff --stat` e confere. Verificação: entram só os 16 caminhos abaixo. Os outros `.xs` modificados pelo pull não entram. Verificado em 27/11/2026: chegou à `main` pelo PR #98 (merge b7d2eb4). O `git show --name-status` mostra exatamente os caminhos listados abaixo: `count_GET.xs` como único `.xs`, os 3 módulos, os 5 testes, o script, os 3 docs e a change arquivada; os únicos extras são as specs principais em `openspec/specs/`, atualizadas pelo arquivamento.
  - Xano: `xano/api/catalog/catalog/donations/count_GET.xs`.
  - Frontend: `doafacil/doafacil.py`, `doafacil/cartoes_doacao.py` e `doafacil/explorar.py` (novo).
  - Testes: `tests/test_public_home.py`, `tests/test_explore.py` (novo), `tests/test_login.py`, `tests/test_my_donations.py` e `tests/test_chat.py`.
  - Script: `scripts/teste_landing_real.py` (novo).
  - Docs: `docs/design/README.md`, `docs/design/16-landing-nova.png` (novo, com os 4 cartões cobertos) e `docs/guia-do-colaborador.md`.
  - OpenSpec: `openspec/changes/landing-nova/` (proposal, design, tasks, `.openspec.yaml` e os 7 deltas em `specs/`).
