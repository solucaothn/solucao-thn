# Design: fotos-formulario-doacao

## Contexto

O motivo da change está em `proposal.md`. Abaixo fica o estado atual, verificado no código (só leitura em `xano/`).

### Como a ordem e a capa funcionam hoje no Xano

- **`publish_POST.xs`:**
  - recebe `file[]? photos?` (de 1 a 5) e percorre o array **na ordem recebida**;
  - para cada arquivo, faz `storage.create_image` e soma 1 a `$photo_position`;
  - a foto da posição 1 vira `$cover_photo`.
  - Na transação, grava `donation.photo = $cover_photo` e uma linha `donation_photo` por foto, com `position` de 1 a N.
  - A resposta traz `donation` (com o `id` e o `status`) e `photos`.
- **Tabela `donation_photo`:** `donation_id`, `position` e `photo` (`image?`), com índice em `donation_id`.
- **Leitura:**
  - **cartões** (`recent`, `donor`, `mine`): usam `donation.photo`, a capa;
  - **detalhe** (`detail_GET.xs`): primeiro `donation.photo`; depois as `donation_photo` em `sort = {position: "asc"}`, sem repetir o caminho da capa.
- **Conclusão:** a ordem salva é a ordem das partes `photos[]` do multipart, e a capa é a primeira. Basta o frontend enviar na ordem escolhida. **Nenhuma mudança no Xano.**

### O frontend hoje (`doafacil/cadastro_doacao.py`)

- **Passo 3:** um `rx.upload` (`multiple`, `accept` de imagens, `max_files=5`) guarda os arquivos **só no navegador**.
  - A tela lista apenas os **nomes** (`rx.selected_files`), com “Remover todas” (`rx.clear_selected_files`).
  - O Reflex não oferece remover nem reordenar arquivos individuais dessa seleção, nem uma URL de prévia.
  - Escolher de novo **substitui** a seleção.
- **`advance`** (passo 3) e **`publish`** recebem `rx.upload_files(...)`. O `publish` lê os bytes, valida com `_validated_photos` e envia `photos[]` na ordem da seleção do navegador.
- **Sucesso:** `published = True` e `success_message` no passo 5, sem sair da página.
- **Selects:** `_select_field` usa `rx.select(...)` (o atalho de alto nível) com o fundo e a borda no `Root`. Esse estilo não chega ao botão visível (Trigger), que fica cinza.
  - É o mesmo defeito corrigido em `minhas_doacoes._edit_select`, que põe o estilo no `rx.select.trigger`.
  - O `_select_field` serve aos quatro selects do cadastro: Categoria, Condição, Forma de entrega e Preferência de contato.
- **Dependência circular:** `minhas_doacoes.py` importa de `cadastro_doacao.py`. Por isso o cadastro não pode importar o `_edit_select` de `minhas_doacoes.py`.
- **Limites atuais das fotos:**
  - até 5 (no `max_files` e no `_validated_photos`);
  - tipos JPEG, PNG, GIF e WEBP, pela extensão e pelo tipo;
  - **nenhum limite de tamanho** para fotos de doação, nem na tela nem no Xano. O guia registra isso desde a change foto-perfil. Esta change cria o limite de 5 MB na tela (resposta 1).
- **Mensagens atuais:**
  - “Adicione pelo menos uma foto para continuar.”;
  - “Selecione até cinco imagens JPEG, PNG, GIF ou WEBP.”;
  - “Não foi possível ler uma das imagens. Remova-a e tente novamente.”;
  - “Uma das imagens está vazia. Remova-a e tente novamente.”.

## Objetivos e não objetivos

**Objetivos:**

- Miniaturas, remover uma, reordenar sem arrastar e escolher a capa, com a ordem da tela sendo a ordem salva.
- Somar novas escolhas às anteriores, com os limites e as mensagens atuais.
- Selects com fundo branco.
- Depois de publicar, ir para o detalhe com o aviso e o link para “Minhas doações”.
- Nenhuma mudança no Xano.

**Não objetivos:**

- Arrastar para reordenar.
- Recortar ou girar fotos de doação. A orientação EXIF é corrigida automaticamente, mas não há giro manual.
- Editar fotos depois de publicar.
- Mudar os limites no Xano. O limite de 5 MB é só da tela.

