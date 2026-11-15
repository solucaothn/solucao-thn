# Tarefas

Esta change não muda o Xano: nenhum `.xs` é editado e não há dry-run nem push.

## 1. Preparação

- [x] 1.1 (manual) O grupo responde às dúvidas 1 a 4 do `design.md`, e a spec, o design e estas tarefas são ajustados se alguma resposta mudar o comportamento. Verificação: as respostas no `design.md` e o `openspec validate fotos-formulario-doacao --strict` passando.
  - Respondidas pelo Higor com o Claude:
    - limite de 5 MB por foto na tela;
    - o texto novo do passo 3;
    - os quatro selects;
    - o aviso sem botão de fechar.
  - Acréscimo: o reprocessamento das fotos (decisão 4b) e a limpeza dos arquivos no servidor (decisão 1a).

## 2. Funções puras das fotos

- [x] 2.1 Em `doafacil/recorte_foto.py`, criar `encode_limited(source, max_side=2048)` (sem ampliar e sem metadados), compartilhando a codificação com o `encode_square`. Criar `doafacil/fotos_doacao.py` com `check_file` (tipo e 5 MB), `process_photo` (decisão 4b, com a miniatura de 240 px), `rejection_message`, `remove`, `move` e `make_cover` (decisão 2). Verificação: os testes da 2.2.
- [x] 2.2 Escrever os testes das funções puras em `tests/test_donation_photos.py`:
  - tipo e 5 MB (no limite e 1 byte acima);
  - EXIF corrigido;
  - nenhum metadado (EXIF, GPS, marca/modelo nos bytes e ICC);
  - WEBP→JPEG ou PNG e GIF→PNG;
  - o máximo de 2048 px sem ampliar;
  - a miniatura de até 240 px;
  - a imagem ilegível;
  - a `rejection_message`;
  - remover, mover (inclusive nas pontas) e tornar capa, mantendo a ordem relativa.

  Os testes do `encode_limited` ficam em `tests/test_profile_photo_crop.py`. Verificação: os dois arquivos de teste passam.

## 3. Select compartilhado

- [x] 3.1 Criar `doafacil/campos.py` com `select_field` (o `_edit_select` atual, movido). Fazer o `minhas_doacoes.py` importar dali, mantendo o nome `_edit_select`, e o `cadastro_doacao._select_field` usar `select_field` com os mesmos ids (decisão 6). Verificação:
  - os testes de “Minhas doações” e “Editar perfil” continuam passando;
  - um teste novo confere o Trigger branco com borda `#C8C8C8` e foco `#007A42` nos quatro selects do cadastro, inclusive o “Preferência de contato”.

## 4. Estado e passo 3

- [x] 4.1 Em `DonationCreateState`, criar o fluxo da decisão 1:
  - `add_photos`, com a variável de backend `_photo_files`, o `photos`, o `photos_busy` e a limpeza da seleção do componente;
  - `photos_rejected`;
  - `remove_photo`, `move_photo` e `make_cover`, com o `rx.set_focus` e o aviso curto.

  Guardar só a versão reprocessada em `_photo_files`. Ter uma função única `_clear_photos`, usada ao reiniciar (`load_initial_data`) e ao publicar com sucesso; remover uma foto apaga só a entrada dela (decisão 1a). Verificação: testes do estado em `tests/test_donation_photos.py`:
  - somar;
  - limitar com a mensagem atual, sem perder as já aceitas;
  - tipo inválido, mais de 5 MB, imagem ilegível e arquivo vazio;
  - remover, mover e tornar capa;
  - `_photo_files` sem a foto removida e vazio no reinício;
  - nenhum byte original guardado.
- [x] 4.2 Refazer o `_step_three` (decisão 3): área de escolha com `on_drop` e `on_drop_rejected`, contador, lista com miniaturas, selo “Capa”, os quatro botões com rótulos que incluem a posição, o limite atingido e o texto novo do passo. Verificação: testes de componente:
  - os rótulos e os ids dos botões;
  - os botões desativados nas pontas e na capa;
  - os 44 px;
  - o selo só na primeira foto;
  - o texto alternativo “Foto N de M”;
  - nenhuma largura fixa maior que a coluna;
  - o contraste do selo, do ícone de remover e do ícone da área.

## 5. Publicação e detalhe

- [x] 5.1 Fazer o `advance` (passo 3) e o `publish` usarem `photos` e `_photo_files`, enviando na ordem de `photos` com os nomes `foto-N.<ext>`. No sucesso, limpar as fotos (`_clear_photos`), chamar `DonationDetailState.set_published_notice` (importação local) e redirecionar para `/doacao/<id>`. Verificação: testes em `tests/test_donation_creation.py`:
  - a ordem e os nomes das partes `photos[]` no multipart;
  - o redirecionamento e o aviso no sucesso;
  - `_photo_files` vazio depois do sucesso;
  - as fotos e a ordem mantidas na falha;
  - um segundo clique não publica de novo.

  Os testes antigos de `advance` e `publish` são atualizados.
