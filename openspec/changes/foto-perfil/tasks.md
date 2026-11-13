# Tarefas

Apply em duas partes:
- **Parte A (Xano):** grupos 1 a 4, até o teste real.
- **Parte B (frontend):** grupos 5 a 9.

O dry-run e o push são feitos pelo Higor.

## 1. Preparação

- [x] 1.1 (manual) Responder às dúvidas 1 a 7 do `design.md` e ajustar a spec, o design e estas tarefas se alguma resposta mudar o comportamento. Verificação: o `design.md` tem as respostas e o `openspec validate foto-perfil --strict` passa.
- [x] 1.2 Pedir confirmação ao Higor e rodar `xano workspace pull -d ./xano`. Verificação: `git diff --ignore-all-space --ignore-cr-at-eol --stat -- xano` mostra só as divergências antigas e conhecidas.
  - Pull feito pelo Higor. O diff sem espaços mostra só as divergências antigas, que não são desta change. Os `guid` da tabela `user` e dos seis endpoints de leitura estão no lugar.

## 2. Xano (Parte A)

- [x] 2.1 Consultar no Xano Developer MCP as propriedades do arquivo de entrada (`name`, `size`, `mime`), a sintaxe de “termina com” e de minúsculas para a extensão, o `storage.delete_file` e a leitura de `photo.path` de um campo nulo. Verificação: as respostas anotadas no `design.md`.
- [x] 2.2 Acrescentar `photo` à tabela `user` (decisão 1). Verificação: validação no MCP e o `guid` da tabela mantido.
- [x] 2.3 Escrever `auth/profile/photo_POST.xs` e `photo_DELETE.xs` (decisões 2 e 3). Verificação: validação no MCP sem erros.
- [x] 2.4 Acrescentar a URL da foto ao `profile_GET.xs`, `mine_GET.xs`, `donor_GET.xs`, `detail_GET.xs`, `chat/conversations_GET.xs` e `chat/messages_GET.xs` (decisão 4). Verificação: validação no MCP, os `guid` mantidos, nenhuma consulta nova ao banco e a foto como único campo novo.
- [x] 2.5 Mostrar ao Higor os arquivos e o `git diff -- xano` e parar antes do dry-run. Verificação: o diff tem só os arquivos desta change, além das divergências conhecidas.
- [x] 2.6 (manual) O Higor roda o dry-run, revisa e faz o push. Verificação: no dry-run, o ADD_FIELD em `user`, 2 CREATE (a foto, com POST e DELETE) e 6 UPDATE.
  - Dry-run conferido pelo Higor: o ADD_FIELD em `user`, 2 CREATE (`auth/profile/photo`, com POST e DELETE) e 6 UPDATE (`auth/profile` GET, `donations/mine`, `donations/donor`, `donations/detail`, `chat/conversations` e `chat/messages`). Push feito.
- [x] 2.7 (manual) Pull pós-push. Verificação: os endpoints novos ganharam só o `guid`, e os alterados não mudaram de lógica.
  - Os dois endpoints novos ganharam o `guid` (`zg2NVqsaRsxoYbwROPSIVL8HUCg` no POST e `bOuUm83kecK6ENuEw8HCQxNnUY0` no DELETE), mantiveram os comentários e continuam válidos no MCP. A única outra diferença foi o Xano juntar a cadeia da extensão numa linha só.

- [ ] 2.8 (manual) Correção depois do teste real 4.1 (FP2): o `photo_POST.xs` passa a guardar com `create_attachment` e conferir o tipo pelo `.mime` e o tamanho pelo `.size` do objeto guardado, com “Escolha uma foto.” para o envio sem arquivo. O Higor roda o dry-run e o push e depois o pull. Verificação: no dry-run, só o UPDATE do `auth/profile/photo` (POST); depois do pull, o arquivo sem mudança de lógica e com o mesmo `guid`.

  - **Resultado da 2.8:** com o `create_attachment` publicado, o FP2 passou a dar 403 “Not supported. Please upgrade your Xano instance.”. O plano gratuito do Xano não tem esse recurso. A correção segue na 2.9.
- [ ] 2.9 (manual) Segunda correção: o `photo_POST.xs` volta ao `storage.create_image` (os mesmos parâmetros do `publish_POST.xs`) dentro de um `try_catch`, que dá 400 de formato quando ele falha, e confere o `.mime` e o `.size` do arquivo guardado. O Higor roda o dry-run e o push e depois o pull. Verificação: no dry-run, só o UPDATE do `auth/profile/photo` (POST); depois do pull, o mesmo `guid`.

## 3. Teste real e documentação do backend (Parte A)

