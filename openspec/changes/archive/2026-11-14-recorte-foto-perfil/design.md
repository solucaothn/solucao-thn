# Design: recorte-foto-perfil

## Contexto

O motivo da change está em `proposal.md`. Abaixo fica o estado atual que define a abordagem.

- **Fluxo atual** (`doafacil/editar_perfil.py`):
  - o `rx.upload` de “Alterar foto” tem `accept` (os formatos do cadastro de doação), `max_files=1` e `max_size` de 5 MB;
  - o `on_drop` chama `upload_photo(rx.upload_files(...))`, que lê o arquivo no servidor do Reflex, confere de novo o formato (extensão e tipo) e o tamanho com `validate_photo_file` e envia na hora com `upload_profile_photo` (multipart, campo `photo`);
  - um arquivo recusado pela tela chama `photo_rejected`, sem requisição.
- **Mensagens atuais:** `PHOTO_FORMAT_MESSAGE`, `PHOTO_SIZE_MESSAGE`, `PHOTO_MISSING_MESSAGE`, `PHOTO_ERROR_MESSAGE` e `PHOTO_SAVED_MESSAGE`. Os 400 do Xano são traduzidos por `_photo_rejection_message`.
- **Xano:** o `POST /auth/profile/photo` guarda com `storage.create_image` e confere o `mime` e o tamanho do arquivo guardado. Ele não muda.
- **Reflex 0.9.12** (verificado no `.venv`):
  - existe `rx.NoSSRComponent`, para envolver componentes React que usam `window`;
  - existe `reflex.experimental.client_state.ClientStateVar` (também `rx._x.client_state`), uma variável que vive só no navegador e pode ser alterada por eventos do próprio componente, sem ida ao servidor. A API é experimental;
  - `rx.dialog` (Radix) prende o foco e fecha com `Esc`;
  - `rx.slider` (Radix) tem suporte a teclado.
- **Pillow:** não está instalado no `.venv` nem no `requirements.txt`.
- **Nenhum componente React próprio** foi envolvido no projeto até agora (nenhum `library =`).

## Objetivos e não objetivos

**Objetivos:**

- Enviar só a área enquadrada, num quadrado de 512 × 512 px, pelo endpoint atual.
- Arrastar e dar zoom de forma fluida, também no celular, sem ida ao servidor a cada movimento.
- Manter as validações e as mensagens atuais.
- Corrigir a orientação EXIF e remover os metadados.
- Manter o recorte em funções puras, testáveis sem navegador.

**Não objetivos:**

- Girar, espelhar ou filtrar a imagem.
- Recortar fotos de doações.
- Mudar o Xano.
- Reenquadrar a foto já enviada.

## Decisões

### 1. `react-easy-crop` envolvido como `NoSSRComponent`

Módulo novo `doafacil/recorte_foto.py`:

```python
class ImageCropper(rx.NoSSRComponent):
    library = "react-easy-crop@<versão fixa>"   # confirmada na tarefa 1.1
    tag = "Cropper"
    is_default = True
    image: rx.Var[str]
    crop: rx.Var[dict]          # {x, y}, ligado a um ClientStateVar
    zoom: rx.Var[float]         # ligado a um ClientStateVar
    aspect: rx.Var[float]       # 1
    crop_shape: rx.Var[str]     # "round"
    show_grid: rx.Var[bool]     # False
    min_zoom / max_zoom / zoom_speed / keyboard_step
    restrict_position: rx.Var[bool]   # True: a imagem cobre sempre a moldura
    on_crop_change / on_zoom_change: ligados aos ClientStateVar
    on_crop_complete: rx.EventHandler[lambda area, pixels: [pixels]]
```

- **Arraste e zoom só no navegador:** o `crop` e o `zoom` ficam em `ClientStateVar`s. O `on_crop_change` e o `on_zoom_change` chamam os setters deles, sem evento no servidor. O controle deslizante de zoom usa o mesmo `ClientStateVar`.
- **Servidor só no fim do gesto:** só o `on_crop_complete`, que o `react-easy-crop` dispara no fim de cada gesto, vai ao estado (`set_crop_area`). Ele leva o `croppedAreaPixels` (`x`, `y`, `width`, `height`, em pixels da imagem mostrada).
- **`restrict_position=True` e `min_zoom=1`:** a imagem sempre cobre a moldura. Isso cumpre o cenário “sem área vazia”.
- **Por que `NoSSRComponent`:** o `react-easy-crop` lê o tamanho do elemento e da janela no navegador.

