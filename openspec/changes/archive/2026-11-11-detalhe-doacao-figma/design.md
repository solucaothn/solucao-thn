# Design

## Contexto

- **Página atual** (`doafacil/detalhe_doacao.py`, `_donation_content`):
  - **Linha de cima:** uma grade de duas colunas. À esquerda, a capa (440 px) e as miniaturas embaixo, com `wrap`. À direita, um cartão branco com o título, “Condição: …”, os botões e a mensagem de contato.
  - **Linha de baixo:** “Detalhes” como lista de rótulo em negrito e texto (Descrição, Categoria, Forma de entrega e Preferência de contato), “Localização” com “Cidade, UF” e o cartão “Quem doa”.
  - **Botão principal:** `#00A859` com texto branco, cerca de 2,9:1, abaixo de AA.
- **Dados do detalhe** (`_parse_donation_detail`): `id`, `title`, `condition`, `description`, `category`, `city`, `state`, `delivery_method`, `contact_preference`, `donor_first_name` e `photos`. Não há `created_at` nem `status`; o endpoint só devolve doações disponíveis.
- **Fotos:** no máximo 5 (`MAX_PHOTOS` no cadastro), sem repetição, com a imagem genérica quando não há nenhuma.
- **Figma** (lido pelo MCP, frames `337:812` `detalhes-doacao-inteira` e `246:576` `detalhes-doacao-1`, 1512 px de largura):
  - **Galeria:** capa de 474×470 e grade 2×2 de 261×227, com 16 px entre as fotos.
  - **“Painel de compra”:** 407 px, branco, borda `#d9d9d9`, raio 8 e sombra `0 8px 13px rgba(0,0,0,.15)`. Tem o título em 45 px, “Estado: …”, o botão verde `#007d32` em pílula de 63 px e o botão “Chat” branco com borda `#85858d`.
  - **Título:** abaixo da galeria, em LINE Seed JP Bold de 24 px e caixa alta.
  - **Descrição:** em LINE Seed JP de 20 px.
  - **“Detalhes”:** título de 24 px. Cada atributo tem um ícone verde de 18 px, o rótulo de 10 px e o valor de 14 px (medium), com recuo de 32 px, em grade de 4 colunas de cerca de 240 px.
  - **“Localização”:** entre divisórias `#d9d9d9`, com o título de 24 px, a ilustração de edifícios verde de 56 px e duas linhas (16 px `#2a2a2a` e 14 px `#556786`).
  - **“Card do anunciante”:** branco, borda `#d9d9d9` e raio 8.
  - **Voltar:** o Figma põe “Voltar ao início” na linha do logotipo, em `#6de29c`.
  - **Fontes:** o Figma usa Roboto nos textos de interface; o projeto usa LINE Seed JP em tudo.

## Objetivos / Fora do escopo

**Objetivos:** a página com a mesma disposição, hierarquia e cores do Figma, só com os dados atuais, mantendo a acessibilidade e o celular.

**Fora do escopo:** o Xano, novos dados, o cabeçalho e o estado ou cliente da página.

## Decisões

1. **Só os componentes mudam.** `DonationDetailState`, `_parse_donation_detail`, o fluxo de contato, os estados de carregamento e erro e o `_back_link` não mudam. A troca é feita dentro de `_donation_content` e em funções pequenas novas, como `_gallery`, `_summary_card`, `_detail_item`, `_details_section`, `_location_card` e `_donor_card`.

2. **Galeria como no Figma.**
   - **No computador (`md` em diante):** uma grade com a capa à esquerda e, à direita, até 4 miniaturas em 2 colunas, como `rx.foreach(photos[1:5])`. As fotos usam `object_fit="cover"`, raio de 8 px e fundo `#EEEEEE` enquanto carregam.
   - **Com 1 foto:** a capa ocupa a largura da galeria.
   - **No celular:** a capa vem em cima e as miniaturas abaixo, em 2 colunas.
   - **`alt`:** a capa recebe o título; as miniaturas, “Foto da doação”, como hoje.

3. **Duas colunas no computador**, como no Figma (cerca de 2,6 : 1):
   - **à esquerda:** a galeria, o título, a descrição, “Detalhes” e “Localização”;
   - **à direita:** o cartão de resumo e, abaixo dele, o cartão “Quem doa”.

   **No celular, em uma coluna:** galeria → resumo → título e descrição → Detalhes → Localização → Quem doa. Assim os botões de contato ficam perto do topo.

4. **Cartão de resumo:**
   - **Caixa:** branco, borda `#D9D9D9`, raio de 8 px, sombra `0 8px 13px rgba(0,0,0,0.15)` e espaçamento de 40/20/32 px.
   - **Título:** cerca de 2,4 rem no computador e 1,8 rem no celular, em `#2A2A2A`.
   - **Condição:** “Condição: …” em `#2A2A2A`. O rótulo do Figma é “Estado”, mas a spec pede “Condição”.
   - **Botão principal:** pílula de 56 px, fundo **`#007A42`** e texto branco em negrito; o hover é `#006B39`, como no chat. É o verde AA do projeto, perto do `#007d32` do Figma.
   - **Botão “Chat”:** branco, borda `#85858D` e texto `#2A2A2A`.
   - **Mensagem de contato:** igual à de hoje.

