# Tarefas

Os comandos `git` e `xano` são do Higor. Esta change não toca no Xano.

## 1. Galeria em grade única

- [x] 1.1 Acrescentar `gallery_size` (`@rx.var`, `min(len(photos), 5)`) ao `DonationDetailState` (decisão 2). Verificação: um teste confere 1, 3, 5 e 7 fotos → 1, 3, 5 e 5.
- [x] 1.2 Reescrever `_gallery` como uma grade única com `grid-template-areas` escolhidas por `rx.match` sobre `gallery_size`, com os cinco arranjos do computador e o arranjo do celular (decisões 1 a 3), e trocar `_gallery_thumbnail` por `_gallery_photo`, com `object-fit: cover`, cantos de 8 px e área `a`…`e` pela posição (decisões 4 e 5). Verificação: testes em `tests/test_donation_detail.py` conferem as colunas e áreas de cada quantidade, `2fr 1fr` com 3 fotos, `1fr 1fr 1fr 1fr` com 5, o arranjo `'a a a a' 'b c d e'` com miniaturas quadradas no celular, `minmax(0, …)` nas colunas, `contain` só com uma foto e `cover` de 2 a 5, `photos[0:5]` num único `foreach` e um único botão que abre o visualizador com o rótulo “Ampliar foto N de M”.
- [x] 1.3 Ajustar os testes antigos da galeria que esperavam a capa separada, `contain` na foto única e as miniaturas em `repeat(2, …)`. Verificação: `python -m unittest tests.test_donation_detail tests.test_acabamento` passa.

## 2. Documentação e verificação

- [x] 2.1 Atualizar em `docs/design/README.md` os itens “Galeria” e “Uma foto só” para o novo arranjo. Verificação: o texto bate com a delta (`contain` só na foto única).
- [x] 2.2 Rodar a suíte inteira e compilar o app. Verificação: `python -m unittest discover -s tests` passa e `reflex compile` termina sem erro.
- [ ] 2.3 Roteiro manual (para o Higor): abrir doações com 1, 2, 3, 4 e 5 fotos em tela larga e em 360 px, conferir os arranjos, o espaçamento, a ausência de rolagem horizontal e que cada foto abre o visualizador nela. Parcial em 27/11/2026: doações com 3 e 4 fotos conferidas em tela larga; 1, 2, 5 fotos e 360 px não conferidos formalmente.