**Alternativas consideradas:**

- *`crop` e `zoom` em variáveis do estado do servidor:* cada movimento do mouse viraria um evento pela websocket. Seria lento no celular e geraria dezenas de eventos por segundo. Recusada.
- *Recortar no navegador com `<canvas>`:* exigiria JavaScript próprio para gerar o arquivo e ainda mandaria ao servidor um arquivo sem a validação do Pillow (EXIF, metadados, bombas de descompressão). Recusada.
- *Uma moldura feita só com CSS e eventos do Reflex:* não há eventos de ponteiro contínuos sem ida ao servidor. Recusada.

**Resultado da prova técnica (tarefa 1.1): foi usado o plano B.**

- **Versão:** `react-easy-crop@6.2.4`, publicada em 2026-10-06. A 6.2.5 tinha só 5 dias e ficou de fora. As props `cropShape`, `restrictPosition`, `zoomWithScroll`, `keyboardStep`, `cropperProps`, `minZoom`/`maxZoom` e `onCropComplete(area, pixels)` foram conferidas no `index.d.ts` do pacote.
- **Setas:** o próprio pacote trata as setas na área de enquadramento, que tem `tabIndex=0` e emite a área no `keyup`. **`+` e `-` não são tratados por ele.**
- **Por que não o `ClientStateVar`:**
  - no Reflex 0.9.12, um `on_key_down` só extrai a tecla (`key_event`) e manda o evento ao servidor. Não há como filtrar `+` e `-` no navegador sem escrever JavaScript;
  - o `ClientStateVar` é experimental, e o arraste com ele não pôde ser comprovado sem um navegador.
- **O que foi feito:**
  - um componente local `assets/recorte/image_cropper.jsx` guarda o `crop` e o `zoom` em `useState`, trata `+` e `-`, desenha o controle “Zoom” (`input type=range`) e os botões “Diminuir zoom” e “Aumentar zoom”, e chama `onCropComplete` só com os `croppedAreaPixels`;
  - ele é envolvido em `doafacil/recorte_foto.py` (`ImageCropper`, `NoSSRComponent`, `library = "$/public/recorte/image_cropper.jsx"`, `lib_dependencies = ["react-easy-crop@6.2.4"]`).
- **Conferido:**
  - o `reflex compile` gera `ClientSide(() => import('$/public/recorte/image_cropper.jsx'))`;
  - o `package.json` do `.web` recebe o `react-easy-crop` 6.2.4;
  - o `reflex export --frontend-only --no-zip` gera o pedaço `image_cropper-*.js` com o CSS da moldura redonda.
  - O arraste, a pinça e o teclado no navegador ficam para o roteiro 5.3.
- **Nomes das funções:** no código, `crop_square` ficou dividida em `crop_box` (a caixa, com escala e limites) e `encode_square` (512 × 512, formato e sem metadados).

**Plano B, como foi proposto (aprovado na 1.2 e usado):** um componente local mínimo em `assets/` (`rx.asset(..., shared=True)`), envolvido do mesmo jeito. Ele guarda o `crop` e o `zoom` em `useState` e expõe só o `on_crop_complete` e o `zoom`. É um arquivo `.jsx` pequeno e entra no projeto como componente do Reflex, mas o grupo precisa aprovar antes (dúvida 3).

### 2. Fluxo no estado (`EditProfileState`)

1. O `on_drop` passa a chamar **`prepare_crop(files)`**:
   - lê o arquivo;
   - aplica as mesmas validações de hoje (`validate_photo_file`);
   - abre com o Pillow (`prepare_source`, decisão 3), sem nenhuma requisição ao Xano.
   - Erro de formato ou tamanho: as mensagens atuais, sem abrir o modal.
   - Imagem ilegível: a mensagem de formato.
   - Sucesso:
     - guarda o original já reorientado numa **variável de backend** (`_crop_source: bytes`, `_crop_format: str`), que começa com `_` e por isso não vai ao navegador;
     - guarda a **prévia** em `crop_preview` como `data:` URL, reduzida para no máximo 1024 px no lado maior;
     - guarda o tamanho da prévia e abre o modal (`crop_open = True`).