5. **Título e descrição abaixo da galeria.**
   - **Título:** `rx.heading` em LINE Seed JP Bold, de 1,5 rem, preto, com `text_transform="uppercase"`. A caixa alta é só visual, como no Figma, e o texto lido continua o original.
   - **Descrição:** 1,1 rem no computador e 1 rem no celular, em `#222222`, com `white_space="pre-wrap"`.

6. **Seção “Detalhes”.**
   - **Título:** “Detalhes” em 1,5 rem.
   - **Grade:** 4 colunas no computador, 2 no `sm` e 1 numa largura de 360 px, se o texto não couber. Assim nada é cortado.
   - **Cada item:** o ícone verde de 18 px (`aria-hidden`), o rótulo e o valor. O rótulo tem **0,75 rem** (12 px) em `#555555`, e não os 10 px do Figma, para ficar legível. O valor tem 0,95 rem, peso 600 e cor `#2A2A2A`.
   - **Os 4 itens, nesta ordem:** Categoria, Condição, Forma de entrega e Preferência de contato.

7. **Seção “Localização”.** É um cartão branco com borda `#D9D9D9` e raio de 8 px, como o usuário pediu, no lugar das divisórias do Figma.
   - **Título:** “Localização”.
   - **Linha:** a ilustração de 56 px (`aria-hidden`) e uma só linha “Cidade, UF” em 1 rem, peso 600 e cor `#2A2A2A`.
   - **Sem a segunda linha do Figma** (zona, UF e CEP), que não existe aqui.

8. **Cartão “Quem doa”.** Tem o visual do “Card do anunciante”: branco, borda `#D9D9D9` e raio de 8 px. Mostra o primeiro nome em 1,2 rem, peso 600 e cor `#001C3C`, e o ícone `map-pin` com “Cidade, UF” em `#001C3C`. Não tem foto, “Online”, data de cadastro nem os outros itens.

9. **Ícones do Figma.** Serão baixados durante o apply com `curl -L` a partir das URLs do `get_design_context`, que valem 7 dias; se tiverem expirado, o MCP é chamado de novo.
   - **Arquivos:** o “Ícone de atributo” (`05740.svg`) vira `assets/detalhe-atributo.svg` e a “Localização/Ilustração de edifícios” (`f4e9f.svg`) vira `assets/detalhe-localizacao.svg`.
   - **Uso:** os dois ficam decorativos (`alt=""` e `aria-hidden`), com o tamanho original preservado.
   - **Ícone `map-pin`:** no cartão de quem doa, vem do `rx.icon` (Lucide), igual ao do Figma.

10. **Cores e fontes.**
    - **Fundo:** o creme do projeto, `#FFF6E8`, e não o `#FFF9ED` do Figma.
    - **Fonte:** LINE Seed JP em tudo, como no resto do site, no lugar da Roboto do Figma.
    - **Cores de texto:** `#2A2A2A`, `#555555` e `#001C3C` passam de 7:1 sobre branco e creme.

11. **Itens do Figma que não entram** (decisão do grupo): Cor, Material e Tipo não existem no cadastro. Bairro, zona e CEP ficam fora por privacidade: a localização pública é só cidade e UF. O cartão do anunciante fica sem foto, “Online”, data de cadastro, avaliações, histórico, verificações e perfil. Nada aparece como “Em breve”.

12. **Animação.** `page-fade-enter` continua só no conteúdo estático, como hoje. Os novos títulos de seção (“Detalhes” e “Localização”) usam a mesma classe; os dados do Xano não animam.

13. **Testes** (`tests/test_donation_detail.py`):
    - a galeria com a capa e no máximo 4 miniaturas, com 1 foto e com 5;
    - a ordem das seções e os 4 itens da grade com rótulo e valor;
    - a localização só com cidade e UF, sem bairro e sem CEP;
    - o botão principal em `#007A42`;
    - os ícones decorativos com `aria-hidden`;
    - os breakpoints de 360 px;
    - os testes existentes de conteúdo aprovado, de itens excluídos e do “Voltar” continuam valendo.

14. **Foto única** (ajuste pedido pelo Higor depois do roteiro 4.2). Com 1 foto, ou só a imagem genérica, a capa usa `object_fit="contain"`, centralizada, com o fundo neutro `#EEEEEE` nas sobras e a mesma altura de antes (300/470 px). Nada é cortado. Com várias fotos, a galeria continua com `cover`.