- [x] 5.2 Em `DonationDetailState` e na página de detalhe, criar o aviso “Doação publicada!” com o link “Minhas doações” (decisão 5), mostrado só na chegada. Verificação: testes em `tests/test_donation_detail.py`:
  - aparece com o id certo e é consumido;
  - não aparece ao recarregar nem em outra doação;
  - o `role="status"`, o link para `/minhas-doacoes`, os 44 px e o contraste.

## 6. Teste real e documentação

- [x] 6.1 Escrever `scripts/teste_fotos_formulario_real.py` com os cenários FF1 a FF7 da decisão 7, no padrão dos outros:
  - credenciais só em memória;
  - nada impresso além de status, contagens e sim/não;
  - apagar a doação de teste no `finally`.

  Verificação: `py_compile` e a conferência offline das partes locais (imagens, ordem e `accept_files`).
- [x] 6.2 Atualizar o `docs/design/README.md` (o passo 3 do cadastro, os selects brancos e o aviso no detalhe) e o `docs/guia-do-colaborador.md` (o fluxo das fotos no servidor do Reflex, a ordem e a capa sem mudança no Xano, o `campos.py` e como rodar o script). Verificação: o texto bate com a spec delta e o design.

## 6a. Ajustes depois do roteiro (7.3)

- [x] 6a.1 Visualizador: diagnosticar a foto pequena e com marca d'água (decisão 5b). Verificação: o diagnóstico registrado no design.
  - Uma rota `/foto-original` chegou a ser feita e depois foi **removida**: os downloads com `Accept: */*` e com o `Accept` do Chrome vieram idênticos e pequenos, e o problema estava nas fotos de teste, não na entrega.
  - A galeria e o visualizador voltaram a usar a URL do Xano.
- [x] 6a.2 Publicação mais rápida: medir o Pillow e o tamanho enviado, e aplicar 1600 px, JPEG q82 com `optimize` e PNG só com transparência (decisão 4c). Acrescentar a medição FF8 ao script real. Verificação:
  - os testes do `encode_limited` e do `process_photo` atualizados;
  - a tabela de antes e depois no design;
  - as partes locais do FF8 conferidas offline.
- [x] 6a.3 Foco verde em “Voltar”, “Continuar” e “Publicar doação” (decisão 5c). Verificação: o teste `WizardFocusTests` em `tests/test_donation_creation.py`.

## 7. Verificação final

- [x] 7.1 Rodar `python -m unittest discover -s tests`, `openspec validate fotos-formulario-doacao --strict` e `reflex compile`, e mostrar o `git diff --stat`. Verificação: tudo passa, e não há nenhum arquivo em `xano/` na diff desta change.
  - Resultados:
    - 525 testes OK;
    - `reflex compile` OK, e o `reflex export --frontend-only --no-zip` também OK;
    - `openspec validate --strict` OK.
  - Os `.xs` que aparecem no `git status` são divergências antigas do pull. Esta change não toca em `xano/`.
- [x] 7.2 (manual) O grupo roda o `teste_fotos_formulario_real.py`. Verificação: FF1 a FF7 OK, anotados aqui.
  - **1ª rodada (Higor):** 7 de 7 OK.
  - **2ª rodada (Higor), depois dos ajustes da 6a:** 8 de 8 OK (FF1 a FF8).
  - **FF8**, 5 fotos de celular:

    | Regra | Requisição ao Xano | Enviado |
    |---|---|---|
    | antiga (2048 px, JPEG q90) | 4,2 s | 7.073 KB |
    | nova (1600 px, JPEG q82 com `optimize`) | 3,5 s | 3.235 KB |
- [x] 7.3 (manual) No navegador, em 1512 px e 360 px, conferir:
  - escolher 2 fotos e depois mais 2, que devem somar;
  - tentar passar de 5, com a mensagem e as fotos mantidas;
  - um `.pdf`, com a mensagem;
  - uma foto com mais de 5 MB, com a mensagem de tamanho;
  - uma foto de celular tirada em pé, que aparece em pé na miniatura e no detalhe;
  - as miniaturas e o selo “Capa”;
  - mover, tornar capa e remover pelo mouse e pelo teclado, com o foco no lugar certo;
  - voltar ao passo 2 e retornar ao 3 sem perder as fotos;
  - os quatro selects brancos;
  - publicar e cair no detalhe com o aviso e o link, com a capa e a ordem certas;
  - recarregar o detalhe, que não mostra mais o aviso;
  - “Minhas doações” com a capa certa;
  - nenhuma rolagem horizontal;
  - no visualizador do detalhe, uma foto real de celular grande, sem marca d'água e sem ficar borrada;
  - o anel de foco verde em “Voltar”, “Continuar” e “Publicar doação”;
  - o tempo do “Publicar” com 5 fotos de celular.

  Verificação: os itens anotados aqui.
  - **Resultado (Higor):** roteiro OK.
  - O visualizador com foto pequena e com marca d'água era das fotos de teste, que já eram assim na origem; com foto real de celular, a foto ficou grande e sem marca (decisão 5b).