## Decisões

### 1. As fotos passam a ficar no servidor do Reflex assim que são escolhidas

O que hoje fica só no navegador não pode ser reordenado nem removido individualmente. Por isso:

- **Envio a cada escolha:** o `rx.upload` passa a enviar cada escolha na hora (`on_drop=DonationCreateState.add_photos(rx.upload_files(...))`), como já faz a seção Foto de “Editar perfil”.
- **`add_photos(files)`:**
  - **valida cada arquivo** com as regras atuais: extensão e tipo (a lógica do `_validated_photos`, agora por arquivo), arquivo vazio e leitura;
  - **limite de 5 MB por foto** (resposta 1):
    - na tela, o `rx.upload` ganha `max_size` de 5 MB, e um arquivo maior é recusado pelo componente (`on_drop_rejected`, código `file-too-large`), sem requisição;
    - no `add_photos`, o tamanho é conferido de novo;
    - nos dois casos, a mensagem é “A foto pode ter no máximo 5 MB.”;
  - **reprocessa a foto com o Pillow na hora** (decisão 4b). Uma imagem ilegível é recusada com a mensagem de formato;
  - **aceita só até completar 5,** na ordem da escolha. Os excedentes e os de tipo inválido são recusados com “Selecione até cinco imagens JPEG, PNG, GIF ou WEBP.”, e as fotos já aceitas ficam como estão;
  - **guarda só a versão reprocessada** (sem metadados, até 1600 px desde a decisão 4c), numa **variável de backend** `_photo_files: dict[str, tuple[bytes, tipo, extensão]]`, que não vai ao navegador. O arquivo como veio do navegador não é guardado (decisão 1a);
  - **guarda no estado** `photos: list[dict]`, com `id` (um identificador aleatório), `thumb` (`data:` URL da miniatura) e `name`;
  - **limpa a seleção do componente** (`rx.clear_selected_files`), para a próxima escolha somar.
- **Arquivos recusados pelo próprio componente:** o `on_drop_rejected` (tipo errado ou mais de 5 numa escolha) mostra a mesma mensagem, sem requisição.
- **Estado de preparo:** enquanto `add_photos` roda, `photos_busy = True` e o texto “Preparando fotos...” aparecem (`role="status"`). Isso cumpre o “progresso enquanto o arquivo é processado” da spec. A área de escolha e “Continuar” ficam desativados.
- **O que vai ao Xano é a versão reprocessada** (decisão 4b), e não o arquivo original.

### 1a. Onde os arquivos ficam e quando são apagados

- **Onde ficam:**
  - na variável de backend `_photo_files` do `DonationCreateState`, dentro do estado da sessão no servidor do Reflex;
  - o projeto não configura Redis (`rxconfig.py` sem `redis_url` e nenhuma variável `REFLEX_REDIS_URL`), então esse estado fica **na memória do processo do servidor do Reflex**. Nada é gravado em disco pelo nosso código, e nada vai ao navegador além das miniaturas (`photos[].thumb`);
  - durante o envio de uma escolha, o Starlette, usado pelo Reflex, pode manter o arquivo recebido num arquivo temporário (`SpooledTemporaryFile`) até o fim do `add_photos`. Ele é fechado e apagado pelo próprio framework.
- **Quando são apagados:**

  | Momento | O que é apagado |
  |---|---|
  | Escolha de uma foto | o arquivo como veio do navegador; só a versão reprocessada é guardada |
  | Remover uma foto | a entrada dela em `_photo_files` |
  | Publicar com sucesso | tudo em `_photo_files` e `photos`, antes do redirecionamento |
  | Reiniciar o cadastro (`load_initial_data`: entrar, recarregar ou trocar de conta) | tudo em `_photo_files` e `photos` |

  - Numa falha de publicação, as fotos ficam, para a pessoa tentar de novo (spec “Falha durante a publicação”).
  - Uma sessão abandonada é descartada quando o Reflex expira o estado dela.
- **Função única de limpeza:** `_clear_photos(state)` zera `photos`, `_photo_files` e `photos_busy`. Os testes conferem os três momentos.

