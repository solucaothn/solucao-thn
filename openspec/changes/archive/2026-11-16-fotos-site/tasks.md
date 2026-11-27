# Tarefas

Os comandos `git` e `xano` são feitos pelo Higor. Esta change não mexe no Xano. As próximas fotos (blocos verdes do Sobre nós e 4 cartões da home) entram depois, como novas seções desta lista, por `/opsx:update`.

## 1. Componente, conversão e foto da `/quem-somos`

- [x] 1.1 Criar `scripts/converter_fotos.py` (decisão 5) e um teste dele num diretório temporário: JPEG, mesmo tamanho, canto transparente virando branco e sem metadados. Verificação: o teste passa.
  - Resultado: `tests/test_converter_fotos.py` com 2 testes OK.
- [x] 1.2 Converter `assets/sobre/quem-somos.png` para `assets/sobre/quem-somos.jpg`. Verificação: o `.jpg` tem 750 × 842, não tem EXIF e o tamanho em KB fica anotado aqui.
  - Resultado: 750 × 842, sem EXIF nem ICC; 98 KB (o PNG tinha cerca de 935 KB).
- [x] 1.3 Criar o componente `_photo` em `doafacil/institucional.py` (decisão 1) e usá-lo na `about_page`, com `/sobre/quem-somos.jpg`, o `alt` da decisão 3, o crédito “Foto: Freepik” e `max-width: 375px`. Verificação: os testes da 1.5.

## 2. Foto da `/seguranca`

- [x] 2.1 Converter `assets/seguranca/seguranca.png` para `assets/seguranca/seguranca.jpg` e medir o raio dos cantos no PNG. Verificação: o `.jpg` tem o tamanho do PNG (esperado 1014 × 678), não tem EXIF, e o raio e o tamanho em KB ficam anotados aqui.
  - Resultado: 1014 × 678, sem EXIF nem ICC; 89 KB (o PNG tinha cerca de 920 KB). Raio de cerca de 32 px no PNG, ou seja, 16 px na tela.
- [x] 2.2 Na `security_page`, trocar o `_placeholder` pela foto `/seguranca/seguranca.jpg`, com `aspect-ratio` 507/339, `max-width: 507px`, o `alt` escrito ao ver a foto e o crédito “Foto: Freepik” (origem informada pelo Higor; decisões 2 a 4). Remover o `_placeholder` e o `PLACEHOLDER_GRADIENT`, que ficam sem uso. Verificação: os testes da 3.1.
  - Resultado: o raio passou a ser um parâmetro do componente (8 px na Quem somos e 16 px na Segurança).

## 3. Testes, documentação e verificação automatizada

- [x] 3.1 Atualizar `tests/test_institucional.py` (decisão 6):
  - `src`, `alt`, `object-fit`, `aspect-ratio` e crédito nas duas páginas;
  - nenhum placeholder nas duas;
  - os JPEGs no tamanho 2x e sem EXIF;
  - o contraste AA do crédito.

  Verificação: os testes passam.
- [x] 3.2 Atualizar `docs/design/README.md`: as fotos da Quem somos e da Segurança no lugar do placeholder, com os créditos, na lista das páginas e na tabela de diferenças do Figma, e como converter fotos novas com o script. Verificação: o texto bate com a spec delta.
- [x] 3.3 Rodar `python -m unittest discover -s tests`, `reflex compile` e `openspec validate fotos-site --strict`. Verificação: tudo passa, e os resultados ficam anotados aqui.
  - Resultados: 638 testes OK, `reflex compile` OK e `openspec validate --strict` OK.

## 4. Verificação manual e commit

- [x] 4.1 (manual, Higor) No navegador, abrir a `/quem-somos` e a `/seguranca` no desktop e com a janela estreita. Verificar:
  - as fotos aparecem sem distorção, com os cantos arredondados e sem canto branco ou duplo;
  - as fotos estão na proporção do Figma;
  - o crédito aparece pequeno logo abaixo de cada foto.

  Verificação: os itens anotados aqui.
  - Resultado (Higor): `/quem-somos` e `/seguranca` com as fotos sem distorção, cantos arredondados sem canto branco e o crédito “Foto: Freepik” abaixo, também a 360 px.
- [x] 4.2 Montar a lista de caminhos para o commit (decisão 7), sem os `.png`; o Higor confere com o `git diff --stat`. Verificação: entram só os caminhos da decisão 7. Verificado em 27/11/2026: chegou à `main` pelo PR #103 (merge 5f0bb76), com exatamente os caminhos da decisão 7 (`git show --name-status`); os únicos extras são as specs principais em `openspec/specs/`, atualizadas pelo arquivamento. O `git log --all` dos dois `.png` não retorna nenhum commit, então eles nunca foram versionados.
  - Resultado parcial: a lista foi entregue; falta a conferência do Higor.
