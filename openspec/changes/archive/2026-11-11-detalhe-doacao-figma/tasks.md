# Tarefas

Só frontend: nada muda em `xano/` e não há comandos xano.

## 1. Preparação

- [x] 1.1 (manual) Confirmar com o Higor a dúvida 1 do `design.md`: os arquivos da `chat-visto-edicao` sem commit estão fora desta branch, e a branch parte da `main` atualizada. Verificação: `git status --short -- . ':!xano'` mostra só os artefatos desta change.
- [x] 1.2 Baixar os dois SVGs do Figma (decisão 9) para `assets/detalhe-atributo.svg` e `assets/detalhe-localizacao.svg`, pedindo as URLs de novo ao MCP se tiverem expirado. Verificação: os dois arquivos existem, não estão vazios e têm `width` e `height` na raiz.

## 2. Página

- [x] 2.1 Reorganizar `_donation_content` em duas colunas no computador e uma no celular, na ordem da decisão 3, sem mudar o estado nem o fluxo de contato. Verificação: os testes existentes de `tests/test_donation_detail.py` continuam passando.
- [x] 2.2 Implementar a galeria da decisão 2: a capa e até 4 miniaturas em 2 colunas; a capa sozinha com 1 foto. Verificação: testes com 1 foto e com 5.
- [x] 2.3 Implementar o cartão de resumo da decisão 4, com o botão principal em `#007A42`. Verificação: teste da cor, dos dois botões e da mensagem de contato.
- [x] 2.4 Implementar o título e a descrição abaixo da galeria (decisão 5). Verificação: teste da posição, do `pre-wrap` e da caixa alta só visual.
- [x] 2.5 Implementar a grade “Detalhes” da decisão 6: os 4 itens, o ícone `aria-hidden`, o rótulo de 0,75 rem e as colunas por largura. Verificação: testes dos itens, da ordem e da ausência de Cor, Material e Tipo.
- [x] 2.6 Implementar o cartão “Localização” (decisão 7) e o cartão “Quem doa” (decisão 8). Verificação: testes de “Cidade, UF” sem bairro e sem CEP e do cartão só com o primeiro nome e “Cidade, UF”.
- [x] 2.7 Com 1 foto, mostrar a imagem inteira com `contain`, centralizada, com fundo neutro e a mesma altura (decisão 14). Verificação: teste do `contain` com 1 foto e do `cover` com várias.
- [x] 2.8 Implementar o visualizador de fotos da decisão 15:
  - a abertura pela capa e pelas miniaturas;
  - ‹ ›, as setas do teclado e o contador;
  - o zoom de 1x e 2x com rolagem e a pinça no celular;
  - o fechamento por X, Esc e clique fora;
  - o foco preso, os rótulos e a área de 44 px;
  - sem setas com 1 foto.

  Verificação: testes de estado e de componente.
- [x] 2.9 Ajustar o visual do visualizador (segunda rodada do roteiro, decisão 15):
  - fundo creme `rgba(255, 246, 232, 0.85)` com `blur(6px)`, sem o véu escuro do Radix;
  - textos e ícones em `#1F1F1F`; ‹, › e X brancos com sombra leve;
  - foto em 1x inteira abaixo do cabeçalho de 80 px, sem passar da borda de baixo;
  - X e setas a 16 px das bordas visíveis, em qualquer largura.

  Verificação: teste do fundo, do CSS do overlay, das cores, das alturas máximas e das posições.

## 3. Documentação

- [x] 3.1 Atualizar a seção “Detalhe da doação” do `docs/design/README.md` com:
  - os frames do Figma e o novo layout;
  - as diferenças aprovadas (fonte, rótulo de 12 px, botão `#007A42`, cartão de localização, itens que não entram);
  - a decisão sobre “NOVO” e status.

  Verificação: o texto bate com a spec delta e com o `design.md`.

## 4. Verificação

- [x] 4.1 Rodar `python -m unittest discover -s tests -v` e mostrar `git status` e `git diff --stat`. Verificação: todos os testes passam e nada muda em `xano/`.
- [x] 4.2 (manual) No navegador, comparar `/doacao/<id>` com os frames do Figma no computador (cerca de 1512 px) e no celular (360 px), com uma doação de 1 foto e outra de 5:
  - galeria, resumo, título e descrição;
  - “Detalhes”, “Localização” e “Quem doa”;
  - sem rolagem horizontal;
  - Chat, E-mail e Voltar funcionando.
  - o visualizador: abrir pela capa e por uma miniatura, ‹ ›, setas do teclado, “N de M”, zoom de 1x/2x com rolagem, pinça no celular, X, Esc e clique fora, foco preso; com 1 foto, sem setas;
  - com 1 foto, a imagem inteira, sem corte.

  Verificação: os itens conferidos e anotados.

  Primeira rodada, anotada pelo Higor, antes dos ajustes 2.7 e 2.8: com 5 fotos, a página ficou como ele queria; Voltar, Chat e celular OK. Faltam conferir os itens do visualizador e da foto única.

  Segunda rodada, anotada pelo Higor: o visualizador funciona (abrir, setas, teclado, contador, zoom, fechar e 1 foto). Ele pediu os ajustes visuais da 2.9 (fundo creme com desfoque, foto inteira em 1x, X e setas sem corte) e marcou a 4.2 junto com eles.