2. **`set_crop_area(pixels)`** guarda a área recebida do `on_crop_complete`, em pixels da prévia.
3. **`cancel_crop`** (botão “Cancelar”, `Esc` ou clique fora) limpa tudo e fecha o modal, sem requisição.
4. **`confirm_crop`** (“Usar foto”):
   - converte a área para as coordenadas do original (decisão 4);
   - gera o quadrado de 512 px (`crop_square`);
   - fecha o modal;
   - envia com o `upload_profile_photo` atual, com `photo_busy`, as mensagens e o tratamento de 401 e 429 de hoje;
   - limpa as variáveis do recorte em qualquer caso.
5. **O `upload_photo` atual sai.** O envio passa a acontecer só pelo `confirm_crop`.

O `photo_rejected` (arquivo recusado pela própria tela) não muda.

### 3. Abertura e preparação da imagem (`prepare_source`, função pura)

- Usa `Image.open` dentro de `try`. `UnidentifiedImageError`, `OSError` e `Image.DecompressionBombError` levam à mensagem de formato.
  - Os casos de tamanho absurdo levam à mensagem de formato, e não a uma mensagem nova, para manter as mensagens atuais.
  - O limite `Image.MAX_IMAGE_PIXELS` fica em 40 milhões de pixels, para evitar bombas de descompressão.
- O formato real vem do Pillow (`image.format`), e não da extensão. Um arquivo `.png` que na verdade é JPEG segue como JPEG.
- `ImageOps.exif_transpose` corrige a orientação, e só depois vêm a prévia e o recorte.
- GIF: usa o primeiro quadro (`seek(0)`).
- Converte para `RGB`, ou para `RGBA` quando há transparência e o formato de saída aceita.

### 4. Recorte (`crop_square`, função pura)

- **Entrada:** a imagem já reorientada, a área `{x, y, width, height}` em pixels da prévia e a escala `original / prévia`.
- **Conversão:** multiplica pela escala e arredonda.
- **Limites:**
  - força o quadrado (usa o menor lado da área);
  - limita a área à imagem, deslocando-a para dentro sem mudar o tamanho;
  - se o lado for maior que a imagem, reduz até o menor lado da imagem.
  - Largura ou altura menor que 1 pixel, ou valores não numéricos ou infinitos, geram um erro (`CropAreaError`), e a tela mostra `PHOTO_ERROR_MESSAGE` sem enviar.
- **Saída:**
  - `crop` e `resize((512, 512), Image.LANCZOS)`. Uma área menor que 512 px também é ampliada, para que todas as fotos tenham o mesmo tamanho;
  - salva sem metadados (sem `exif=` nem `icc_profile` de origem), conforme a tabela abaixo.

  | Original | Saída | Arquivo enviado |
  |---|---|---|
  | JPEG | JPEG, qualidade 90, `RGB` | `foto.jpg`, `image/jpeg` |
  | PNG | PNG otimizado, mantém a transparência | `foto.png`, `image/png` |
  | WEBP com algum pixel transparente | PNG otimizado, mantém a transparência | `foto.png`, `image/png` |
  | WEBP sem transparência | JPEG, qualidade 90, `RGB` | `foto.jpg`, `image/jpeg` |
  | GIF | PNG (primeiro quadro) | `foto.png`, `image/png` |

  Esta tabela já tem a regra do WEBP da decisão 4a. A versão inicial mantinha o WEBP como WEBP.

- O nome do arquivo enviado é fixo (`foto.<ext>`), e o nome original não sai do navegador para o Xano.

### 4a. WEBP nunca é enviado como WEBP (depois do teste real 5.2)

- **O que aconteceu:** no `teste_recorte_foto_real.py`, o RC4 (“WEBP continua WEBP”) falhou, e todos os outros cenários passaram.
  - O envio foi aceito, e o download deu HTTP 200 e abriu como imagem. Mas o arquivo entregue no fim do redirecionamento (303) não era WEBP, ou não tinha 512 × 512. O RC1 mostrou que o Xano não muda o tamanho.
- **O que foi conferido do nosso lado:**
  - o Pillow do `.venv` tem suporte a WEBP (`features.check("webp")` é `True`);
  - para uma entrada WEBP, o código da época gerava `foto.webp`, `image/webp`, com a assinatura `RIFF…WEBP`, lido de volta como WEBP de 512 × 512.
  - O código não era a causa.
- **Causa não confirmada:** sem as credenciais e as URLs do Xano neste ambiente, não deu para ver o que ficou guardado. Sobraram duas hipóteses:
  - (A) o `storage.create_image` converte o WEBP ao guardar (a documentação do MCP não fala em conversão);
  - (B) o servidor de arquivos troca o formato na entrega, conforme o cabeçalho `Accept`, que no script era `*/*` e num navegador inclui `image/webp`.
  - Um diagnóstico que separaria as duas foi preparado, mas o Higor decidiu não rodá-lo, e ele foi apagado.