**Alternativas consideradas:**

- *Manter os arquivos no navegador e gerar prévias com `URL.createObjectURL`:* exigiria JavaScript próprio para guardar, reordenar e reenviar os arquivos, porque o Reflex não expõe a lista de `File` da seleção. Recusada: o caminho pelo servidor usa só mecanismos do Reflex e o Pillow, que já é dependência.
- *Mandar a ordem ao Xano num campo novo:* mudaria o endpoint sem necessidade, já que a ordem do envio basta. Recusada.

### 2. Funções puras em `doafacil/fotos_doacao.py`

Para testar sem o Reflex:

- `check_file(name, content_type, size)`: confere o tipo (extensão e tipo) e o tamanho de até 5 MB, e devolve a mensagem atual de erro ou `""`;
- `process_photo(contents)`: o reprocessamento da decisão 4b. Devolve os bytes, o tipo, a extensão e a miniatura de até 240 px (`make_preview`), ou gera `PhotoImageError` para uma imagem ilegível;
- `rejection_message(rejections)`: a mensagem para os arquivos recusados pelo componente (`file-too-large` dá a de tamanho; os outros casos dão a de formato e limite);
- `remove(order, photo_id)`, `move(order, photo_id, delta)` (`-1` ou `+1`, trocando com a vizinha, sem passar das pontas) e `make_cover(order, photo_id)` (leva para a posição 0 e mantém a ordem relativa das outras). As três devolvem uma lista nova.

Os eventos `remove_photo(id)`, `move_photo(id, delta)` e `make_cover(id)` só aplicam essas funções a `photos` e, no `remove`, apagam também a entrada de `_photo_files`. Nenhum deles faz requisição.

### 3. O passo 3 (`_step_three`)

- **Área de escolha:** o mesmo `rx.upload` tracejado, agora com `on_drop` e `on_drop_rejected`.
  - O texto passa a ser “Arraste as imagens para cá ou escolha os arquivos” e “JPEG, PNG, GIF ou WEBP · até 5 fotos · a primeira é a capa”.
  - Com 5 fotos, a área fica desativada e mostra “Limite de 5 fotos atingido”.
  - O ícone verde de imagem passa a `#168447` (AA).
- **Contador:** “N de 5 fotos”, com `aria-live="polite"`.
- **Lista vertical** (o wizard tem até 360 px de largura). Uma linha por foto:
  - a miniatura de 72 px, quadrada, com `object-fit: cover`, cantos de 8 px e o texto alternativo “Foto N de M”;
  - o texto “Foto N” e, na primeira, o selo **“Capa”** (pílula `#E8F5EC` com texto `#166B3B`, 5,8:1, o mesmo par do selo de e-mail verificado);
  - quatro botões de ícone, de 44 × 44 px, com `aria-label` e `title`:

    | Botão | Ícone | Desativado quando |
    |---|---|---|
    | “Mover foto N para a esquerda” | `chevron-left` | é a primeira foto |
    | “Mover foto N para a direita” | `chevron-right` | é a última foto |
    | “Tornar foto N a capa” | `star` | já é a capa |
    | “Remover foto N” | `trash-2`, em `#B42318` | nunca |

  - Os botões quebram para uma segunda linha quando não cabem. Não há rolagem horizontal em 360 px.
- **Rótulos:** os rótulos pedidos (“Remover foto N”, “Mover para a esquerda/direita”, “Tornar capa”) entram com a posição da foto, para o leitor de tela saber qual foto é. O texto visível fica só nos ícones, com o `title`.
- **Foco depois de mover:**
  - mover leva o foco ao mesmo botão da foto, já na posição nova (ids `photo-<id>-left`, `-right` e `-cover`). Se ele ficou desativado (a foto chegou a uma ponta), o foco vai ao botão do outro lado;
  - tornar capa leva o foco a “Mover para a direita”, ou a “Remover” quando só há uma foto;
  - remover leva o foco ao “Remover” da foto que ocupou o lugar ou, se não houver mais fotos, à área de escolha.
  - **No apply:** em vez de `rx.set_focus`, que usa as `refs` do Reflex e não funciona com ids dinâmicos dentro de `rx.foreach`, o evento devolve `rx.call_script` com um `setTimeout(() => document.getElementById(id)?.focus(), 0)`, que roda depois de a lista ser redesenhada.
