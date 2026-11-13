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

### Respostas do Higor

As sete recomendações foram aceitas:

1. A foto de perfil tem limite de 5 MB, conferido na tela e no Xano. As fotos de doação continuam sem limite.
2. O arquivo antigo é apagado do armazenamento (`storage.delete_file`) ao trocar ou remover a foto.
3. O quadro “Quem vê estas informações” usa o texto novo, que cita a foto.
4. “Remover foto” não pede confirmação.
5. O avatar entra no “Quem doa” do detalhe (48 px) e no cabeçalho da conversa (38 px).
6. O `start` do chat e o envio e a edição de mensagens não mudam.
7. `doafacil/sobre.py` passa a se chamar `doafacil/perfil_publico.py`.

## Consulta ao Xano Developer MCP (tarefa 2.1)

- **Entrada do arquivo:** `file? photo`. O `.name` do arquivo de entrada já é usado no `publish_POST.xs` (`filename = $file.name`).
- **Extensão:** `($input.photo.name ?? "")|to_lower|split:"."|last` e `["jpg", "jpeg", "png", "gif", "webp"]|in:$extension`.
  - O validador recusou o alias `lower` (como recusou o `div` antes) e aceitou `to_lower`.
  - A checagem vem antes do `storage.create_image`, que responde 500 para outros tipos.
- **Tamanho:** o `.size`, em bytes, do objeto que o `storage.create_image` devolve. A doc não garante essa propriedade no arquivo de entrada.
  - Acima de 5 MB (`5242880` bytes), um `conditional` apaga o arquivo novo, e uma `precondition` com `inputerror` responde 400. O teste real já mostrou que esse padrão dá 400.
- **Apagar:** `storage.delete_file { pathname = <path> }`, confirmado na doc (seção “Deleting & Replacing Files”).
- **Campo na tabela:** `image? photo?`, como o `photo` da tabela `donation`.
- **URL nas respostas:** o mesmo bloco do `recent_GET.xs`, que monta `$env.PUBLIC_BASE_URL ~ photo.path` e lança `ConfigurationError` sem a variável. Ele foi repetido nos seis endpoints, por ser o padrão já validado no projeto.
- **`GET auth/profile`:** passou a montar a resposta campo a campo. Antes ele devolvia o registro inteiro, e o campo `photo` do registro é o objeto do armazenamento, não a URL. O `PATCH auth/profile` não muda e continua sem `photo` na resposta.

## Correção depois do teste real 4.1 (FP2)

- **Sintoma:** um PNG válido, enviado no campo `photo` com o nome `foto-teste.png` e o tipo `image/png`, recebia 400 “Envie uma imagem JPG, PNG, GIF ou WEBP.”. A mesma mensagem servia para “sem arquivo” e para “formato inválido”, então não dava para saber qual checagem falhou.
- **Comparação com o `publish_POST.xs`, que funciona:**
  - lá, a entrada é `file[]? photos?`, enviada como `photos[]`. O endpoint não *confere* nenhuma propriedade do arquivo antes de guardar; só repassa `$file.name` como `filename`;
  - o script e o frontend enviam igual: o nome do campo bate com a entrada, e vão o nome do arquivo com extensão e o tipo do arquivo.
- **Causa mais provável:** a checagem da extensão **antes** de guardar, feita com `$input.photo.name|to_lower|split:"."|last` e `["jpg", …]|in:$extension`.
  - A doc do MCP não garante nenhuma propriedade do arquivo de entrada além do `.path`. A tabela de uploads lista a leitura de propriedades da entrada (como `.tmp_name`) entre os erros comuns.
  - A doc também não garante esse uso do `in`. Ela só garante `name`, `size`, `mime` e `type` no objeto que o armazenamento devolve.
  - Sem rodar no Xano, não dá para dizer qual das duas falhou. As mensagens agora separadas vão mostrar isso se o problema voltar.
