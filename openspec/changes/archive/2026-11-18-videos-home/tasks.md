# Tarefas

Os comandos `git` e `xano` são feitos pelo Higor. Esta change não mexe no Xano e é separada da `navegacao-celular`, que continua aberta.

## 1. Arquivos e cartões

- [x] 1.1 Criar o teste dos arquivos (decisão 4): cada `.mp4` de `assets/landing/` é H.264 (`avc1`), sem faixa de áudio, tem no máximo 8 s e 490 × 490; cada capa `.jpg` tem 490 × 490. Verificação: o teste passa; se algum arquivo não passar, parar e avisar o Higor, sem converter nada.
  - Resultado: `tests/test_videos_home.py` OK. Os quatro vídeos são H.264, sem áudio e de 490 × 490, com 8,0 s (`solidariedade`, `seguranca` e `passo-a-passo`) e 7,3 s (`missao`); as capas são JPEG de 490 × 490.
- [x] 1.2 Trocar `image` e `placeholder` de `INSTITUTIONAL_CARDS` por `video` e `poster`, e montar o cartão com a capa de fundo, o `rx.el.video` (atributos da decisão 1), o véu e o conteúdo por cima. Remover o `_institutional_background`. Verificação: os testes da 1.4.
- [x] 1.3 Movimento reduzido (decisão 2): criar `assets/home.css` com a regra que esconde os vídeos, adicioná-lo ao `stylesheets` e pôr o script de pausa no `on_mount` da seção. Verificação: os testes da 1.4.
- [x] 1.4 Atualizar `tests/test_public_home.py` (decisões 3 e 5):
  - atributos do vídeo, `aria-hidden`, `tabIndex` e sem `controls`;
  - véu e capa;
  - textos e ícones iguais;
  - sem degradê;
  - movimento reduzido (CSS, `stylesheets` e `on_mount`);
  - medidas em 360 px;
  - contraste AA do branco sobre o véu nas capas.

  Verificação: os testes passam; um véu ajustado fica anotado aqui.
  - Véu ajustado: com o véu antigo (transparente a 35% e 0,72 embaixo), as capas de “Nada se perde” e “Doar leva minutos” davam 2,2:1 e 3,4:1.
    O novo é transparente até 30%, 0,5 em 55% e 0,8 embaixo, e dá 9,0, 9,8, 4,9 e 7,0:1. É o mais leve entre os testados que passa nas quatro.
  - Os testes de eventos da home (`tests/test_public_home.py` e `tests/test_login.py`) passam a aceitar o `on_mount` da seção.

## 2. Documentação e verificação automatizada

- [x] 2.1 Atualizar o `docs/design/README.md`: a seção da home e a tabela de diferenças do Figma dizem “vídeo próprio com capa”, e não mais degradê, e citam o movimento reduzido. Verificação: o texto bate com a spec delta.
- [x] 2.2 Rodar `python -m unittest discover -s tests`, `reflex compile` e `openspec validate videos-home --strict`. Verificação: tudo passa, e os resultados ficam anotados aqui.
  - Resultados: 710 testes OK, `reflex compile` OK e `openspec validate --strict` OK.

## 3. Verificação manual e commit

- [x] 3.1 (manual, Higor) No navegador, em 1512 px, 768 px e 360 px. Verificação: os itens anotados aqui.
  - Os quatro vídeos tocam sozinhos, sem som e em repetição, sem distorcer e com os cantos arredondados.
  - O texto fica legível em todo o vídeo.
  - Com “reduzir movimento” ligado no sistema, ou emulado no DevTools (Rendering → `prefers-reduced-motion`), aparece só a capa.
  - Num celular, os vídeos tocam dentro da página, sem tela cheia.
  - Não há rolagem horizontal em 360 px.
  - O resto da home fica igual.
  - Rodada 1 (Higor): OK nos 4 cartões (vídeos tocando, texto legível, cantos certos).
    - Problema no Edge: ao passar o mouse, apareciam os controles do navegador (picture-in-picture e “pular”), e clicar neles tirava o vídeo da página, que travava.
    - Corrigido no `<video>` com `disablePictureInPicture`, `disableRemotePlayback`, `controlsList` e `pointer-events: none`, coberto em `tests/test_public_home.py` (710 testes OK e `reflex compile` OK).
    - Falta conferir de novo no Edge.
  - Rodada 2 (Higor): OK no Edge; ao passar o mouse, nenhum controle do navegador aparece.
- [ ] 3.2 Montar a lista de caminhos para o commit (decisão 6); o Higor confere com o `git diff --stat`. Verificação: entram só esses caminhos.
