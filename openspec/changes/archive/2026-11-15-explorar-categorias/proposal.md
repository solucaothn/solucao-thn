# Proposal

## Why

A busca da home já leva a `/explorar` com `q`, `categoria` e `uf`, mas a página ainda é provisória e não mostra doação nenhuma. O menu “Categorias” aponta para uma rota que não existe. O Figma (`docs/design/17-explorar.png`, `18-categorias-01.png` e `18-categorias-02.png`) define as duas telas, e falta no Xano uma busca pública que aplique os três filtros e pagine.

## What Changes

- **Parte A, Xano:** um endpoint público e só de leitura, `GET catalog/donations/search`.
  - Filtros `q` (no título ou na descrição), `category_id` e `state` (UF), todos opcionais, e `page`, com 12 por página.
  - Só doações disponíveis, da mais nova para a mais antiga.
  - Os mesmos campos de cartão do `recent` (id, data, título, foto e condição), com `page`, `per_page`, `total` e `page_total`.
  - O `GET catalog/donations` antigo não muda: ele devolve doações de qualquer status, sem foto nem paginação, e pode ter outros consumidores.
  - Push só desse arquivo, com `-i` e dry-run antes.
- **`/explorar` de verdade**, no lugar da página provisória:
  - cabeçalho do Figma, com busca por texto, seletor de UF, lupa, “Quero Doar” e “Entrar” (ou o menu da conta);
  - “Voltar ao início”;
  - o título conforme os filtros: “Adicionadas recentemente”, “Categoria “Roupas”” ou “Resultados para “cadeira””, com a UF quando houver;
  - a grade de cartões, o botão “Carregar mais” (12 por vez) e o estado vazio, com o link “Limpar filtros”;
  - os parâmetros `q`, `categoria` e `uf` continuam os mesmos.
- **Categorias:**
  - o item “Categorias” do menu da home passa a abrir a **gaveta** do Figma, com as categorias reais do Xano, ícone e seta, fechando com X, Esc ou clique fora;
  - a rota **`/categorias`** passa a existir, como página com a mesma lista, para links diretos e para o celular, onde o menu da home não aparece;
  - cada categoria leva a `/explorar?categoria=<id>`, que mostra o título “Categoria “Roupas””, como na tela 476:2478.
- **360 px:** sem rolagem horizontal da página. A grade passa a uma coluna, e o cabeçalho da `/explorar` empilha a busca.

Diferenças em relação ao Figma, detalhadas na decisão 8 do `design.md`:

| No Figma | Na implementação |
|---|---|
| “Estado: Ótimo” nos cartões | “Condição: Ótimo”, o termo do domínio |
| a gaveta lista “Móveis” | as categorias do Xano, com as exclusões do cadastro (Alimentos e Móveis) |
| setas de “expandir” (subcategorias) na gaveta | seta de “ir”, porque não há subcategorias |
| `/explorar` sem filtro com a seção “Da categoria “Roupas”” | só a lista geral (seções por categoria fora do escopo) |
| grade fixa de 5 cartões de 245 px | grade flexível (cartões de 220 a 260 px; uma coluna em 360 px) |
| “Voltar ao inicio” | “Voltar ao início” (acento) |

## Capabilities

### New Capabilities

- `donation-categories`: a gaveta e a página `/categorias`, com as categorias do backend levando à `/explorar` filtrada.

### Modified Capabilities

- `donation-explore`: a página provisória é substituída pela listagem real, com filtros, “Carregar mais”, estado vazio e cabeçalho com busca.
- `public-donation-discovery`: requisito novo, a busca pública paginada de doações disponíveis.
- `public-home`: o item “Categorias” do menu passa a abrir a gaveta, em vez de ir para `/categorias`.
- `donation-chat-interface`: o botão flutuante do chat passa a aparecer em `/explorar` (como no Figma) e em `/categorias`, e a `/explorar` sai da lista de páginas sem o botão.

## Impact

- **Xano:** só o arquivo novo `xano/api/catalog/catalog/donations/search_GET.xs`. Nenhuma tabela muda.
- **Frontend:**
  - `doafacil/explorar.py` reescrito, e `doafacil/categorias.py` novo;
  - em `doafacil/doafacil.py`, o menu e a rota `/categorias`;
  - o menu da conta sai de `doafacil.py` para um módulo compartilhado (`doafacil/cabecalho.py`), porque a `/explorar` também o usa;
  - o cartão em grade (`donation_grid_card`) é reaproveitado.
- **Testes:** `tests/test_explore.py` (reescrito), `tests/test_categories.py` (novo) e os testes da home afetados pelo menu.
- **Docs:** `docs/design/README.md` (as telas 17 e 18 e as diferenças) e `docs/guia-do-colaborador.md`. Os PNGs já estão em `docs/design/`.
- **Fora do escopo:**
  - seções por categoria na `/explorar` sem filtro;
  - subcategorias;
  - ordenação diferente da data;
  - a gaveta nas outras páginas;
  - as rotas futuras que não são `/categorias`.
