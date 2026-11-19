# Design

## Context

- **Hoje:** `doafacil/doafacil.py` tem os quatro cartões em `INSTITUTIONAL_CARDS`, com `category`, `title`, `icon`, `image` (sempre `None`) e `placeholder`, um degradê. O `institutional_card` monta um `rx.box` quadrado:
  - `aspect-ratio: 1`;
  - largura de 100% no celular (até 320 px), metade em `sm` e um quarto em `lg`;
  - cantos de 16 px e `padding` de 16 px;
  - o fundo vem do `_institutional_background` (degradê, ou véu + imagem quando houver uma);
  - o conteúdo (ícone em círculo verde, rótulo e título `h3`) fica embaixo, em branco.
- **Véu escuro:** `INSTITUTIONAL_VEIL` (`rgba(0,0,0,0)` a 35% até `rgba(0,0,0,0.72)` embaixo).
- **Figma:** o nó 655:2691 (Frame 18) não foi encontrado no arquivo do Figma ligado ao projeto (`l4MoQJUROh7b7gY3vCFTC0`). As medidas seguem o pedido do Higor (245 × 245, cantos, ícone em círculo verde, rótulo e título por cima do gradiente escuro), que já são as do cartão atual.
- **Arquivos** em `assets/landing/`: quatro `.mp4` (cerca de 160 a 270 KB cada) e quatro capas `.jpg` de 490 × 490 (o 2x de 245).
- **Ferramentas:** o projeto não tem `ffprobe`.
- **Movimento reduzido:** as regras do projeto ficam em `assets/auth-card.css` e `assets/chat.css`, carregadas pelo `stylesheets` do app.

## Goals / Non-Goals

**Goals:**
- O vídeo preenche o cartão sem distorcer, e a capa aparece antes, no lugar de um vídeo que falha e com movimento reduzido.
- O texto fica legível sobre qualquer quadro: o véu escuro fica sempre por cima do vídeo.
- Nenhuma mudança nos textos, na ordem, no tamanho e na disposição dos cartões.

**Non-Goals:**
- Controles de vídeo, som e legendas: os vídeos são decorativos e não têm fala.
- Tocar só quando o cartão aparece na tela (`IntersectionObserver`). O navegador já pausa vídeos mudos fora da tela.

## Decisions

### 1. Estrutura do cartão

O `rx.box` do cartão ganha `position: relative` e `overflow: hidden`. Por baixo, o fundo é a capa (`url(<capa>) center / cover`). Por cima, três camadas:
1. **Vídeo:** `rx.el.video` absoluto em `inset: 0`, com 100% × 100%, `object-fit: cover`, `src` do `.mp4`, `poster` da capa, `autoplay`, `muted`, `loop`, `playsInline` e `preload="metadata"`.
   - Também tem `aria-hidden="true"`, `tabIndex=-1`, nenhum `controls` e a classe `home-institutional-video`.
   - **Sem controles do navegador** (3.1, Edge): ao passar o mouse, o Edge mostrava picture-in-picture e “pular”, e clicar neles tirava o vídeo da página, que travava. O vídeo ganha:
     - `disablePictureInPicture` e `disableRemotePlayback`;
     - `controlsList="nodownload nofullscreen noremoteplayback noplaybackrate"`;
     - `pointer-events: none`.

     O cartão continua como antes: não navega e não tem evento.
2. **Véu:** um `rx.box` absoluto em `inset: 0`, com o `INSTITUTIONAL_VEIL` e `aria-hidden`.
3. **Conteúdo:** ícone, rótulo e título, como hoje, com `position: relative` e `z-index: 1`.

- **Dados:** `INSTITUTIONAL_CARDS` troca `image` e `placeholder` por `video` (`/landing/<nome>.mp4`) e `poster` (`/landing/<nome>.jpg`). O `_institutional_background` sai.
- **Alternativa descartada:** vídeo como imagem de fundo via CSS. Isso não existe para vídeo, e o `poster` resolve a capa.

### 2. Movimento reduzido: CSS e pausa no carregamento

