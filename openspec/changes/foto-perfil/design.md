# Design

## Contexto

**Upload das fotos de doação hoje:**

- **Frontend (`cadastro_doacao.py`):**
  - um `rx.upload` com `accept=IMAGE_ACCEPT` (JPG, PNG, GIF e WEBP) e `max_files=5`, sem `max_size`;
  - o `_validated_photos` confere a extensão e o tipo do arquivo;
  - o `publish` lê os bytes no servidor do Reflex e envia `multipart/form-data` ao Xano, com o campo `photos[]`.
- **Xano (`publish_POST.xs`):** entrada `file[]? photos?`, de 1 a 5 fotos, e `storage.create_image` com `access = "public"`. A URL é `$env.PUBLIC_BASE_URL ~ .path`.
- **Não há limite de tamanho em lugar nenhum** (dúvida 1).

**Xano Developer MCP (doc de uploads), consultado no explore:**

- **Entrada do arquivo:** precisa ser `file?`. Com `image?`, o `.path` não é preenchido e o upload falha.
- **`storage.create_image`:** só aceita JPEG, PNG, GIF e WEBP, e responde **500** (“Invalid file extension.”) para outros tipos. Por isso, o 400 com mensagem clara exige uma validação nossa.
- **O objeto guardado** traz `size` (em bytes) e `mime`.
- **`storage.delete_file { pathname = ... }`** apaga o arquivo. Limpar a coluna, sozinho, não apaga.

**Onde a pessoa aparece hoje:**

| Lugar | Hoje | Endpoint |
|---|---|---|
| Prévia de `/perfil/editar` | círculo de 80 px com a inicial | `GET auth/profile` |
| Cartão de `/minhas-doacoes` | círculo de 80 px | `GET catalog/donations/mine` (`owner`) |
| Perfil público | círculo de 72 px (celular) e 120 px | `GET catalog/donations/donor` (`donor`) |
| “Quem doa” do detalhe | **sem círculo**: nome e cidade | `GET catalog/donations/detail` (`donor_first_name`) |
| Lista do chat | círculo verde de 38 px (`_avatar`) | `GET catalog/chat/conversations` (`other_user_first_name`) |
| Cabeçalho da conversa | **sem círculo**: só o nome | `GET catalog/chat/messages` (primeiro nome de quem doa e de quem tem interesse) |

## Objetivos / Fora do escopo

**Objetivos:**
- Nenhuma requisição a mais: a URL da foto vem nas respostas que já existem.
- Um único componente de avatar (foto ou inicial), com tamanho e cor configuráveis.
- A validação de formato e tamanho vale também no Xano.

**Fora do escopo:**
- Recorte ou compressão da imagem.
- Limite de tamanho nas fotos de doação.
- A foto no `start` do chat e nos envios ou edições de mensagem, porque a tela não usa esses dados.

## Decisões

### Parte A — Xano

1. **Tabela `user`:** campo novo `image? photo?`, como o `photo` da tabela `donation`. Guarda o objeto do armazenamento.
2. **`POST auth/profile/photo`** (`xano/api/authentication/auth/profile/photo_POST.xs`), com `auth = "user"` e a entrada `file? photo`.
   - **Sem arquivo:** precondição, que responde 400 com “Envie uma imagem JPG, PNG, GIF ou WEBP.”.
   - **Formato:** a extensão de `$input.photo.name`, em minúsculas, precisa ser `.jpg`, `.jpeg`, `.png`, `.gif` ou `.webp`. Senão, 400 com a mesma mensagem. Essa checagem vem **antes** do armazenamento, para evitar o 500 do `create_image`.
   - **Armazenamento:** `storage.create_image` com `access = "public"`, como nas doações.
   - **Tamanho:** se `$stored.size > 5 * 1024 * 1024`, o arquivo novo é apagado com `storage.delete_file` e a resposta é 400 com “A foto pode ter no máximo 5 MB.”. A doc não confirma se o arquivo de entrada já traz o tamanho; isso será confirmado no MCP no apply.
   - **Gravação:** lê a foto atual, grava a nova com `db.edit user` e apaga o arquivo antigo, se houver (dúvida 2).
   - **Resposta:** `{photo: <URL pública>}`.
   - Os nomes exatos das propriedades do arquivo de entrada e a sintaxe de “termina com” serão confirmados no MCP.
