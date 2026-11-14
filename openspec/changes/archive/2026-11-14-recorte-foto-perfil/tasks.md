# Tarefas

Esta change não muda o Xano: nenhum `.xs` é editado e não há dry-run nem push.

## 1. Preparação

- [x] 1.1 Fazer uma prova técnica descartável, fora do commit (página temporária ou script na pasta temporária), com o `react-easy-crop` envolvido como `NoSSRComponent` no Reflex 0.9.12. Confirmar:
  - a versão exata do pacote;
  - que o componente renderiza com `crop_shape="round"`, `aspect=1` e `restrict_position=True`;
  - que o `crop` e o `zoom` ligados a `ClientStateVar` arrastam sem eventos no servidor;
  - que o `on_crop_complete` entrega os `croppedAreaPixels` ao estado;
  - o suporte do pacote às setas (`keyboardStep`);
  - um caminho para `+` e `-` no zoom.

  Verificação: os achados anotados na decisão 1 do `design.md`. Se o `ClientStateVar` não funcionar, parar e levar a dúvida 3 ao grupo.
  - Resultado: foi usado o plano B, aprovado na 1.2. Os motivos estão na decisão 1. As versões e o build ficaram assim:
    - `react-easy-crop@6.2.4`;
    - o componente local `assets/recorte/image_cropper.jsx`;
    - `reflex compile` e `reflex export --frontend-only` OK.
- [x] 1.2 (manual) O grupo responde às dúvidas 1 a 4 do `design.md`, e a spec, o design e estas tarefas são ajustados se alguma resposta mudar o comportamento. Verificação: as respostas no `design.md` e o `openspec validate recorte-foto-perfil --strict` passando.
- [x] 1.3 Instalar o `Pillow` no `.venv` com `pip` e fixar a versão no `requirements.txt`. Verificação: `python -c "import PIL"` funciona, e o `requirements.txt` tem a versão instalada.
  - Instalado `pillow==13.0.0` com `.venv\Scripts\python.exe -m pip install Pillow` e fixado no `requirements.txt`.

## 2. Recorte (funções puras)

- [x] 2.1 Criar `doafacil/recorte_foto.py` com:
  - `prepare_source`: abre a imagem, aplica o limite de pixels, corrige o EXIF, usa o primeiro quadro do GIF e devolve o formato real;
  - `make_preview`: lado maior de até 1024 px, em `data:` URL, e a escala;
  - `crop_square`: escala, quadrado, limites e erro de área inválida;
  - `encode_square`: 512 × 512, formato da tabela da decisão 4 e sem metadados.

  Verificação: os testes da 2.2.
- [x] 2.2 Escrever `tests/test_profile_photo_crop.py`, com os casos da decisão 7:
  - coordenadas com quatro quadrantes e escala;
  - EXIF 3, 6 e 8;
  - limites (negativos, além da largura, maior que a imagem, não quadrado, nulo, NaN e infinito);
  - formatos (JPEG, PNG com transparência, WEBP→JPEG ou PNG conforme a transparência, e GIF→PNG);
  - remoção dos metadados;
  - arquivos ilegíveis e acima do limite de pixels;
  - prévia de até 1024 px.

  Verificação: `python -m unittest tests.test_profile_photo_crop` passa.

## 3. Componente e estado

- [x] 3.1 Criar o `ImageCropper` (`NoSSRComponent`) em `doafacil/recorte_foto.py`, com a versão fixa da 1.1, e os `ClientStateVar` do `crop` e do `zoom`. Verificação: teste de renderização com as props `cropShape`, `aspect`, `restrictPosition` e `minZoom`/`maxZoom`, e o `reflex compile` sem erros.
- [x] 3.2 Em `EditProfileState`, trocar o envio na hora pelo fluxo da decisão 2: `prepare_crop`, `set_crop_area`, `cancel_crop` e `confirm_crop`, com as variáveis de backend `_crop_source` e `_crop_format`. Remover o `upload_photo` antigo. Verificação: testes do estado em `tests/test_edit_profile.py`:
  - um arquivo válido abre o modal sem requisição;
  - arquivos inválidos mostram as mensagens atuais;
  - “Cancelar” limpa tudo sem requisição;
  - “Usar foto” envia os bytes do recorte com o nome `foto.<ext>` e o `mime` certo;
  - os erros 400, 401, 429 e de rede seguem como hoje;
  - a área inválida mostra o erro sem enviar;
  - o formulário digitado é mantido.
