# Tarefas

Os comandos `git` e `xano` são do Higor. O agente edita os arquivos, valida o XanoScript no Xano Developer MCP e para antes de qualquer push. O log `[xano]` continua desligado por padrão.

## 1. Categorias (Móveis liberada, Alimentos sem exclusão)

- [x] 1.1 Tirar `EXCLUDED_CATEGORY_NAMES` de `cadastro_doacao.py`, aceitando todas as categorias válidas, e trocar o ícone de “moveis” para `sofa` em `explorar.py` (decisões 1 e 2). Ajustar os testes que esperavam a exclusão e acrescentar casos: “Móveis” presente no cadastro, na edição e na lista; item sem id ou sem nome ignorado; ícone `sofa`. Verificação: `tests.test_donation_creation`, `tests.test_categories`, `tests.test_explore` e `tests.test_my_donations` passam.
- [x] 1.2 Atualizar `docs/design/README.md` e `docs/guia-do-colaborador.md`, que hoje falam da exclusão de Alimentos e Móveis. Verificação: o grep por “Alimentos e Móveis” em `docs/` não acha mais regra de exclusão.

## 2. Links, estado vazio e “Tentar de novo”

- [x] 2.1 Trocar o destino de “Explorar outras doações” em `perfil_doador.py` para `/explorar`. Verificação: um teste confere o `href`.
- [x] 2.2 Criar `retry_button` em `cabecalho.py` (decisão 4). Verificação: um teste confere 44 px, o texto “Tentar de novo” e a cor `#166B3B`.
- [x] 2.3 Explorar vazia sem filtros: a frase de convite e o botão “Quero Doar”, para `/cadastro-doacao` com sessão e `/login?next=/cadastro-doacao` sem sessão. Com filtros, só “Limpar filtros” (decisão 3). Verificação: testes do componente para os dois casos.
- [x] 2.4 “Tentar de novo” na contagem e nas recentes da home (`HomeState.load_home_data`), em Minhas doações (`MyDonationsState.load_page`) e no erro do perfil de quem doa (`DonorProfileState.load_profile`), sem botão no “não encontrada” nem na lista vazia. Verificação: testes do componente de cada página.

## 3. Orçamento de pedidos (chat e perfil de quem doa)

- [x] 3.1 Chat (decisão 5): mensagens a cada 25 s; a lista não se atualiza com conversa à mostra; as mensagens não se atualizam com a lista à mostra no celular; `back_to_list` consulta a lista uma vez e mescla. Ajustar os testes de 15 s e de lista “com ou sem conversa aberta” e acrescentar os novos. Verificação: `tests.test_chat` passa.
- [x] 3.2 Perfil de quem doa no cache público (espaço `DONOR` em `DONATION_NAMESPACES`), mais a invalidação ao salvar o perfil ou trocar e remover a foto (decisão 6). Verificação: testes de duas leituras em 60 s fazendo um pedido só, de falha não guardada, de `invalidate_donations()` descartando o espaço e da edição do perfil invalidando; `tests.test_donor_profile`, `tests.test_cache_publico` e `tests.test_edit_profile` passam.
- [x] 3.3 Atualizar no `docs/guia-do-colaborador.md` o orçamento do chat (25 s e a lista parada com conversa aberta) e o cache do perfil de quem doa. Verificação: o texto bate com as deltas.

## 4. Texto, `.gitignore` e testes antigos

- [x] 4.1 Central de ajuda: a resposta “Posso editar uma doação já publicada?” passa a dizer que a entrega é sempre “A combinar”. Verificação: um teste confere o texto e a ausência de “mudar … entrega”.
- [x] 4.2 `.gitignore` com `.env` e `.claude/settings.local.json`. Verificação: as duas linhas estão no arquivo.
- [x] 4.3 `tests/test_acabamento.py`: o escape na linha 133 e `tobytes()` no lugar de `getdata()` na 239 (decisão 9). Verificação: `python -W error::SyntaxWarning -W error::DeprecationWarning -m unittest tests.test_acabamento` passa.

## 5. Publicação no Xano (só o arquivo; o push é do Higor)

- [x] 5.1 Aplicar em `xano/api/catalog/catalog/donations/publish_POST.xs` os limites e os valores da decisão 7, sem mexer no stack. Verificação: o Xano Developer MCP valida o arquivo sem erros, e um teste local lê o arquivo e confere os quatro inputs.
- [x] 5.2 Criar `scripts/teste_publicar_limites_real.py` (decisão 8), com P1 e P2 sem fotos, e documentá-lo no guia. Verificação: `python scripts/teste_publicar_limites_real.py --help` mostra o uso; o script não roda sem `XANO_API_URL`.
- [x] 5.3 (manual, Higor) `xano workspace push -d ./xano -i "api/catalog/catalog/donations/publish_POST.xs" --dry-run`. Verificação: só 1 item, o UPDATE de `catalog/donations/publish` (POST, grupo Catalog). Com o OK do grupo, o push e depois o script da 5.2, com P1 e P2 OK.
  - Resultado (Higor): o push teve 1 UPDATE, e o `teste_publicar_limites_real.py` deu 2/2 OK.

## 6. Verificação automatizada e manual

- [x] 6.1 Rodar `python -m unittest discover -s tests`, `reflex compile` e `openspec validate correcoes-finais --strict`. Verificação: tudo passa, e os resultados ficam anotados aqui.
  - Resultados (2026-11-22):
    - 751 testes OK, nenhum pulado, também com `-W error::SyntaxWarning`;
    - `reflex compile` OK;
    - `openspec validate correcoes-finais --strict` OK;
    - o Xano Developer MCP validou o `publish_POST.xs`. Ficou só um aviso que já existia no arquivo (o `db.add donation_photo` sem `as`, na linha 137).
- [x] 6.2 (manual, Higor) Roteiro no navegador. Verificação: os itens anotados aqui.
  - OK (Higor):
    - “Móveis” aparece com o ícone de sofá;
    - a Explorar vazia mostra o convite e o “Quero Doar”;
    - o chat vazio mostra o link para a Explorar;
    - a Ajuda tem o texto novo sobre a entrega na edição.