- [x] 3.1 Escrever `scripts/teste_foto_perfil_real.py` com os cenários FP1 a FP12 (decisão 5). Ele gera as imagens de teste, não imprime nomes, e-mails, URLs nem corpos de resposta e restaura a foto num `finally`. Verificação: `py_compile` e a leitura do script pelo Higor.
- [x] 3.2 Ajustar o PP1 (`teste_perfil_real.py`), o MD2 (`teste_minhas_doacoes_real.py`) e o EP2, o EP3 e o EP11 (`teste_editar_perfil_real.py`) para aceitar `photo`. Verificação: `py_compile` dos três.
- [x] 3.3 Documentar no `docs/guia-do-colaborador.md` os endpoints de foto, o limite, os formatos, a URL da foto nas respostas e como rodar o teste real. Verificação: o texto bate com as decisões 1 a 5.

## 4. Verificação real (Parte A)

- [ ] 4.1 (manual) O Higor roda o `teste_foto_perfil_real.py` e, de novo, os três scripts ajustados. Verificação: todos os cenários OK, anotados aqui.
  - **Primeira rodada:** perfil público com 9 de 9, Minhas doações com 20 de 20 e editar perfil com 13 de 13.
  - **Foto:** o FP1 passou, mas o FP2 falhou. Um PNG válido recebeu 400 “Envie uma imagem JPG, PNG, GIF ou WEBP.”. A correção está na 2.8 e na seção “Correção depois do teste real 4.1” do design. É preciso rodar o `teste_foto_perfil_real.py` de novo depois da 2.8.
  - **Terceira rodada da foto, depois da 2.9:** 10 de 13. FP2, FP3, FP5, FP7 a FP10 e FP12 passaram.
    - O FP4 falhou porque o Xano recusa o envio sem arquivo antes do endpoint (“Missing param: photo”).
    - O FP6 e o FP11 falharam porque as URLs respondem 303 e o script não seguia o redirecionamento.
    - O script foi ajustado (veja “Terceira rodada do teste real” no design). O `photo_DELETE.xs` não mudou. É preciso rodar de novo.

## 5. Avatar e leitura da foto (Parte B)

- [ ] 5.1 Criar o componente `avatar` e o `parse_photo_url` (decisão 6) e fazer o `_avatar` do chat delegar para ele. Verificação: testes da foto (redonda, `cover`, `alt` com o primeiro nome), da inicial sem foto, do tamanho e das URLs inválidas.
- [ ] 5.2 Ler a foto nos parsers e estados do perfil público, de “Minhas doações”, do detalhe e do chat (decisão 7). Verificação: testes de cada parser (foto, nulo e tipo inválido) e de cada estado.

## 6. Foto nas telas que já existem (Parte B)

- [ ] 6.1 Trocar o círculo pelo avatar no perfil público e no cartão de “Minhas doações”. Verificação: testes de componente com e sem foto.
- [ ] 6.2 Acrescentar o avatar de 48 px ao cartão “Quem doa” do detalhe e o de 38 px ao cabeçalho da conversa, e usar o avatar na lista do chat (dúvida 5). Verificação: testes de componente e os testes atuais do detalhe e do chat atualizados.

## 7. Seção “Foto” em /perfil/editar (Parte B)

- [ ] 7.1 Criar o cliente e os eventos `upload_photo` e `remove_photo` no `EditProfileState` (decisão 8). Verificação:
  - testes do `multipart` com o token;
  - de 200, 400 (as duas mensagens), 401 e 429;
  - da prévia atualizada;
  - dos valores do formulário mantidos;
  - do arquivo recusado sem requisição.
- [ ] 7.2 Montar a seção “Foto” (decisões 8 e 9), com o aviso, “Alterar foto”, “Remover foto” só com foto, as mensagens acessíveis e o texto novo do quadro. Verificação: testes de componente, `reflex compile` sem erros e os testes atuais do formulário atualizados.

## 8. Documentação (Parte B)

- [ ] 8.1 Atualizar no `docs/design/README.md` a “Editar perfil” (a seção Foto e a diferença do Figma), o perfil público, “Minhas doações”, o detalhe e o chat. Atualizar também o `docs/guia-do-colaborador.md`. Verificação: o texto bate com as specs delta.

## 9. Verificação final

- [ ] 9.1 Rodar `python -m unittest discover -s tests`, `openspec validate foto-perfil --strict` e `reflex compile`, e mostrar o `git diff --stat`. Verificação: tudo passa.
- [ ] 9.2 (manual) No navegador, em 1512 px e 360 px, conferir:
  - enviar uma foto, pelo mouse e pelo teclado, com a prévia atualizada;
  - um arquivo grande ou de outro formato, recusado com a mensagem;
  - “Remover foto”;
  - a foto na prévia, em “Minhas doações”, no perfil público, no “Quem doa” e no chat (lista e cabeçalho), vista também por outra conta;
  - a inicial em todos esses lugares, para uma conta sem foto;
  - nenhuma rolagem horizontal e o contraste.

  Verificação: os itens conferidos e anotados.