3. **`DELETE auth/profile/photo`** (`.../profile/photo_DELETE.xs`), com `auth = "user"`. Lê a foto atual, grava `photo: null` e apaga o arquivo antigo (dúvida 2). Responde `{photo: null}`. Sem foto, também responde 200.
4. **URL da foto nas respostas:** sempre `$env.PUBLIC_BASE_URL ~ $user.photo.path`, ou nulo. Isso usa o mesmo `conditional` do `recent_GET.xs`, que lança `ConfigurationError` sem a variável.
   - `GET auth/profile`: o campo `photo`. É a própria pessoa.
   - `GET catalog/donations/mine`: `owner.photo`.
   - `GET catalog/donations/donor`: `donor.photo`.
   - `GET catalog/donations/detail`: `donor_photo`. O `db.get user` passa a ler `photo`.
   - `GET catalog/chat/conversations`: `other_user_photo` em cada item. A consulta que já busca os outros usuários em lote passa a ler `photo`.
   - `GET catalog/chat/messages`: `other_user_photo`. Os dois `db.get user` que já existem passam a ler `photo`, e a resposta escolhe a foto da outra pessoa.
   - Nenhuma resposta ganha e-mail, sobrenome ou id. Nenhum endpoint ganha uma consulta a mais ao banco: as leituras de usuário já existem.
5. **Teste real (`scripts/teste_foto_perfil_real.py`)**, com duas contas (a dona de uma doação e outra pessoa que tenha conversa com ela) e imagens pequenas geradas pelo próprio script. As fotos de teste são PNG mínimos, e o arquivo de mais de 5 MB é gerado na memória.
   - **Cenários FP1 a FP12:**
     - FP1: envio sem token dá 401;
     - FP2: um PNG válido dá 200 com a URL;
     - FP3: o `GET auth/profile` traz a mesma URL;
     - FP4: `.txt` e PDF dão 400 com a mensagem de formato;
     - FP5: um arquivo de mais de 5 MB dá 400 com a mensagem de tamanho;
     - FP6: trocar a foto muda a URL;
     - FP7: a foto aparece no `mine`;
     - FP8: a foto aparece no `donor`;
     - FP9: a foto aparece no `detail`;
     - FP10: a outra pessoa vê a foto no `conversations` e no `messages`;
     - FP11: `DELETE` faz todas as respostas voltarem nulas;
     - FP12: `DELETE` sem foto dá 200.
   - **Restauração:** no fim, num `finally`, a conta fica sem foto, como estava, ou com a foto original reenviada, se o script conseguir baixá-la. Se não conseguir, ele avisa.
   - **Scripts antigos:** o PP1, o MD2, o EP2, o EP3 e o EP11 passam a aceitar `photo` nas chaves.

### Parte B — Frontend

6. **Componente `avatar(photo, initial, size, ...)`**, em `doafacil/sobre.py`, renomeado para `doafacil/perfil_publico.py` (dúvida 7):
   - com foto, um `rx.image` redondo, com `object-fit: cover` e `alt` “Foto de <primeiro nome>”;
   - sem foto, o círculo atual (a cor e a cor do texto continuam as de cada lugar);
   - o tamanho fica igual ao círculo de hoje em cada lugar.
   - **O `_avatar` do chat** passa a delegar para ele.
   - **Leitura:** um `parse_photo_url(value)` aceita texto `http(s)` ou nulo, que vira `""`. Outro tipo é resposta inválida.
7. **Parsers e estados** ganham a foto e passam a usá-la no avatar:
   - `perfil_doador.py`: `donor.photo`;
   - `minhas_doacoes.py`: `owner.photo`;
   - `detalhe_doacao.py`: `donor_photo`, num avatar novo de 48 px no cartão “Quem doa”, com o círculo `#F2F2F2` e a inicial `#555555` (dúvida 5);
   - `chat.py`: `other_user_photo` nos itens e na leitura das mensagens, mais um avatar de 38 px no cabeçalho da conversa (dúvida 5);
   - `editar_perfil.py`: `photo`.