- **Correção:**
  - sem arquivo, a resposta é 400 com “Escolha uma foto.”;
  - o arquivo é guardado primeiro com `storage.create_attachment`, que aceita qualquer tipo e não dá o 500 do `create_image`;
  - o tipo é conferido pelo `.mime` do objeto guardado, com comparações diretas (`image/jpeg`, `image/png`, `image/gif` e `image/webp`), sem o `in`;
  - o tamanho é conferido pelo `.size`;
  - fora das regras, o arquivo novo é apagado e a resposta é 400 com a mensagem de formato ou de tamanho.
  - A coluna `image?` aceita o objeto do `create_attachment`, como a doc confirma (“verified live”).
- **Script:** o FP4 passou a conferir também o envio sem arquivo (“Escolha uma foto.”).

## Segunda correção: o plano gratuito do Xano não tem `create_attachment`

- **Sintoma:** com a primeira correção publicada, o FP2 passou a receber **403 “Not supported. Please upgrade your Xano instance.”**. O `storage.create_attachment` **não existe no plano gratuito** do Xano. O `storage.create_image`, usado no `publish_POST.xs`, funciona.
- **Regra para o projeto:** nos endpoints, usar só o `storage.create_image` para guardar imagens. O `create_attachment`, que a doc do MCP recomenda como padrão, não está disponível na nossa instância.
- **Correção no `photo_POST.xs`:**
  - sem arquivo, continua o 400 com “Escolha uma foto.”;
  - guarda com `storage.create_image`, com os mesmos parâmetros do `publish_POST.xs` (`value = $input.photo`, `access = "public"`, `filename = $input.photo.name`), dentro de um `try_catch` (sintaxe `try_catch { try { … } catch { … } }`, confirmada na doc do MCP, tópico `syntax`, “Error Handling”);
  - se o `create_image` der erro (ele responde 500 para arquivos que não são imagem), o `catch` só marca a falha numa variável, e uma `precondition` com `inputerror` responde 400 com “Envie uma imagem JPG, PNG, GIF ou WEBP.”;
  - depois de guardar, o tipo é conferido pelo `.mime` (`image/jpeg`, `image/png`, `image/gif` ou `image/webp`) e o tamanho pelo `.size` (até 5 242 880 bytes). Fora disso, o arquivo novo é apagado e a resposta é 400 com a mensagem de formato ou de tamanho;
  - nenhuma propriedade da entrada é conferida antes de guardar.

## Terceira rodada do teste real (10 de 13)

- **FP4:** o Xano recusa o envio sem arquivo **antes** de executar o endpoint, com 400 “Missing param: photo”.
  - O FP4 passou a aceitar qualquer 400 nesse caso.
  - A precondição “Escolha uma foto.” fica como defesa, e a tela só envia com um arquivo escolhido.
  - A spec foi ajustada.
- **FP6 e FP11:** as URLs do armazenamento respondem **303** (redirecionamento). O script passou a seguir os redirecionamentos: “abre” é 200 no final, e “não abre” é 403, 404 ou 410 no final, ou erro.
- **FP11 (o arquivo parecia continuar existindo depois do `DELETE`):**
  - **Comparação:** o `photo_DELETE.xs` e o trecho do `photo_POST.xs` que apaga a foto antiga são **iguais**. Os dois leem a foto com `db.get user` **antes** de gravar e apagam com `storage.delete_file { pathname = $current.photo.path }`, no mesmo `conditional`. Não há diferença de ordem nem de formato.
  - **Diferença no teste:**
    - no FP6, o script conferiu a URL antiga, **nunca aberta antes**, e ela deu 404;
    - no FP11, conferiu a URL atual, que **já tinha sido aberta no FP6**, e recebeu 303 sem seguir o redirecionamento;
    - o 303 não prova que o arquivo existe, e um redirecionamento já visto pode ter ficado em cache.
  - **Decisão:** sem evidência de bug, o `photo_DELETE.xs` **não foi alterado**. O FP11 agora envia uma foto nova, nunca aberta, remove essa foto e confere a URL dela seguindo os redirecionamentos. Se ela ainda abrir, o bug é real e será corrigido com essa evidência.