- **Sem o nome do arquivo:** `photos` guarda só o `id` e a miniatura (`thumb`). O nome original não vai ao estado nem ao Xano.
- **Aviso curto:** cada ação gera um aviso com `role="status"` (“Foto 3 virou a capa.”, “Foto removida.”, “Foto movida para a posição 2.”).
- **Sai:** a lista de nomes e “Remover todas”.
- **Texto do passo:** “Você pode publicar sem fotos.” vira “Adicione de 1 a 5 fotos. A primeira foto é a capa da doação.” (dúvida 2).

### 4. Envio na ordem escolhida

- O `advance` (passo 3) e o `publish` deixam de receber `rx.upload_files`. Eles usam `photos` e `_photo_files`.
- O `publish` monta `[(f"foto-{N}.{ext}", bytes, tipo) for N, foto in enumerate(photos, 1)]` **na ordem de `photos`** e chama o `_publish_donation` atual, que envia `photos[]` nessa ordem. O nome é fixo e numerado, e o nome original do arquivo não sai do servidor do Reflex.

### 4b. Reprocessamento de cada foto antes do Xano (acréscimo)

Feito no `add_photos`, assim que a foto é aceita. Reaproveita `doafacil/recorte_foto.py`:

- `prepare_source(contents)`:
  - abre a imagem e recusa as ilegíveis e as com mais de 40 milhões de pixels (mensagem de formato);
  - usa o 1º quadro do GIF;
  - corrige a **orientação EXIF**;
  - devolve uma imagem nova **sem nenhum metadado**: EXIF, GPS, ICC e textos;
  - resolve o formato de saída pela mesma regra da foto de perfil: **JPEG→JPEG, PNG→PNG, GIF→PNG, WEBP→PNG com algum pixel transparente e JPEG sem**.
- Uma função nova em `recorte_foto.py`, `encode_limited(source, max_side=1600)` (ajustada na decisão 4c; a primeira versão usava 2048 px e JPEG q90):
  - **reduz o lado maior para no máximo 1600 px**, mantendo a proporção, sem ampliar (`thumbnail`);
  - codifica sem metadados: JPEG com qualidade 82 e `optimize` em `RGB`, ou PNG otimizado só quando há transparência real;
  - devolve os bytes, o tipo e a extensão (`jpg` ou `png`).
  - Ela compartilha o código de codificação com o `encode_square`, para não duplicar.
- **A miniatura de 240 px** sai da mesma imagem já reprocessada (`make_preview`).
- **O que se ganha:** o arquivo enviado nunca tem metadados (a localização da câmera não vaza nas fotos públicas), fica sempre em pé, com no máximo 1600 px (decisão 4c), e sempre em JPEG ou PNG. É a mesma garantia da foto de perfil, que evitou o problema do WEBP no Xano.
- **O limite de 5 MB** vale para o arquivo escolhido. O arquivo reprocessado, com até 1600 px, fica bem abaixo disso na prática. O Xano continua sem limite para fotos de doação.
- O `_validated_photos` e a leitura dos bytes no `publish` saem, porque a validação passou para o `add_photos`.
- Os erros e as mensagens da publicação continuam os mesmos. Numa falha, as fotos e a ordem ficam como estavam.

### 4c. Publicação mais rápida (depois do roteiro 7.3)

- **Problema:** publicar 5 fotos demorava muito.
- **Medição** (5 fotos sintéticas com textura, que comprimem um pouco pior que fotos reais):
  - o Pillow roda **na escolha da foto** (`add_photos`), e não no “Publicar”. O `publish` só monta o envio com os bytes já preparados (`_photos_payload`), o que foi confirmado no código;
  - o tempo do “Publicar” é o envio dos bytes, mais o processamento das imagens no Xano (`storage.create_image` de cada uma).

  | 5 fotos | Regra | Pillow (na escolha) | Enviado ao Xano |
  |---|---|---|---|
  | celular, JPEG 4032 × 3024 (~4,4 MB cada) | antes: 2048 px, JPEG q90 | 2,5 s | 7.073 KB |
  | celular, JPEG 4032 × 3024 | depois: 1600 px, JPEG q82 com `optimize` | 2,2 s | **3.235 KB (−54%)** |
  | print, PNG 1920 × 1080 sem transparência | antes: PNG mantido | 4,2 s | 16.715 KB |
  | print, PNG 1920 × 1080 sem transparência | depois: vira JPEG | 0,9 s | **1.832 KB (−89%)** |