8. **Seção “Foto” em `/perfil/editar`:**
   - **Upload:** um `rx.upload` com `id="profile-photo-upload"`, `accept=IMAGE_ACCEPT` (o mesmo do cadastro), `max_files=1` e `max_size=5 MB`.
   - **Envio na hora:** `on_drop` chama `EditProfileState.upload_photo(rx.upload_files(...))`, que lê os bytes e envia um `multipart` com o campo `photo`.
   - **Arquivo recusado:** `on_drop_rejected` mostra a mensagem de formato ou de tamanho.
   - **Botões:** “Alterar foto”, um botão de verdade dentro do `rx.upload`, acessível pelo teclado, e “Remover foto”, que só aparece com foto (dúvida 4).
   - **Aviso:** “Sua foto aparece para outras pessoas.”, em `#555555`.
   - **Resultado:** a mensagem de sucesso ou de erro aparece com `role="status"` ou `role="alert"`.
   - **Prévia:** atualizada pela resposta do endpoint.
   - **Formulário:** não muda. O “Salvar alterações” continua só para os campos de texto.
9. **Ordem do formulário,** como no Figma: “Foto”, “Dados públicos”, “Localização”, “Conta”, o quadro e as ações.

## Riscos / Trade-offs

- **[Arquivo grande enviado ao Xano antes da checagem de tamanho]** → O `max_size` do `rx.upload` barra o arquivo na tela. O Xano confere de novo depois de guardar, e apaga o arquivo se ele passar do limite.
- **[O arquivo antigo fica no armazenamento]** → Ele é apagado com `storage.delete_file` ao trocar ou remover (dúvida 2). Se a exclusão falhar, a foto nova continua valendo.
- **[Foto inadequada]** → Não há moderação nesta change. O aviso deixa claro que a foto é pública.
- **[Cache da imagem]** → Cada envio gera um `path` novo no armazenamento, então a URL muda e não há foto antiga em cache.
- **[Limite de 10 requisições a cada 20 s]** → Enviar ou remover a foto custa 1 requisição. Mostrar a foto não custa nenhuma a mais.

## Dúvidas para o Higor

1. **Limite de tamanho:** as fotos de doação **não têm limite** hoje, nem na tela nem no Xano, então não há “o mesmo limite” para copiar. Recomendo **5 MB** para a foto de perfil, conferido na tela (`max_size`) e no Xano. A spec já está escrita assim. As fotos de doação continuam sem limite nesta change; aplicar o mesmo limite a elas seria outra change.
2. **Apagar o arquivo antigo:** recomendo apagar o arquivo anterior do armazenamento ao trocar ou remover a foto, com `storage.delete_file`, que a doc do Xano confirma. Assim, a pendência das imagens órfãs não cresce.
3. **Texto do quadro “Quem vê estas informações”:** a foto passa a ser pública, e o texto atual não a cita. Recomendo:

   > “Seu primeiro nome, sua foto, cidade, estado e o texto de Sobre aparecem no seu perfil público. Suas doações mostram o primeiro nome, a foto atual e a cidade e o estado do momento em que foram publicadas. Seu e-mail é usado para entrar e só é mostrado a pessoas logadas que pedirem contato numa doação sua com a preferência “E-mail”.”

   A spec já está escrita assim.
4. **Remover sem confirmação:** recomendo que “Remover foto” não peça confirmação, porque basta enviar a foto de novo. Outra opção é uma confirmação simples.
5. **“Quem doa” e cabeçalho do chat:** hoje nenhum dos dois tem círculo com a inicial, só o nome. Recomendo acrescentar o avatar, com a foto ou a inicial: 48 px no cartão “Quem doa” e 38 px no cabeçalho da conversa, igual ao da lista. A outra opção é mostrar só a foto quando ela existir, sem nada quando não houver foto. A spec já está escrita com a recomendação.
6. **Foto no `start` do chat:** recomendo não mudar esse endpoint, nem o envio e a edição de mensagens, porque a tela não usa esses dados. A foto vem só na lista e na leitura das mensagens.
7. **Nome do módulo compartilhado:** recomendo renomear `doafacil/sobre.py` para `doafacil/perfil_publico.py`, com o Sobre e o avatar juntos. Outra opção é um módulo novo só para o avatar.