- **Decisão (Higor):** independentemente da causa, o WEBP é convertido **antes do envio**: para **PNG** quando algum pixel tem transparência (`alpha < 255`), mantendo a transparência, e para **JPEG** quando não tem. Um WEBP com canal alfa, mas todo opaco, vira JPEG.
- **Motivo:** assim o resultado não depende do comportamento do Xano nem do servidor de arquivos. O que é enviado é sempre JPEG ou PNG, formatos que funcionaram em todos os cenários do teste real.
- **Efeitos:**
  - o Xano continua aceitando WEBP. A regra vale só para a foto de perfil enquadrada no site;
  - a spec (“Formato do resultado”), a tabela da decisão 4, os testes unitários e o RC4 do script foram atualizados. O RC4 agora é “WEBP sem transparência vira JPEG”, e o RC4b, novo, é “WEBP com transparência vira PNG com transparência”.

### 5. Modal (`_crop_dialog`)

- **Estrutura:** `rx.dialog.root` controlado por `crop_open`, com `on_open_change` que chama `cancel_crop` ao fechar.
  - Título “Ajustar foto”.
  - Texto de ajuda: “Arraste para posicionar. Use o controle, a roda do mouse ou a pinça para o zoom.”
- **Área de enquadramento:**
  - um quadrado responsivo (`width: 100%`, `aspect-ratio: 1`, até 400 px) com o `ImageCropper` dentro, `position: relative`;
  - fundo `#1F1F1F` fora da moldura, que é o padrão do `react-easy-crop`;
  - envolvida por um elemento focável (`tabIndex=0`) com o rótulo acessível “Área de enquadramento. Use as setas para mover e as teclas mais e menos para o zoom.”
- **Teclado:**
  - as setas usam o suporte do próprio `react-easy-crop` (`keyboardStep`), a confirmar na tarefa 1.1;
  - `+` e `-` usam um `on_key_down` que altera o `ClientStateVar` do zoom, também a confirmar na tarefa 1.1. Se não der, entram os botões do item abaixo, sempre presentes.
- **Zoom:**
  - um `rx.slider` (1 a 3, passo 0,1) com o rótulo “Zoom”;
  - dois botões redondos de 44 px, “Diminuir zoom” e “Aumentar zoom”, com os ícones `minus` e `plus`.
- **Botões:**
  - “Cancelar”, com contorno `#85858D`;
  - “Usar foto”, com fundo `#007A42` e texto branco. Fica desativado até o primeiro `on_crop_complete`.
- **Largura:** `min(480px, calc(100vw - 32px))`, sem rolagem horizontal em 360 px.
- **Sem animação de entrada própria:** é um modal, não uma página. O Radix já respeita `prefers-reduced-motion`.

### 6. Dependências

- **`Pillow`:** instalado no `.venv` com `pip` e fixado no `requirements.txt`, na versão instalada.
- **`react-easy-crop`:** a versão exata vai no `library` do componente. O Reflex a instala no `.web` na compilação. A tarefa 1.1 confirma a versão e as props (`keyboardStep` e `restrictPosition`).

### 7. Testes

- **`tests/test_profile_photo_crop.py`** (novo), com imagens geradas na memória:
  - **coordenadas:** uma imagem com quatro quadrantes de cores diferentes. O recorte de cada quadrante dá 512 × 512 da cor certa, e a escala da prévia para o original é aplicada;
  - **EXIF:** imagens com orientação 3, 6 e 8 saem na orientação certa, conferida pela cor de um canto, e sem EXIF;
  - **limites:**
    - área com `x` ou `y` negativos, ou além da largura;
    - área maior que a imagem;
    - área não quadrada;
    - área nula, NaN ou infinita (`CropAreaError`);
  - **formatos:** JPEG, PNG com transparência, WEBP→JPEG (sem transparência), WEBP→PNG (com transparência) e GIF→PNG, com o `mime` e a extensão certos. Nenhuma saída é WEBP (decisão 4a);
  - **arquivos ruins:** bytes que não são imagem e uma imagem acima do limite de pixels dão a mensagem de formato;
  - **prévia:** no máximo 1024 px e com a escala certa.