- **Tempo da requisição ao Xano:** não dá para medir daqui, sem acesso à instância. O script real ganhou a medição **FF8**: publica 5 fotos de celular com a regra antiga e com a nova, cronometra as duas requisições e apaga as duas doações. Os tempos ficam anotados na 7.2.
- **Ajuste aplicado** (`encode_limited` em `recorte_foto.py`, usado só nas fotos de doação):
  - o lado maior passa de 2048 para **1600 px**, sem ampliar;
  - o JPEG passa a usar **qualidade 82 com `optimize`**;
  - o **PNG só é usado quando há algum pixel transparente**; um PNG ou GIF sem transparência vira JPEG. A regra do WEBP (PNG com transparência, JPEG sem) passa a valer para todos os formatos.
- **A foto de perfil não muda:** o `encode_square` continua com JPEG q90 e o formato da decisão 4a da change recorte-foto-perfil.

### 5b. Foto pequena e com marca d'água no visualizador (diagnóstico do roteiro 7.3, sem mudança no código)

- **Sintoma:** no visualizador, a foto aparecia com uns 325 × 285 px na tela e com a marca “POWERED BY XANO NOCODE BACKEND”.
- **Primeira hipótese (descartada):** o servidor de arquivos do Xano entregaria ao navegador uma versão reduzida e com marca d'água, escolhida pelo `Accept` (`image/avif`, `image/webp`). Com base nela, chegou a ser feita uma rota `/foto-original` no servidor do Reflex, que buscava o arquivo com `Accept: */*`. A rota não mudou nada no roteiro 7.3.
- **Diagnóstico** (script temporário, já apagado): para cada foto da doação mais recente, a URL guardada foi baixada com `Accept: */*` e com o `Accept` e o `User-Agent` de um Chrome.
  - Os dois downloads vieram **idênticos** e já pequenos (por exemplo, 261 × 228 em PNG e 474 × 470 em JPEG).
  - Ou seja, o Xano **não troca a versão pelo `Accept`**: o arquivo guardado é que já era pequeno.
  - As fotos usadas no teste já eram pequenas e com a marca d'água na origem. Com uma foto real de celular, o visualizador mostrou a foto grande e sem marca.
- **Conclusão:** não há defeito na entrega nem no visualizador. A rota `/foto-original` e tudo ligado a ela foram removidos, e a galeria e o visualizador voltaram a usar a URL que o Xano devolve no detalhe.
- **CSS do visualizador:** mantido. A foto ocupa o máximo que cabe na tela (descontando as setas e o cabeçalho), com `object-fit: contain`, sem ampliar além do tamanho natural; por isso uma foto pequena aparece pequena.

### 5c. Foco dos botões do cadastro

“Voltar”, “Continuar” e “Publicar doação” ganham `_focus_visible` com o anel `2px solid #007A42` (e `boxShadow: none`), no lugar do anel azul do tema Radix.

### 5. Depois de publicar: detalhe com o aviso

- **No `publish`, com sucesso:**
  - `published = True` (impede um segundo envio);
  - limpa `_photo_files`;
  - `yield DonationDetailState.set_published_notice(donation_id)`;
  - `yield rx.redirect(f"/doacao/{donation_id}")`.
  - O `success_message` sai do passo 5.
- **Em `DonationDetailState`:**
  - um campo `published_notice_id: int = 0` (definido pelo evento acima) e um campo `show_published_notice: bool = False`;
  - no `load_donation`: `show_published_notice = (published_notice_id == id da rota)`; depois, `published_notice_id = 0`. Assim o aviso aparece só nessa chegada. Recarregar ou abrir outra doação não mostra o aviso.
  - É o mesmo padrão do `flash` de “Minhas doações” (`set_flash`).
