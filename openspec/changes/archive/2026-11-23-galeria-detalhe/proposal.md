# Proposta: galeria do detalhe que se adapta à quantidade de fotos

## Why

No detalhe da doação, a galeria usa sempre a mesma estrutura (capa à esquerda e uma grade fixa de duas colunas à direita). Com 2 e 3 fotos ela quebra: com 2, a segunda foto ocupa só meia coluna; com 3, as duas fotos de apoio ficam finas e compridas. Uma doação pode ter de 1 a 5 fotos, e a galeria precisa ficar equilibrada em todos os casos.

## What Changes

- A galeria do detalhe passa a ter um arranjo por quantidade de fotos, com cantos arredondados e espaçamento iguais entre todas as fotos:
  - 1 foto: uma foto grande, com a altura atual da capa;
  - 2 fotos: lado a lado, do mesmo tamanho;
  - 3 fotos: a capa à esquerda com 2/3 da largura e duas fotos empilhadas à direita, com a mesma altura total da capa;
  - 4 fotos: grade 2x2;
  - 5 fotos: a capa à esquerda e as outras 4 em 2x2 à direita (como hoje).
- Com 2 a 5 fotos, todas usam `object-fit: cover`. A foto única continua inteira (`contain`), com fundo neutro nas sobras, como hoje.
- Em 360 px: a capa em cima, na largura toda, e as demais numa fileira de miniaturas do mesmo tamanho logo abaixo, sem rolagem horizontal da página.
- Toda foto continua sendo um botão que abre o visualizador naquela foto, com o mesmo rótulo acessível de hoje.

## Capabilities

### New Capabilities

(nenhuma)

### Modified Capabilities

- `donation-detail`: o cenário de layout da galeria no computador muda, o de foto única ganha a largura toda da galeria, e entra um cenário para a galeria em 360 px. A ordem das fotos, o visualizador e o restante da página não mudam.

## Impact

- `doafacil/detalhe_doacao.py`: só `_gallery`, `_gallery_thumbnail` e as constantes da galeria. O visualizador, o resumo e o restante da página ficam como estão.
- `tests/test_donation_detail.py`: os testes da galeria mudam para o novo arranjo.
- Sem mudança no Xano, nas APIs, em dependências ou em outras páginas.

## Fora do escopo

- Visualizador de fotos, ordem das fotos, limite de 5 fotos, cadastro e edição de fotos.
- Qualquer outra parte do detalhe (resumo, título, detalhes, localização, cartão de quem doa) e as outras páginas.
