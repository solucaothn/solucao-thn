# Proposal

## Why

No passo 3 do cadastro de doação (`/cadastro-doacao`), quem doa vê só o nome dos arquivos escolhidos. Não dá para conferir as fotos, tirar uma só (o botão remove todas) nem escolher qual delas é a capa: a capa nos cartões e no detalhe é sempre a primeira foto da seleção do navegador. Escolher mais fotos depois substitui as anteriores em vez de somar.

O formulário tem ainda dois problemas menores:

- no passo 5, o select “Preferência de contato” aparece com o fundo cinza, como se estivesse desativado. É o mesmo defeito já corrigido em “Editar perfil”;
- depois de publicar, a pessoa fica parada no passo 5, com o botão “Publicado”, sem caminho claro para ver a doação ou “Minhas doações”.

## What Changes

- **Passo das fotos:**
  - uma **miniatura** de cada foto logo depois da escolha, antes de publicar;
  - **“Remover foto N”** em cada foto;
  - **reordenar** com os botões **“Mover para a esquerda”**, **“Mover para a direita”** e **“Tornar capa”**, sem arrastar;
  - a **primeira foto é a capa** e tem o selo **“Capa”**;
  - **escolher mais fotos soma às já escolhidas**, com os limites atuais (até 5 fotos, só JPEG, PNG, GIF ou WEBP) e um limite novo, na tela, de **5 MB por foto**, com a mensagem da foto de perfil: “A foto pode ter no máximo 5 MB.”;
  - **cada foto é preparada antes do envio:** a orientação EXIF é corrigida, todos os metadados saem (inclusive o GPS), o lado maior fica com no máximo 1600 px (sem ampliar), o arquivo é PNG só quando há transparência real e JPEG otimizado nos outros casos (decisão 4c do `design.md`, para publicar mais rápido), e o nome enviado é `foto-N.<ext>`. São as funções do recorte da foto de perfil;
  - **as fotos guardadas no servidor do Reflex** (só a versão preparada, na memória da sessão) são apagadas ao remover, ao publicar e ao reiniciar o cadastro;
  - as mensagens de erro atuais continuam as mesmas;
  - funciona em 360 px sem rolagem horizontal, e tudo é acessível pelo teclado, com rótulos.
- **A ordem escolhida é a ordem salva:** as fotos são enviadas ao endpoint atual na ordem da tela. O Xano já grava a `position` na ordem do envio e usa a primeira foto como capa, nos cartões e no detalhe. **Não há mudança no Xano.**
- **Passo 5:** o select “Preferência de contato” passa a usar o select com o estilo no botão visível, o mesmo da edição de doação e de “Editar perfil”: fundo branco, texto `#1F1F1F` e foco verde. Como os outros selects do cadastro (Categoria, Condição e Forma de entrega) usam o mesmo componente, a correção vale para eles também.
- **Depois de publicar:** a página vai para o detalhe da nova doação (`/doacao/<id>`), que mostra o aviso **“Doação publicada!”** e um link para **“Minhas doações”**. O cadastro não fica mais parado no passo 5.
- **Texto do passo 3:** “Você pode publicar sem fotos.” sai, porque contradiz a regra de pelo menos uma foto. Entra um texto sobre a capa (dúvida 2 do `design.md`).
- **Testes:**
  - testes unitários: estado das fotos (somar, limitar, remover, reordenar e tornar capa), miniaturas, ordem do envio, select e redirecionamento com o aviso;
  - o script `scripts/teste_fotos_formulario_real.py`, no padrão dos outros, que publica uma doação de teste com fotos de cores diferentes numa ordem escolhida, confere a capa e a ordem no detalhe e nas listagens e apaga a doação no fim.

### Fora do escopo

- Arrastar para reordenar.
- Recortar ou girar fotos de doação (o recorte é só da foto de perfil).
- Editar as fotos de uma doação já publicada.
- Qualquer mudança no Xano, como os endpoints, os limites ou os formatos aceitos.

## Capabilities

### New Capabilities

Nenhuma.

### Modified Capabilities

- `donation-creation`:
  - “Seleção de fotos da doação”: miniaturas, remoção, reordenação, capa, soma de seleções e ordem do envio;
  - “Legibilidade dos textos de exemplo e seleção”: o botão do select com fundo branco;
  - “Publicação autenticada e persistente”: ir ao detalhe depois de publicar;
  - “Reinício do formulário a cada nova entrada”: o cenário da publicação concluída na mesma visita.
- `donation-detail`: requisito novo, o aviso “Doação publicada!” com o link para “Minhas doações”.

## Impact

- **Código:**
  - `doafacil/cadastro_doacao.py`:
    - o estado das fotos passa a ficar no servidor do Reflex: os bytes numa variável de backend e as miniaturas no estado;
    - o passo 3 é refeito;
    - o `_select_field` passa a ser o select da edição;
    - o `publish` envia na ordem escolhida e redireciona;
  - `doafacil/detalhe_doacao.py`: o aviso de publicação, mostrado uma vez;
  - o `_edit_select` de `doafacil/minhas_doacoes.py` é reaproveitado;
  - as miniaturas usam o Pillow, que já é dependência.
- **Xano:** nenhuma mudança. O `publish_POST.xs`, a tabela `donation_photo` e os endpoints de leitura continuam iguais.
- **Testes:**
  - `tests/test_donation_creation.py` e `tests/test_donation_detail.py` ajustados;
  - `tests/test_donation_photos.py`, novo;
  - `scripts/teste_fotos_formulario_real.py`, novo.
- **Documentação:** `docs/design/README.md` (cadastro de doação e detalhe) e `docs/guia-do-colaborador.md`.
