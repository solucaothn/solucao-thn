# Tarefas

Os comandos `git` e `xano` são feitos pelo Higor. Esta change não mexe no Xano.

## 1. Voltar à origem depois do login

- [x] 1.1 Criar `safe_next`, `current_path`, `login_url` e `login_redirect` em `doafacil/rotas.py` (decisão 1), com os testes de caminhos aceitos e recusados em `tests/test_acabamento.py`. Verificação: os testes passam.
- [x] 1.2 Trocar os `rx.redirect("/login")` dos handlers de páginas pelo `login_redirect` (decisão 2), deixando as exceções do fluxo de autenticação. Ajustar os testes que esperavam `/login` exato. Verificação: a suíte passa, e um teste confirma que não sobrou `rx.redirect("/login")` fora das exceções.
- [x] 1.3 Criar `LoginState.login_href` e `signup_href` e usá-los no “Entrar” do cabeçalho e do painel, no `chat_fab` e nos links entre login e cadastro. O `login` volta ao `next` seguro, e o cadastro leva o `next` até o login (decisão 2). Verificação: os testes de login com `next` seguro, com `next` inválido e pelo cadastro passam.

## 2. Página 404, títulos e favicon

- [x] 2.1 Criar a página 404 (`doafacil/nao_encontrada.py`) e registrá-la com `route="404"` (decisão 3). Verificação: o teste confere o cabeçalho, o título, os dois links, a animação e o registro.
- [x] 2.2 Pôr o `title` “… | DoaFácil” em todos os `add_page` (decisão 4). Verificação: o teste percorre todas as páginas registradas.
- [x] 2.3 Criar o `requirements-dev.txt` com o `pymupdf` (fora do `requirements.txt`) e o `scripts/gerar_favicon.py`, com a instalação explicada no topo. O Higor instala o PyMuPDF no `.venv`. Gerar `assets/favicon.ico`, `assets/favicon-32.png` e `assets/apple-touch-icon.png` e declará-los no `head_components` (decisão 4). Verificação: o teste dos arquivos e do `head` passa.
  - Feito: `requirements-dev.txt`, `scripts/gerar_favicon.py`, `FAVICON_HEAD` e os testes (o do `head` e o do PyMuPDF só no dev passam).
  - Arquivos gerados pelo Higor. O primeiro recorte por vão entre colunas pegava o logotipo inteiro (a ponta da folha passa por cima do “d”). Agora o recorte é por manchas de tinta, sem respiro no .ico e no PNG de 32 px. O teste dos arquivos deixou de ser pulado e passa: 729 testes OK.

## 3. Doação indisponível, chat vazio e contêiner

- [x] 3.1 Detalhe `not_found` com a explicação e os links “Ver outras doações” e “Voltar ao início” (decisão 5). Verificação: o teste passa, e “Doação não encontrada” continua.
- [x] 3.2 Link “Explorar doações” no chat vazio (decisão 6). Verificação: o teste passa.
- [x] 3.3 Contêiner de 1200 px com `HEADER_PADDING_X` no perfil de quem doa, no detalhe e no Editar perfil, sem mudar a grade do detalhe (decisão 7). Verificação: os testes do contêiner e da grade passam.

## 4. Documentação e verificação automatizada

- [x] 4.1 Atualizar `docs/guia-do-colaborador.md` (`next` seguro, como gerar o favicon e a página 404) e `docs/design/README.md` (404, favicon, detalhe indisponível, chat vazio e contêiner). Verificação: o texto bate com as specs delta.
- [x] 4.2 Rodar `python -m unittest discover -s tests`, `reflex compile` e `openspec validate acabamento --strict`. Verificação: tudo passa, e os resultados ficam anotados aqui.
  - Resultados: 729 testes OK (1 pulado: os arquivos do favicon, que esperam a 2.3), `reflex compile` OK (a rota 404 compilada é a página nova, e o `head` tem os dois links do favicon) e `openspec validate --strict` OK.

## 5. Verificação manual e commit

- [x] 5.1 (manual, Higor) Roteiro no navegador (entregue com a 4.2). Verificação: os itens anotados aqui.
  - OK: volta à origem depois do login; `next` externo vai para a home; 404 em português; doação indisponível com os links; títulos e ícone na aba; alinhamento.
- [ ] 5.2 Montar a lista de caminhos para o commit; o Higor confere com o `git diff --stat`. Verificação: entram só os arquivos desta change.