- **Importação:** `chat.py` importa de `cadastro_doacao.py`, e `detalhe_doacao.py` importa de `chat.py`. Por isso o `DonationDetailState` é importado **dentro** do `publish` (importação local), para não criar um ciclo no carregamento dos módulos.
- **Aviso no detalhe:**
  - uma faixa no topo do conteúdo (`role="status"`), em `#E8F5EC`, com “Doação publicada!” em `#166B3B` negrito;
  - ao lado, o link “Minhas doações” (`/minhas-doacoes`), em `#007A42`, sublinhado, com 44 px de altura mínima;
  - a faixa quebra a linha em 360 px;
  - **sem animação própria**, porque o detalhe já anima o conteúdo estático.

### 6. Select com o estilo no Trigger, compartilhado

- Novo módulo `doafacil/campos.py` com `select_field(label, options, value, on_change, placeholder, field_id)`. É o `_edit_select` de `minhas_doacoes.py`, movido para cá:
  - estilo no `rx.select.trigger`: fundo branco, borda `#C8C8C8`, 40 px, texto `#1F1F1F`, placeholder `#333333` e foco `#007A42`;
  - `rx.select.content(high_contrast=True)`.
- O `minhas_doacoes.py` passa a importar dali e mantém `_edit_select` como nome, para o `editar_perfil.py` não mudar.
- O `cadastro_doacao._select_field` passa a chamar `select_field`. Valem os mesmos ids (`donation-category`, `donation-condition`, `donation-delivery-method` e `donation-contact-preference`), então as regras de cor do placeholder no `app.style` continuam valendo.
- Os quatro selects do cadastro ficam brancos. O pedido citava só o do passo 5, mas o defeito vem do mesmo componente (dúvida 3).

### 7. Testes

- **`tests/test_donation_photos.py`** (novo):
  - `check_file`: tipo, 5 MB exatos aceitos e 5 MB + 1 byte recusados;
  - `process_photo`:
    - EXIF corrigido;
    - sem metadados: nem EXIF, nem GPS, nem marca/modelo nos bytes, nem ICC;
    - WEBP→JPEG ou PNG pela transparência, e GIF→PNG;
    - lado maior de no máximo 1600 px (2048 na primeira versão), sem ampliar uma imagem pequena;
    - miniatura de até 240 px;
    - imagem ilegível;
  - `encode_limited` em `recorte_foto.py`: formato, tamanho e ausência de metadados;
  - `rejection_message`;
  - a limpeza dos arquivos no servidor (decisão 1a): `_photo_files` vazio depois de remover a última foto, depois de publicar com sucesso e depois de `load_initial_data`; numa falha, as fotos ficam;
  - os nomes enviados `foto-1.jpg`, `foto-2.png` e assim por diante, na ordem;
  - `remove`, `move` (pontas inclusive) e `make_cover`, mantendo a ordem relativa;
  - eventos do estado:
    - `add_photos` soma e limita;
    - excedentes e inválidos dão a mensagem atual, sem perder as já aceitas;
    - `remove_photo`, `move_photo` e `make_cover` com o `set_focus`;
    - `advance` sem fotos;
  - o passo 3: miniaturas, selo “Capa”, rótulos com a posição, botões de 44 px desativados nas pontas e contraste.
- **`tests/test_donation_creation.py`** (ajustes):
  - o `publish` envia as partes `photos[]` **na ordem de `photos`**, conferida pelo nome e pelos bytes no multipart;
  - no sucesso: `set_published_notice` e o redirecionamento para `/doacao/<id>`, sem `success_message`;
  - na falha: as fotos e a ordem mantidas;
  - o reinício limpa as fotos;
  - os quatro selects usam o Trigger branco;
  - os testes antigos que usavam `rx.upload_files` no `advance` e no `publish` são atualizados.