O `autoplay` não pode ser tirado por CSS, então são duas camadas:
1. **CSS:** uma folha nova, `assets/home.css`, adicionada ao `stylesheets`, com `@media (prefers-reduced-motion: reduce) { .home-institutional-video { display: none; } }`.
   - O cartão mostra a capa, que é o seu fundo, sem nenhum quadro de movimento.
2. **Script na montagem da seção** (`on_mount` com `rx.call_script`): com `matchMedia('(prefers-reduced-motion: reduce)')`, tira o `autoplay` e chama `pause()` em cada `video.home-institutional-video`, para o navegador não ficar decodificando vídeo escondido.
   - Fica no `on_mount` da seção, e não no `on_load` da home, para não mexer nos eventos de carregamento da home nem nos testes deles.
- **Alternativa descartada:** tirar o `autoplay` e tocar por script. Contraria o pedido (`<video autoplay …>`) e deixa os cartões parados se o script falhar.

### 3. Legibilidade

- O véu fica sempre acima do vídeo, então o texto nunca fica direto sobre o quadro.
- **Teste automático:** a conferência usa as capas, que representam o vídeo. Na faixa de baixo de cada capa, onde fica o texto (os 45% inferiores), o teste aplica o véu e calcula o contraste do branco com o pixel mais claro do percentil 95. O resultado tem que ser pelo menos 4,5:1 (AA).
- Se alguma capa não passar, o véu escurece o mínimo necessário, e isso fica anotado na tarefa.
- **Resultado na implementação:** o véu de duas paradas não passou na capa de “Nada se perde” (2,2:1), que é clara embaixo. Ficou um véu de três paradas, escuro só na faixa do texto: transparente até 30%, 0,5 em 55% e 0,8 embaixo. O pior caso dá 4,9:1, e o alto do vídeo continua sem véu.

### 4. Conferência dos arquivos sem ffprobe

Um teste lê as caixas do MP4 em Python, sem dependência nova, e confere em cada `.mp4`:
- a caixa `ftyp`;
- a amostra `avc1` (H.264) no `stsd`;
- nenhuma faixa `soun` no `hdlr`, ou seja, sem áudio;
- a duração do `mvhd` (duração ÷ escala) de no máximo 8 s;
- 490 × 490 no `tkhd` da faixa de vídeo.

As capas são conferidas com o Pillow: JPEG de 490 × 490.

### 5. Testes da página

Em `tests/test_public_home.py`:
- cada cartão renderiza um `video` com os atributos pedidos, `aria-hidden` e `tabIndex=-1`, sem `controls`, mais o véu por cima e a capa como fundo;
- os textos e os ícones continuam iguais;
- não sobra nenhum `placeholder` com degradê;
- a regra de movimento reduzido está em `assets/home.css` e no `stylesheets`;
- o script de pausa está no `on_mount` da seção;
- em 360 px, a largura continua 100% com máximo de 320 px;
- o teste antigo de contraste (branco sobre as pontas do degradê) passa a valer para o véu sobre as capas (decisão 3).

### 6. Commit (para a lista final)

Entram:
- `assets/landing/` (os 8 arquivos) e `assets/home.css`;
- `doafacil/doafacil.py`;
- `tests/test_public_home.py`, `tests/test_login.py` (eventos permitidos na home) e `tests/test_videos_home.py`;
- `openspec/changes/videos-home/`;
- `docs/design/README.md`.

## Risks / Trade-offs

- **[Peso: cerca de 870 KB de vídeo na home]** → Com `autoplay`, o navegador baixa o vídeo mesmo com `preload="metadata"`, mas os quatro juntos ainda são menos que uma foto PNG grande. As capas (15 a 26 KB) aparecem primeiro.
- **[Autoplay bloqueado]** → Pode acontecer em economia de dados ou por política do navegador. O cartão fica com a capa, que é o comportamento esperado.
- **[`muted` no React]** → O React aplica o `muted` como propriedade no cliente. Com o `playsInline`, isso é o que o iOS exige para o autoplay. O roteiro manual confere num celular.
- **[Contraste depende do quadro]** → O teste usa as capas, e o véu cobre a faixa do texto em qualquer quadro. Um quadro muito claro no fim do vídeo é conferido no roteiro manual.

## Migration Plan

Mudança só no frontend. O rollback é reverter pelo `git`.