15. **Visualizador de fotos** (ajuste pedido pelo Higor):
    - **Estado:** `viewer_open`, `viewer_index` e `viewer_zoomed` em `DonationDetailState`, zerados no `load_donation`.
    - **Eventos:**
      - `open_viewer(index)`, `close_viewer` e `set_viewer_open` (o `on_open_change` do diálogo);
      - `next_photo` e `prev_photo`, que dão a volta e voltam o zoom a 1x;
      - `toggle_zoom`;
      - `viewer_key_down`, que trata ← e →; o Esc fica com o diálogo. Nesta versão do Reflex, o `on_key_down` só existe em campos de formulário e no `rx.window_event_listener`. Por isso o ouvinte da janela fica dentro do conteúdo do diálogo: ele só existe com o modal aberto, e nenhuma tecla vai ao servidor fora do visualizador.
      - Com 1 foto, trocar de foto não faz nada.
    - **Componente:** `rx.dialog` do Radix, que já prende o foco, fecha com Esc e devolve o foco ao fechar.
      - O conteúdo fica preso às bordas visíveis (`position: fixed`, `inset: 0`, 100% de largura e altura, sem o `100vw` que soma a barra de rolagem), e um clique no fundo fecha.
      - **Fundo (segunda rodada do roteiro):** creme `rgba(255, 246, 232, 0.85)` com `backdrop-filter: blur(6px)` (e o prefixo `-webkit-`). O Radix pinta um véu escuro no `::before` do overlay; um `<style>` dentro do conteúdo, que só existe com o modal aberto, deixa esse véu transparente só quando o overlay contém `.detail-viewer`.
      - Textos e ícones em `#1F1F1F`, acima de 15:1 sobre o creme, bem acima do AA.
      - A foto, os botões e o contador param a propagação do clique, para não fechar o visualizador.
    - **Cabeçalho:** altura fixa de 80 px (16 + botão de 48 + 16), com o `rx.dialog.title` (contador “N de M”), a descrição curta (só no computador) e o X a 16 px da borda direita.
    - **Foto:** fica dentro de um botão com rótulo “Ampliar foto” ou “Reduzir foto”.
      - Em 1x: `object-fit: contain`, com altura máxima `calc(100dvh - 80px - 16px)` (abaixo do cabeçalho, com 16 px embaixo) e largura máxima `calc(100vw - 32px)` no celular ou `calc(100vw - 160px)` no computador, onde sobra espaço para as setas.
      - Em 2x: o dobro dessas larguras (`calc(200vw - 64px)` e `calc(200vw - 320px)`) dentro de uma área com `overflow: auto`, para mover com a rolagem.
      - `touch-action: pinch-zoom` deixa o celular usar a pinça do navegador.
    - **Botões:** “Fechar” (X), “Foto anterior” (‹) e “Próxima foto” (›), com 48×48 px, fundo branco, sombra leve (`0 2px 8px rgba(0, 0, 0, 0.18)`), ícone `#1F1F1F` e contorno de foco visível. O ‹ e o › ficam a 16 px das laterais, no meio da área da foto (`top: calc(50% + 40px)`); no celular passam por cima da foto. Só existem com mais de uma foto.
    - **Galeria:** a capa e cada miniatura viram `rx.el.button` sem estilo próprio, com rótulos como “Ampliar foto 1 de 5”. Assim abrem com o clique, o Enter ou o Espaço.
    - **Animação:** nenhuma própria; o diálogo do Radix já respeita o `prefers-reduced-motion` do tema.
    - **Requisições:** nenhuma; as fotos já estão no estado.

## Riscos / Trade-offs

- **Fidelidade e legibilidade:** o rótulo de 12 px em vez de 10 px e a LINE Seed JP em vez da Roboto mudam um pouco o visual, mas seguem o resto do site e o contraste AA.
- **Títulos longos** em caixa alta ocupam mais espaço. O `overflow-wrap: anywhere` evita quebrar o layout.
- **Assets do Figma:** a URL temporária pode expirar antes do apply. Se o MCP não devolver mais o arquivo, usa-se o ícone Lucide mais próximo (`layout-grid` e `building-2`), e isso é registrado no README.
- **Branch:** a parte B da `chat-visto-edicao` está sem commit nesta branch e também mexe em `doafacil/doafacil.py` e em `docs/design/README.md` (veja a dúvida 1).

## Dúvidas respondidas pelo Higor

1. **Branch:** corrigida. A `feat/detalhe-doacao-figma` parte da `main` atualizada, já com a `chat-visto-edicao` integrada.
2. **“NOVO” e status:** não aparecem no detalhe.
3. **Título:** fica nos dois lugares, como no Figma: no cartão de resumo e abaixo da galeria.
4. **Caixa alta no título de baixo:** só visual, via CSS (`text-transform: uppercase`).
5. **Link “Voltar”:** vai para a linha do logotipo como “Voltar ao início”, igual ao chat e ao Figma.
   - Usa o mesmo cabeçalho do chat: `back_home_header()` em `doafacil/chat.py`, reaproveitado pelo detalhe.
   - Seta verde `#166B3B`, com o texto escondido em telas estreitas e o rótulo acessível “Voltar ao início”.
   - Muda o requisito “Botão Voltar do detalhe” na spec delta.
6. **Ícones:** os SVGs do Figma estão em `assets/detalhe-atributo.svg` (18×18) e `assets/detalhe-localizacao.svg` (56×56).
