# Tarefas

Apply em duas partes:
- **Parte A (Xano):** grupos 1 a 4, até o teste real.
- **Parte B (frontend):** grupos 5 a 9.

O dry-run e o push são feitos pelo Higor.

## 1. Preparação

- [ ] 1.1 (manual) Responder às dúvidas 1 a 6 do `design.md` e ajustar a spec, o design e estas tarefas se alguma resposta mudar o comportamento. Verificação: o `design.md` tem as respostas e o `openspec validate minhas-doacoes --strict` passa.
- [ ] 1.2 Pedir confirmação ao Higor e rodar `xano workspace pull -d ./xano`. Verificação: `git diff --ignore-all-space --ignore-cr-at-eol --stat -- xano` mostra só as divergências antigas e conhecidas.

## 2. Endpoints no Xano (Parte A)

- [ ] 2.1 Consultar no Xano Developer MCP a sintaxe do limite de tamanho de texto (`max:`), do enum de valor único, da condição com “ou” no `where` e do `db.bulk.delete`. Verificação: as respostas anotadas no `design.md`.
- [ ] 2.2 Escrever `xano/api/catalog/catalog/donations/mine_GET.xs` (decisão 1). Verificação: validação do arquivo no Xano Developer MCP sem erros.
- [ ] 2.3 Escrever `xano/api/catalog/catalog/donations/mine/item_GET.xs` (decisão 2). Verificação: validação no MCP sem erros.
- [ ] 2.4 Alterar `donations_PATCH.xs` (decisão 3), `status_PATCH.xs` (decisão 4, se a dúvida 1 for aprovada) e `donations_DELETE.xs` (decisão 5, se a dúvida 5 for aprovada). Verificação: validação no MCP sem erros e um `git diff -- xano` só com essas mudanças.
- [ ] 2.5 Mostrar ao Higor os arquivos e o `git diff -- xano` e parar antes do dry-run. Verificação: o diff tem só os arquivos desta change, além das divergências conhecidas.
- [ ] 2.6 (manual) O Higor roda `xano workspace push -d ./xano --dry-run`, revisa e faz o push. Verificação: só os CREATE e UPDATE esperados no dry-run.
- [ ] 2.7 (manual) Pull pós-push, para os `guid` dos endpoints novos. Verificação: os arquivos novos ganharam a linha `guid`, sem mudar a lógica.

## 3. Teste real e documentação do backend (Parte A)

- [ ] 3.1 Escrever `scripts/teste_minhas_doacoes_real.py` com os cenários MD1 a MD19 (decisão 6), reaproveitando os auxiliares do `teste_chat_real.py`, sem imprimir nomes, e-mails, URLs nem corpos de resposta, e desfazendo a edição e o status no fim. Verificação: `python -m py_compile scripts/teste_minhas_doacoes_real.py` e a leitura do script pelo Higor.
- [ ] 3.2 Documentar no `docs/guia-do-colaborador.md` os endpoints novos, as mudanças no `PATCH`, no status e no `DELETE`, e como rodar o teste real. Se a dúvida 5 for aprovada, tirar a pendência das fotos órfãs da seção 7. Verificação: o texto bate com as decisões 1 a 6.

## 4. Verificação real (Parte A)

- [ ] 4.1 (manual) O Higor roda o script contra o Xano real. Verificação: todos os cenários OK, anotados aqui.

## 5. Cliente e estado da lista (Parte B)

- [ ] 5.1 Criar em `doafacil/minhas_doacoes.py` o cliente da decisão 7, com a validação das respostas. Verificação: testes em `tests/test_my_donations.py` da URL e do token de cada chamada, do 200, 400, 401, 403, 404 e 429, de resposta inválida e de campos extras ignorados.
- [ ] 5.2 Criar o `MyDonationsState` (decisão 8): `load_page` com a proteção de login, `go_to_page`, ações com confirmação, recarga depois da ação e 401 levando a `/login`. Verificação: testes de sem token sem requisição, do carregamento, do erro, da troca de página, de cada ação e do cancelamento sem requisição, da exclusão que volta uma página, do bloqueio com uma ação em andamento e do 401.

## 6. Página Minhas doações (Parte B)

- [ ] 6.1 Montar o cartão da doação com selo, menu e “Ver anúncio” (decisão 9) e a confirmação (decisão 10). Verificação: testes das ações por status, do rótulo acessível do menu, do “Ver anúncio” só nas disponíveis, da ausência do NOVO e do texto de cada confirmação, e o contraste dos três selos calculado e anotado no `docs/design/README.md`.
- [ ] 6.2 Montar a página da decisão 11: cabeçalho, título, cartão da pessoa, grade, paginação, estado vazio, carregamento, erro, aviso e animação. Registrar a rota `/minhas-doacoes`. Verificação: testes de componente de cada parte e da ausência de foto, e-mail, “Sobre”, “Compartilhar”, “Editar perfil”, avaliações, selo de verificação e chat, teste da rota e do `on_load`, e `reflex compile` sem erros.
- [ ] 6.3 Escrever no `docs/design/README.md` a seção “Minhas doações”, com o frame `Group 6`, as diferenças aprovadas e os itens que não entram. Verificação: o texto bate com a spec delta.

## 7. Link no cabeçalho da home (Parte B)

- [ ] 7.1 Acrescentar “Minhas doações” ao cabeçalho logado da home (decisão 12) e atualizar o teste atual do cabeçalho. Verificação: testes do link com login, da ausência sem login, do rótulo acessível no celular e de “Mensagens” continuar fora do cabeçalho.

## 8. Página de edição (Parte B)

- [ ] 8.1 Criar o `EditDonationState` e a página `/minhas-doacoes/[id]/editar` (decisão 13), com a rota. Verificação: testes de sem token, de id inválido sem requisição, de não encontrada, de concluída sem formulário, do preenchimento, do valor fora das opções, de cada validação sem requisição, do salvar com sucesso e o aviso na lista, do erro que mantém os valores, e da animação `auth-card-enter`.
- [ ] 8.2 Atualizar no `docs/design/README.md` a seção “Minhas doações” com a página de edição. Verificação: o texto bate com a spec delta.

## 9. Verificação final

- [ ] 9.1 Rodar `python -m unittest discover -s tests`, `openspec validate minhas-doacoes --strict` e `reflex compile`, e mostrar o `git diff --stat`. Verificação: tudo passa.
- [ ] 9.2 (manual) No navegador, em 1512 px e 360 px, conferir:
  - a entrada sem login (vai para `/login`);
  - o link no cabeçalho da home;
  - o cartão da pessoa, os contadores e a grade com os selos;
  - o menu pelo teclado e cada ação com a confirmação;
  - os contadores atualizados depois de cada ação;
  - a edição com sucesso e com erro;
  - o estado vazio, com uma conta sem doações;
  - a paginação, com mais de 6 doações;
  - nenhuma rolagem horizontal e o contraste.

  Verificação: os itens conferidos e anotados.
