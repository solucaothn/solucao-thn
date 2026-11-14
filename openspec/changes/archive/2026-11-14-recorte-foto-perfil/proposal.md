# Proposal

## Why

Hoje, em `/perfil/editar`, a foto escolhida em “Alterar foto” é enviada na hora, inteira, e as telas a cortam em círculo com `object-fit: cover`. Quem escolhe uma foto retangular ou com o rosto fora do centro não controla o que aparece. O resultado é um rosto cortado ou pequeno demais no avatar, que aparece em “Minhas doações”, no perfil público, no “Quem doa” e no chat.

Esta change deixa a pessoa enquadrar a foto antes de enviar. O endpoint do Xano não muda.

## What Changes

- **Modal de enquadramento:** ao escolher uma foto em “Alterar foto”, abre um modal com a imagem e uma moldura circular. Nele, a pessoa:
  - arrasta a imagem para posicionar (mouse, toque ou setas do teclado);
  - controla o zoom por um controle deslizante, pela roda do mouse, por pinça no celular ou pelas teclas `+` e `-`.
- **Botões do modal:**
  - “Cancelar” fecha o modal sem enviar nada e mantém a foto atual;
  - “Usar foto” envia a área enquadrada.
- **Resultado:** uma imagem quadrada de 512 × 512 px com exatamente a área enquadrada.
  - O recorte é feito no servidor do Reflex com o Pillow. A orientação EXIF é corrigida antes do recorte, e os metadados (inclusive a localização) são removidos.
  - JPEG e PNG mantêm o formato. Um GIF vira PNG estático. Um WEBP vira PNG quando tem transparência e JPEG quando não tem (decisão 4a do `design.md`, depois do teste real). O resultado enviado é sempre JPEG ou PNG.
  - O envio usa o mesmo `POST /auth/profile/photo`, sem mudança no Xano.
- **Validações:** as de hoje (formato e até 5 MB, na tela e no Xano) continuam, com as mesmas mensagens. Um arquivo que o Pillow não consegue abrir recebe a mensagem de formato.
- **Layout e acessibilidade:**
  - o modal cabe em 360 px sem rolagem horizontal;
  - o foco fica preso no modal, e `Esc` cancela;
  - todos os controles têm rótulos acessíveis e área de toque de pelo menos 44 px.
- **Dependências novas:**
  - o pacote Python `Pillow`, que entra no `requirements.txt`;
  - o pacote React `react-easy-crop`, numa versão fixa, envolvido como componente Reflex (`NoSSRComponent`). Ele é instalado pelo próprio Reflex.
- **Testes:**
  - testes unitários do recorte: coordenadas, escala da prévia para o original, orientação EXIF, limites fora da imagem, formatos e remoção de metadados;
  - testes do estado e do modal;
  - o script `scripts/teste_recorte_foto_real.py`, no padrão dos outros testes reais.

### Fora do escopo

- Girar ou espelhar a imagem, filtros e ajustes de cor.
- Recortar fotos de doações. Continuam como hoje.
- Qualquer mudança no Xano, como os endpoints, o limite de 5 MB ou os formatos aceitos.
- Reenquadrar uma foto já enviada sem escolher o arquivo de novo.

## Capabilities

### New Capabilities

Nenhuma.

### Modified Capabilities

- `user-account`:
  - a “Página de edição do perfil” muda: escolher uma foto abre o modal de enquadramento em vez de enviar na hora;
  - entra o requisito novo “Enquadramento da foto de perfil”, com o modal, o resultado quadrado, o formato, o EXIF, os metadados e a acessibilidade.

## Impact

- **Código:**
  - `doafacil/editar_perfil.py`: os eventos de “Alterar foto” e o modal;
  - um módulo novo `doafacil/recorte_foto.py`, com as funções puras do recorte e o componente do `react-easy-crop`.
  - O `upload_profile_photo` e o cliente do Xano continuam iguais.
- **Dependências:** `Pillow` no `requirements.txt` e `react-easy-crop` com versão fixa, declarado no componente.
- **Estado:** o original escolhido fica só no servidor do Reflex, numa variável de backend que não vai ao navegador, até “Usar foto” ou “Cancelar”. A prévia vai ao navegador reduzida, com no máximo 1024 px.
- **Testes:**
  - `tests/test_profile_photo_crop.py`, novo;
  - os testes de upload em `tests/test_edit_profile.py`, ajustados;
  - `scripts/teste_recorte_foto_real.py`, novo.
- **Documentação:** a seção “Editar perfil” do `docs/design/README.md` e a seção da foto de perfil no `docs/guia-do-colaborador.md`.
- **Xano:** nenhuma mudança.