- **`tests/test_edit_profile.py`** (ajustes nos testes de upload):
  - o `prepare_crop` com arquivo válido abre o modal sem chamar o `upload_profile_photo`;
  - arquivos inválidos mostram as mensagens atuais e não abrem o modal;
  - o `cancel_crop` limpa tudo sem requisição;
  - o `confirm_crop` envia os bytes do recorte e mantém o formulário;
  - os erros de envio (400, 401, 429 e rede) se comportam como hoje;
  - o modal tem os rótulos, a largura máxima, os botões de 44 px e o `crop_shape="round"`.
- **`scripts/teste_recorte_foto_real.py`** (novo, no padrão do `teste_foto_perfil_real.py`):
  - usa as funções do recorte e o `upload_profile_photo` de verdade contra o Xano;
  - não imprime nomes, e-mails, URLs nem corpos de resposta;
  - restaura a foto original no fim.

  | Cenário | O que confere |
  |---|---|
  | RC1 | uma imagem de quatro quadrantes enviada com o recorte do quadrante superior direito vira 512 × 512 e tem a cor desse quadrante (baixada pela URL devolvida) |
  | RC2 | uma foto JPEG com orientação EXIF 6 sai em pé |
  | RC3 | um PNG com transparência continua PNG com transparência |
  | RC4 | um WEBP sem transparência vira JPEG (decisão 4a; antes era “um WEBP continua WEBP”) |
  | RC4b | um WEBP com transparência vira PNG com transparência |
  | RC5 | um GIF vira PNG |
  | RC6 | os metadados de localização do original não aparecem no arquivo baixado |
  | RC7 | o `GET auth/profile` traz a URL nova |
  | RC8 | depois de todos os envios, a foto original volta (restauração) |

## Riscos e trade-offs

- **`ClientStateVar` é experimental** → a tarefa 1.1 confirma o funcionamento antes de tudo. Se não funcionar, vale o plano B (dúvida 3).
- **A prévia em `data:` URL passa pela websocket** (até cerca de 300 kB para 1024 px em JPEG) → aceitável para um evento só. O original de até 5 MB nunca vai ao navegador.
- **O original fica na memória do servidor do Reflex** enquanto o modal está aberto → é limpo em “Usar foto”, “Cancelar”, num erro e ao carregar a página de novo. Com várias sessões, são até 5 MB por sessão por pouco tempo.
- **Ampliar áreas menores que 512 px deixa a imagem menos nítida** → é o preço de um tamanho único. As fotos de celular costumam ser bem maiores.
- **GIF animado perde a animação** → dúvida 1.
- **Uma nova dependência de frontend** (`react-easy-crop`) → é um componente React envolvido pelo mecanismo do próprio Reflex, sem trocar a tecnologia de frontend. A versão fica fixa.
- **O Xano continua sendo a validação de segurança.** O recorte é conveniência e não substitui a checagem do `mime` e do tamanho do endpoint.

## Plano de migração

- Não há dados para migrar. Fotos já enviadas continuam como estão.
- Reversão: voltar o `on_drop` para o `upload_photo` antigo e remover o modal e o módulo. O Xano não muda.

## Dúvidas para o grupo (tarefa 1.2)

1. **GIF:** virar PNG estático, com o primeiro quadro (proposta), ou manter GIF de um quadro?
2. **Tamanho do resultado:** 512 × 512 sempre, ampliando áreas menores (proposta), ou nunca ampliar e enviar o lado da área quando ele for menor que 512?
3. **Plano B:** se o `ClientStateVar` não funcionar com o `react-easy-crop`, vocês aprovam um pequeno componente `.jsx` local em `assets/`, envolvido pelo Reflex? Ou preferem o `crop` no estado do servidor, mesmo mais lento?
4. **Zoom máximo:** 3× (proposta) ou outro valor?

### Respostas (tarefa 1.2)

As decisões foram tomadas pelo Higor com o Claude, sem consulta ao grupo.

1. **GIF:** vira PNG estático, com o primeiro quadro.
2. **Tamanho:** sempre 512 × 512, ampliando áreas menores.
3. **Plano B aprovado:** se a prova técnica da 1.1 falhar, o componente `.jsx` local envolvido pelo Reflex entra direto, sem nova consulta.
4. **Zoom máximo:** 3×.
5. **Metadados e nome do arquivo:** aprovados a remoção de todos os metadados, inclusive a localização GPS, e o nome fixo `foto.<ext>` no envio.
