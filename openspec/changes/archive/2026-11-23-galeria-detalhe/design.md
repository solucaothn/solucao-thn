# Design: galeria-detalhe

## Context

Hoje `_gallery` (em `doafacil/detalhe_doacao.py`) monta duas peças: a capa num botão e, se houver mais de uma foto, uma caixa à parte com as miniaturas (`photos[1:5]`) em `repeat(2, 1fr)`. No computador a galeria tem duas colunas iguais (capa | miniaturas), cada uma com 470 px de altura. É essa caixa de miniaturas em duas colunas fixas que quebra com 2 e 3 fotos. No celular a capa tem 300 px e as miniaturas ficam em 2 colunas de 140 px.

A quantidade de fotos só é conhecida no navegador (é estado do Reflex), então o arranjo precisa vir de valores reativos, não de `if` em Python.

## Goals / Non-Goals

**Goals:**
- Um arranjo por quantidade (1 a 5), com 16 px de espaço e cantos de 8 px iguais em todas as fotos no computador, e 8 px de espaço no celular.
- Manter as alturas de hoje: 470 px no computador e capa de 300 px no celular.

**Non-Goals:**
- Mexer no visualizador, no estado das fotos, no parser ou no restante da página.
- Criar um arquivo CSS novo ou mexer em `doafacil.py`.

## Decisions

1. **Uma grade só, com `grid-template-areas`.** Todas as fotos (até 5) viram filhos diretos de uma única grade, e cada uma recebe a área `a`…`e` pela posição. O arranjo muda só no contêiner (`gridTemplateColumns`, `gridTemplateRows`, `gridTemplateAreas`). Com isso o espaço entre todas as fotos é o mesmo `gap`, o que não acontecia com a caixa de miniaturas aninhada. Alternativa descartada: uma subgrade por caso, que repete o problema de espaçamentos diferentes entre a capa e as miniaturas.

2. **Arranjo escolhido por `rx.match` sobre a quantidade.** Um `@rx.var` `gallery_size` no `DonationDetailState` devolve `min(len(photos), 5)`; `rx.match` escolhe as colunas, as linhas e as áreas de cada caso. No computador (altura total de 470 px):

   | Fotos | Colunas | Áreas |
   |---|---|---|
   | 1 | `1fr` | `'a'` |
   | 2 | `1fr 1fr` | `'a b'` |
   | 3 | `2fr 1fr` | `'a b' 'a c'` |
   | 4 | `1fr 1fr` | `'a b' 'c d'` |
   | 5 | `1fr 1fr 1fr 1fr` | `'a a b c' 'a a d e'` |

   Com duas linhas, cada uma usa `minmax(0, 1fr)`, então as duas fotos empilhadas somam a altura da capa. Todas as colunas usam `minmax(0, …)` para não alargar a página. O caso de 5 dá a capa com metade da largura e a 2x2 ao lado, como hoje.

3. **Celular: capa em cima e fileira de 4 posições.** No `initial` (abaixo de `md`), a grade tem sempre 4 colunas `minmax(0, 1fr)`, áreas `'a a a a' 'b c d e'` e linhas `300px auto`. As miniaturas são quadradas (`aspect-ratio: 1 / 1`) e têm o mesmo tamanho com 1, 2, 3 ou 4 miniaturas, alinhadas à esquerda. Em 360 px (328 px úteis) cada miniatura tem cerca de 76 px. Com uma foto só, a grade fica com a área `'a a a a'` e a linha de 300 px.

4. **`cover` de 2 a 5 fotos, `contain` na foto única.** Com uma foto só, `rx.cond(gallery_size > 1, "cover", "contain")` mantém a imagem inteira, centralizada, com o fundo `#EEEEEE` nas sobras, como hoje. Com mais fotos, o `cover` deixa a grade sem sobras.

5. **Os botões continuam como estão.** Cada célula é o `_photo_open_button` de hoje, que abre o visualizador no índice da foto, com o rótulo “Ampliar foto N de M”. Um único `rx.foreach` sobre `photos[0:5]` gera todas as células; o texto alternativo é o título na capa e “Foto da doação” nas demais, como hoje. `_gallery_thumbnail` passa a ser `_gallery_photo`, a célula usada para todas as posições.

## Risks / Trade-offs

- [Doação com mais de 5 fotos vinda do Xano] → `gallery_size` limita a 5 e o `foreach` só renderiza `photos[0:5]`, como o `MAX_THUMBNAILS` de hoje. O visualizador continua passando por todas.
- [Testes que leem o JS renderizado ficam frágeis] → Os testes conferem os valores das áreas e das colunas de cada caso e a contagem de botões, não a string inteira.