- **`tests/test_donation_detail.py`:** o aviso aparece só quando `published_notice_id` é o da rota e é consumido; não aparece ao recarregar nem em outra doação; tem o link, o `role` e o contraste.
- **`scripts/teste_fotos_formulario_real.py`** (novo, no padrão dos outros):
  - usa as funções puras e o `_publish_donation` de verdade contra o Xano;
  - não imprime nomes, e-mails, URLs, títulos nem corpos de resposta;
  - **apaga a doação de teste no fim**, mesmo com erro no meio.

  | Cenário | O que confere |
  |---|---|
  | FF1 | a publicação com três fotos de cores diferentes (vermelha, verde, azul), reordenadas com `make_cover` e `move` para azul, vermelha, verde, responde com uma doação “disponível” |
  | FF2 | o detalhe traz as três fotos nessa ordem, conferida pela cor de cada arquivo baixado |
  | FF3 | a capa do detalhe e a do cartão em `mine` são azuis |
  | FF4 | a capa do perfil público (`donor`) é azul |
  | FF5 | uma foto JPEG com EXIF de orientação, marca, modelo e GPS, reprocessada por `process_photo`, chega ao Xano sem EXIF nem esses textos e em pé (baixada pelo detalhe) |
  | FF6 | o `DELETE` da doação de teste responde 200 |
  | FF7 | depois, o detalhe da doação apagada responde 404 |

## Riscos e trade-offs

- **As fotos reprocessadas ficam na memória do servidor do Reflex** até publicar, remover ou reiniciar (até 5 por sessão, com até 1600 px cada) → limpas nesses três momentos (decisão 1a).
- **Reprocessar no `add_photos` custa alguns décimos de segundo por foto** → aparece “Preparando fotos...”. Em troca, o envio não tem metadados, e a miniatura e o envio saem da mesma imagem.
- **JPEG reprocessado perde um pouco de qualidade** (qualidade 90) → aceitável para as fotos de um anúncio, em troca de remover os metadados e limitar o tamanho.
- **Cada escolha agora vai ao servidor na hora,** e não só no “Publicar” → a pessoa vê “Preparando fotos...”. O envio ao Xano continua acontecendo só ao publicar.
- **Foco depois de reordenar:** o `rx.foreach` recria as linhas, e o foco vai para o botão certo pelo `rx.set_focus`. O roteiro manual confere.
- **Uma imagem que o Pillow não abre,** mas que o Xano aceitaria (raro), passa a ser recusada na tela → é coerente com a mensagem atual de formato.
- **O aviso de publicação depende do estado da sessão:** se o redirecionamento falhar, a doação já foi criada e aparece em “Minhas doações”.

## Plano de migração

- Não há dados para migrar, e o Xano não muda. Doações já publicadas continuam com a ordem que tinham.
- Reversão: voltar o passo 3 e o `publish` para o `rx.upload_files`. O módulo `campos.py` pode ficar.

## Respostas (tarefa 1.1) e acréscimo

As decisões foram tomadas pelo Higor com o Claude, sem consulta ao grupo.

1. **Tamanho:** **limite de 5 MB por foto**, conferido na tela antes de aceitar a foto, com a mesma mensagem da foto de perfil: “A foto pode ter no máximo 5 MB.” (decisão 1).
2. **Texto do passo 3:** “Adicione de 1 a 5 fotos. A primeira foto é a capa da doação.”
3. **Selects:** os quatro selects do cadastro são corrigidos.
4. **Aviso no detalhe:** fica até sair da página, sem botão de fechar.

**Acréscimo obrigatório:** cada foto de doação é reprocessada com o Pillow antes de ir ao Xano (decisão 4b), e os arquivos guardados no servidor do Reflex são apagados ao publicar, ao remover e ao reiniciar (decisão 1a).

## Dúvidas para o grupo (tarefa 1.1)

1. **Tamanho:** hoje não há limite de tamanho para fotos de doação. A proposta é manter assim. Ou entra o mesmo limite de 5 MB por foto da foto de perfil, com a mensagem “A foto pode ter no máximo 5 MB.”?
2. **Texto do passo 3:** trocar “Você pode publicar sem fotos.”, que contradiz a regra de pelo menos uma foto, por “Adicione de 1 a 5 fotos. A primeira foto é a capa da doação.” (proposta)?
3. **Selects:** aplicar o fundo branco aos quatro selects do cadastro (proposta), ou só ao do passo 5?
4. **Aviso no detalhe:** a faixa fica até sair da página (proposta), ou deve ter um botão para fechar?
