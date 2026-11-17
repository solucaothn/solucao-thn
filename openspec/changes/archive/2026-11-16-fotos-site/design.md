# Design

## Context

**Placeholder atual.** A `/quem-somos` e a `/seguranca` usam `_placeholder(...)` em `doafacil/institucional.py`: um `rx.box` decorativo com degradê, cantos de 16 px, `aria-hidden` e altura fixa. A altura é de 200 e 421 px na Quem somos e de 180 e 339 px na Segurança.

**Figma:**
- **Quem somos (354:851):** “Rectangle 15”, de 375 × 421.
- **Segurança (406:1243):** “image 16”, de 507 × 339.

**Arquivos do Higor:**
- `assets/sobre/quem-somos.png`: 750 × 842 (2x), RGBA, com os cantos transparentes. O raio é de cerca de 16 px no arquivo, ou seja, 8 px na tela. Pesa cerca de 940 KB.
- `assets/seguranca/seguranca.png`: 1014 × 678 (2x de 507 × 339), RGBA, com os cantos transparentes. O raio é de cerca de 32 px no arquivo, ou seja, 16 px na tela. Pesa cerca de 920 KB.

## Goals / Non-Goals

**Goals:**
- Um componente de foto com crédito, usado pelas duas páginas e pelas próximas fotos desta change.
- A foto nunca distorce e nunca deixa espaço vazio.
- Arquivos leves, sem metadados.

**Non-Goals:**
- Mudar o layout do resto das páginas.
- Fazer imagens responsivas com vários tamanhos (`srcset`).

## Decisions

### 1. Componente `_photo(src, alt, credit, width, height, radius)`

Os dados de cada foto ficam num dicionário (`ABOUT_PHOTO`, `SECURITY_PHOTO`). A proporção e a largura máxima vêm de `width` e `height`, o retângulo do Figma.

- **Estrutura:** um `rx.el.figure` com um `rx.image` e, quando houver crédito, um `rx.el.figcaption`.
- **Imagem:**
  - `width: 100%`, `aspect-ratio` do retângulo do Figma e `object-fit: cover`;
  - `border-radius` igual à metade do raio medido no PNG 2x (8 px na Quem somos e 16 px na Segurança), com `overflow: hidden`;
  - `display: block`.
- **Alternativa descartada:** manter as alturas fixas do placeholder. No celular elas cortam a foto numa faixa, e a foto deixa de ter o formato do Figma.
- O `_placeholder` e o `PLACEHOLDER_GRADIENT` saem, porque ficam sem uso.

### 2. Tamanho e posição

- **Quem somos:** a figura fica na coluna da direita (`0.9fr`), com `max-width: 375px`, alinhada à direita no desktop e centrada no celular.
- **Segurança:** a figura fica na coluna da direita (`1fr`), com `max-width: 507px`, com o mesmo alinhamento.
- A altura vem do `aspect-ratio`.

### 3. Texto alternativo

- **Quem somos:** “Grupo de jovens agachados no chão de um escritório, sorrindo e apontando para papéis com gráficos.”
- **Segurança:** “Cinco jovens sorrindo, de pé em fila num escritório claro, usando fones de ouvido com microfone.”
- Os dois descrevem a cena, sem nomes nem suposições sobre as pessoas.

### 4. Crédito

- **Formato:** “Foto: <origem>”, em `0.75rem` e na cor `TEXT_MUTED` sobre o branco, com `margin-top: 6px`. O crédito é texto puro, sem link.
- **Quem somos:** “Foto: Freepik”.
- **Segurança:** “Foto: Freepik”. O Higor informou a origem Freepik.
- O crédito é um parâmetro do componente. Uma foto própria pode vir sem ele.

### 5. Conversão para JPEG

- **Script versionado:** `scripts/converter_fotos.py <png> [<png>...]`, reaproveitável nas próximas fotos.
  - Usa o Pillow, que já está no `requirements.txt`.
  - Grava o `.jpg` ao lado do PNG, com o mesmo nome e o mesmo tamanho em pixels.
  - Usa `quality=82`, `optimize=True` e `progressive=True`.
  - Não copia EXIF, ICC nem texto do PNG.
- **Cantos:** a imagem é composta sobre o branco (`#FFFFFF`, o fundo das páginas) antes de virar RGB. Os cantos que eram transparentes ficam brancos e são cobertos pelo `border-radius` de 8 px do CSS, que tem o mesmo raio do arquivo.
- **PNGs:** os originais ficam na pasta, mas não entram no commit. A lista do commit cita só os `.jpg`.
  - Também não adiciono uma regra no `.gitignore`: o projeto já versiona PNG em `assets/` (`ilustracao-rodape.png`).
- **Alternativa descartada:** WebP. É menor, mas o pedido foi JPEG, que todo navegador abre.

### 6. Testes

Em `tests/test_institucional.py`:
- cada página renderiza o `src` `.jpg`, o `alt`, `object-fit: cover`, `aspect-ratio` e o `figcaption` com o crédito;
- nenhuma das duas tem mais o `institutional-photo-placeholder`;
- os `.jpg` existem, são JPEG, têm o tamanho 2x do Figma e não têm EXIF;
- o contraste do crédito passa no AA.

Um teste do script converte um PNG pequeno com cantos transparentes, num diretório temporário, e confere:
- o formato JPEG;
- o tamanho em pixels;
- o canto branco;
- a ausência de metadados.

### 7. Commit (para a lista final)

Entram:
- `assets/sobre/quem-somos.jpg` e `assets/seguranca/seguranca.jpg`;
- `scripts/converter_fotos.py`;
- `openspec/changes/fotos-site/`;
- `doafacil/institucional.py`;
- `tests/test_institucional.py` e o teste do script;
- `docs/design/README.md`.

Não entram os dois `.png`.

## Risks / Trade-offs

- **[Licença]** O crédito vem da origem que o grupo informa. → Se uma origem mudar, é preciso trocar um parâmetro só.
- **[PNG em `assets/` é publicado pelo Reflex]** Enquanto o PNG estiver na pasta, ele também vai para o build local. → Como ele não entra no commit, não vai para o repositório. Depois do commit, o Higor pode mover os PNGs para fora de `assets/`.
- **[Canto duplo]** Pode aparecer se o raio do CSS não bater com o do arquivo. → O raio de cada foto é medido no arquivo, e os cantos brancos ficam escondidos.

## Migration Plan

Mudança só no frontend. O rollback é reverter pelo `git`.