- [x] 3.3 Criar o `_crop_dialog` (decisão 5) e ligá-lo ao `rx.upload` da seção Foto. Verificação: testes de componente:
  - o título “Ajustar foto” e o texto de ajuda;
  - o rótulo acessível da área;
  - o controle “Zoom” e os botões “Diminuir zoom” e “Aumentar zoom” de 44 px;
  - “Cancelar” e “Usar foto” (desativado sem área);
  - a largura `min(480px, calc(100vw - 32px))`;
  - o contraste AA dos botões.

## 4. Teste real e documentação

- [x] 4.1 Escrever `scripts/teste_recorte_foto_real.py` com os cenários RC1 a RC8 da decisão 7, no padrão do `teste_foto_perfil_real.py`:
  - credenciais só em memória;
  - nada impresso além de status, chaves e sim/não;
  - restauração da foto original no fim.

  Verificação: `py_compile` e a leitura do script pelo grupo.
- [x] 4.2 Atualizar o `docs/design/README.md` (“Editar perfil”, com o modal “Ajustar foto”, que não está no Figma) e o `docs/guia-do-colaborador.md` (fluxo da foto, dependências novas e como rodar o `teste_recorte_foto_real.py`). Verificação: o texto bate com a spec delta e o design.

## 5. Verificação final

- [x] 5.1 Rodar `python -m unittest discover -s tests`, `openspec validate recorte-foto-perfil --strict` e `reflex compile`, e mostrar o `git diff --stat`. Verificação: tudo passa, e não há nenhum arquivo em `xano/` na diff desta change.
  - Resultados:
    - 492 testes OK;
    - `reflex compile` OK, e o `reflex export --frontend-only --no-zip` também gerou o bundle;
    - `openspec validate --strict` OK.
  - Os `.xs` modificados no `git status` são divergências antigas do pull. Esta change não toca em `xano/`.
- [x] 5.2 (manual) O grupo roda o `teste_recorte_foto_real.py`. Verificação: RC1 a RC8 OK, anotados aqui.
  - **1ª rodada (Higor):** 7 de 8 OK. Falhou só o RC4 (“WEBP continua WEBP”): HTTP 200, mas o formato não estava certo.
    - A causa não foi confirmada. A decisão 4a passou a converter o WEBP para PNG ou JPEG antes do envio.
    - O RC4 virou “WEBP sem transparência vira JPEG”, e entrou o RC4b (“WEBP com transparência vira PNG”).
  - **2ª rodada (Higor):** 9 de 9 OK (RC1 a RC8 e o RC4b).
- [x] 5.3 (manual) No navegador, em 1512 px e 360 px, conferir:
  - arrastar com o mouse e com o dedo;
  - o zoom pelo controle, pela roda do mouse, pela pinça e por `+` e `-`;
  - as setas;
  - `Esc` e “Cancelar” sem envio;
  - “Usar foto” mostrando a foto nova na seção, na prévia e em “Minhas doações”;
  - uma foto de celular em pé;
  - nenhuma rolagem horizontal;
  - o foco preso no modal e de volta em “Alterar foto”.

  Verificação: os itens anotados aqui.
  - Conferido pelo Higor, em 1512 px e 360 px:
    - o modal abre sem enviar nada;
    - arrastar e o zoom (pelo controle, pela roda e pelos botões) mantêm a moldura sempre coberta;
    - o teclado funciona: as setas e as teclas `+` e `-`;
    - “Cancelar”, `Esc` e o clique fora não mudam a foto nem o formulário;
    - “Usar foto” envia o enquadramento certo;
    - um `.txt` mostra a mensagem de formato;
    - em 360 px não há rolagem horizontal.
  - Ajuste visual feito depois do roteiro, com testes de estilo. O `reflex compile` e o build do frontend passaram.
    - Antes, o controle de zoom tinha o marcador quadrado preto do navegador e a trilha sem preenchimento.
    - Agora a trilha é cinza clara `#C8C8C8`, com a parte preenchida em `#007A42`, e o marcador é redondo, de 20 px, branco com borda verde.
    - O anel de foco é verde (`#007A42`) no controle, nos botões − e + e na área de enquadramento, no lugar do azul do navegador.
