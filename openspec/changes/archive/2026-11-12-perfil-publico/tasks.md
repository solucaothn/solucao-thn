# Tarefas

Apply em duas partes:
- **Parte A (Xano):** grupos 1 a 3, até o teste real.
- **Parte B (frontend):** grupos 4 a 7.

O dry-run e o push são feitos pelo Higor.

## 1. Preparação

- [x] 1.1 (manual) Responder às dúvidas 1 a 3 do `design.md` e ajustar a spec, se alguma resposta mudar o comportamento. Verificação: o `design.md` tem as respostas e o `openspec validate perfil-publico --strict` passa.
- [x] 1.2 Pedir confirmação ao Higor e rodar `xano workspace pull -d ./xano`. Verificação: `git status -- xano` sem alterações além das de formatação já conhecidas.
  - Pull feito pelo Higor. Além da formatação, o diff mostra divergências antigas e conhecidas entre o painel e o Git, que já são pendência do grupo e não são desta change: `signup_pending` sem os valores padrão, `donation_photo.photo` opcional, `signup_POST` com `tags` e o `contact_email_GET.xs` duplicado. Elas não entram no commit desta change.

## 2. Endpoint no Xano (Parte A)

- [x] 2.1 Consultar no Xano Developer MCP a sintaxe da paginação com metadados, do filtro de formatação de data com fuso e de `int page?=1`. Verificação: as respostas anotadas no `design.md` (decisões 2 e 3).
- [x] 2.2 Escrever `xano/api/catalog/catalog/donations/donor_GET.xs` com as decisões 1 a 4. Verificação: validação do arquivo no Xano Developer MCP sem erros.
- [x] 2.3 Mostrar ao Higor o arquivo e o `git diff -- xano` e parar antes do dry-run. Verificação: o diff mostra só o arquivo novo.
  - Desta change, o diff traz só o `donor_GET.xs`. As outras diferenças em `xano/` são as divergências conhecidas da 1.2. O critério final é o dry-run, feito pelo Higor na 2.4.
- [x] 2.4 (manual) O Higor roda `xano workspace push -d ./xano --dry-run`, revisa e faz o push. Verificação: o endpoint aparece no painel do Xano.
  - Dry-run só com `CREATE catalog/donations/donor GET`. Push feito (“Synced 1 GUIDs”).
- [x] 2.5 (manual) Pull pós-push, para o `guid` do endpoint novo. Verificação: o `donor_GET.xs` ganhou só a linha `guid`.
  - Ganhou a linha `guid`. O Xano também refez a formatação de duas expressões, sem mudar a lógica:
    - o `page_total` passou a ter um filtro por linha;
    - o objeto `donor` da resposta ficou entre três crases.
  - O arquivo continua válido no Xano Developer MCP.

## 3. Teste real (Parte A)

- [x] 3.1 Escrever `scripts/teste_perfil_real.py` com os cenários PP1 a PP10 (decisão 5), sem imprimir nomes, e-mails, URLs nem corpos de resposta. Verificação: `python -m py_compile scripts/teste_perfil_real.py` e leitura do script pelo Higor.
- [x] 3.2 (manual) O Higor roda o script contra o Xano real. Verificação: todos os cenários OK, anotados aqui.
  - 10 de 10 OK, com a doação 17 (4 itens) e, no PP9, a doação 23.
- [x] 3.3 Documentar o endpoint e o teste real no `docs/guia-do-colaborador.md`, numa seção sobre o perfil público de quem doa dentro da seção 8. Verificação: o texto bate com a decisão 4 e com os cenários do script.

## 4. Cliente e estado (Parte B)

- [x] 4.1 Criar em `doafacil/perfil_doador.py` o cliente `fetch_donor_profile` e a validação da resposta (decisão 6), reutilizando o `_parse_donations` da home. Verificação: testes em `tests/test_donor_profile.py` da URL, do 200, do 404, do 429, de resposta inválida e de campos extras ignorados.
- [x] 4.2 Criar o `DonorProfileState`, com o `load_profile`, o `go_to_page`, o “membro desde” por extenso e o contador “1 item” ou “N itens”. Verificação: testes do id inválido sem requisição, do carregamento, do não encontrado, do erro, da troca de página e do erro na troca de página.

## 5. Página (Parte B)

- [x] 5.1 Criar o `back_link_header` em `doafacil/chat.py` e manter o `back_home_header()` como caso dele (decisão 7). Verificação: os testes atuais do cabeçalho do chat e do detalhe continuam passando, mais um teste do “Voltar à doação” em `#007A42`.
- [x] 5.2 Montar a página do perfil da decisão 8: o cartão de identificação, a lista, o contador, a paginação, o estado vazio, os estados de carregamento e erro e a animação. Verificação: testes de componente de cada parte e da ausência de foto, selo, chat, avaliações e e-mail.
- [x] 5.3 Registrar a rota `/doacao/[id]/quem-doa` (decisão 10). Verificação: teste da rota e do `on_load`, e `reflex compile` sem erros.

## 6. Detalhe da doação (Parte B)

- [x] 6.1 Transformar o cartão “Quem doa” do detalhe em link para o perfil (decisão 9). Verificação: testes do `href`, do rótulo “Ver perfil de <nome>” e do foco, mais a atualização dos testes atuais do detalhe que proíbem o link para o perfil.

## 7. Documentação e verificação (Parte B)

- [x] 7.1 Escrever a seção “Perfil público de quem doa” do `docs/design/README.md` (frames, diferenças aprovadas, itens que não entram) e atualizar a seção do detalhe sobre o cartão “Quem doa”. Verificação: o texto bate com as specs delta.
- [x] 7.2 Rodar `python -m unittest discover -s tests`, `openspec validate perfil-publico --strict` e `reflex compile`, e mostrar o `git diff --stat`. Verificação: tudo passa.
- [x] 7.3 (manual) No navegador, em 1512 px e 360 px, conferir:
  - o perfil a partir do cartão “Quem doa”;
  - a identificação;
  - o contador, os cartões e “Acessar”;
  - a paginação com mais de 12 doações;
  - o estado vazio, se possível;
  - “Voltar à doação”;
  - “Doação não encontrada” para um id inválido;
  - a ausência de rolagem horizontal e o contraste.

  Verificação: os itens conferidos e anotados.

  - **Conferido pelo Higor no navegador:** o perfil a partir do “Quem doa”, a identificação, o contador, os cartões, “Acessar”, “Voltar à doação”, “Doação não encontrada” e o celular.
  - **Não conferido no navegador:** a paginação, porque não havia doador com mais de 12 doações, e o estado vazio, que quase nunca aparece porque a doação de origem entra na lista. Os dois estão cobertos só pelos testes automatizados de `tests/test_donor_profile.py`.
