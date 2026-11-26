# Tarefas

Os comandos `git` e `xano` são do Higor. Esta change não mexe em `xano/` e não acrescenta chamadas ao Xano. Para os testes com dados reais, `XANO_API_URL` e `XANO_AUTH_API_URL` ficam só no ambiente da sessão, sem gravar em nenhum arquivo.

## 1. Busca do cabeçalho no celular

- [x] 1.1 Em `explore_header()` (`doafacil/explorar.py`), trocar o `flex="1"` e o `style={"width": …}` do formulário por `flex=rx.breakpoints(initial="1 1 100%", md="1 1 0%")` (decisão 1). Verificação: um teste em `tests/test_explore.py` confere, no código gerado, a base de 100% abaixo de 992 px e de 0% a partir dela, e que o `width` do celular saiu.
- [x] 1.2 No navegador, em 360 px, abrir `/explorar` e `/categorias`, digitar na busca e buscar. Em 1280 px, conferir a busca na linha do logotipo. Verificação: `scrollWidth` igual a `clientWidth`, campo com largura maior que zero e o texto digitado aparecendo. Os resultados ficam anotados aqui.
  - Resultados (2026-11-26, Edge headless pelo DevTools, `reflex run --env prod`):
    - 360 px, `/explorar` e `/categorias`: a busca fica na linha de baixo (topo em 92 px; o logotipo vai até 84 px), com 328 px de largura e o campo com 196 px. O texto digitado aparece, o Enter abre `/explorar?q=mesa` e `scrollWidth` = `clientWidth` = 360. Antes, eram 416 px de rolagem e o campo com 0 px;
    - 1280 px: a busca fica na linha do logotipo (topo em 26 px), com 620 px de largura e o campo com 488 px, sem rolagem.

## 2. Chat: envio, edição e carregamentos

- [x] 2.1 `send_message` vira gerador e dá `yield` depois de ligar `is_sending`, depois das validações, para o envio e para a edição. O `_save_edit` deixa de ligar o estado (decisões 2 e 3). Verificação: testes em `tests/test_chat.py` mostram que o primeiro `yield` chega com `is_sending` ligado e nenhum pedido feito, no envio e na edição. Um segundo envio com `is_sending` ligado não faz pedido. Os testes de envio e edição que já existem continuam passando.
- [x] 2.2 `refresh_conversations`, `load_more_conversations` e `load_older_messages` viram geradores, com `yield` depois de ligar o carregamento. Verificação: testes mostram o carregamento ligado no primeiro `yield`, sem pedido, e desligado no fim, com sucesso e com falha, com um único pedido.
- [x] 2.3 O botão da falha da lista passa a ser “Tentar de novo”. Verificação: o teste da página confere o texto, e não há mais “Tentar novamente” em `doafacil/chat.py`.

## 3. Publicar doação e tentar de novo do cadastro

- [x] 3.1 Em `DonationCreateState.publish`, `yield` depois de ligar `is_publishing` e o `upload_progress`. Verificação: teste em `tests/test_donation_creation.py` com o primeiro `yield` chegando com `is_publishing` ligado, “Enviando sua doação...” e nenhum pedido. Numa falha, os dois são desligados. Um dado inválido não emite nada nem faz pedido.
- [x] 3.2 Em `load_initial_data`, `yield` depois de ligar `is_loading_data`. O botão da falha passa a ser “Tentar de novo”. Verificação: teste com o carregamento ligado antes dos pedidos e o mesmo número de pedidos de antes, e o texto do botão.
- [x] 3.3 Aviso legal com o texto novo e o link “Termos de uso” para `/termos` em outra aba (decisão 5). Título da etapa 5: “Como prefere que entrem em contato?”. Verificação: um teste confere o texto, o `href`, o `target="_blank"` e a ausência de “Taxas”. Outro confere o título.

## 4. Login, cadastro e recuperação de senha

- [x] 4.1 Em `LoginState`, `yield` depois de ligar o carregamento, depois das validações, em `login`, `signup`, `request_recovery_code`, `resend_recovery_code` (nos dois fluxos), `verify_recovery_code` (nos dois fluxos) e `confirm_recovery_password`. Verificação: testes em `tests/test_login.py`, `tests/test_signup.py` e `tests/test_password_recovery.py` mostram o carregamento ligado no primeiro `yield`, sem pedido feito. Os testes que esperavam `events == []` nas falhas passam a esperar só o envio de estado. Uma validação que falha continua sem emitir nada.
- [x] 4.2 Dica da verificação de e-mail: “Pode demorar um minutinho. Confira também a caixa de spam.” Verificação: o teste de `tests/test_password_recovery.py` confere o texto novo.

## 5. Tentar de novo com carregamento

- [x] 5.1 Criar `DonationDetailState.retry_donation` e usá-lo no botão da falha, agora “Tentar de novo” (decisão 4). Verificação: teste em `tests/test_donation_detail.py` com `view_state` igual a “loading” na hora e `load_donation` devolvido, e o texto do botão.
- [x] 5.2 Criar `CategoriesState.retry_categories` para a `/categorias`. Na gaveta da home, `HomeState.categories_loading` é ligado com `yield` em `reload_categories` e passado para a gaveta. Verificação: testes em `tests/test_categories.py` e `tests/test_public_home.py` com o carregamento ligado antes do pedido e um único pedido.

## 6. Textos e documentação

- [x] 6.1 `/seguranca`: o cartão “Recebi uma doação” e “a segurança e a transparência”. Ajuda: “vá com alguém”. Home: “Para você”. Verificação: testes em `tests/test_institucional.py` e `tests/test_public_home.py` conferem os textos novos e a ausência dos antigos.
- [x] 6.2 Atualizar `docs/design/README.md`, `docs/guia-do-colaborador.md` e `README.md` onde citam os textos que mudaram. Verificação: o grep por “Para você mesmo”, “ser contatado”, “Doei em uma doação”, “Tentar novamente” e “Olha também no spam” em `doafacil/`, `docs/` e `README.md` não acha nada.

## 7. Verificação final

- [x] 7.1 Rodar `python -m unittest discover -s tests` e `openspec validate correcoes-revisao --strict`. Verificação: tudo passa, e os resultados ficam anotados aqui.
  - Resultados (2026-11-26):
    - 814 testes OK (eram 790);
    - os módulos alterados também passam com `-W error::SyntaxWarning -W error::DeprecationWarning` (464 testes);
    - `openspec validate correcoes-revisao --strict` OK;
    - o build de produção (`reflex run --env prod`) compila sem erro.
- [ ] 7.2 Com o app rodando e o Xano real só no ambiente da sessão, abrir no navegador a home, a `/explorar` em 360 px, uma doação existente e o perfil público dela, e conferir o login com dados inválidos (“Entrando...” e depois a mensagem de erro). Verificação: os resultados ficam anotados aqui.
  - Parcial (agente, 2026-11-26). Desta máquina, o servidor não alcança o Xano: a rede corporativa intercepta o TLS com uma raiz própria, e o Python recusa a cadeia (`CERTIFICATE_VERIFY_FAILED`). Sem os dados reais, a home, a doação e o perfil mostram a mensagem de falha. Conferido no navegador mesmo assim:
    - login com dados inválidos: “Entrando...” desativado e depois “Não foi possível conectar ao serviço de autenticação. Tente novamente.”;
    - detalhe da doação: o “Tentar de novo” mostra “Carregando doação...” e volta à falha;
    - `/categorias`: o “Tentar de novo” mostra “Carregando categorias...” e volta à falha;
    - `/explorar` em 360 px: veja a 1.2.
  - Falta (Higor, numa rede sem interceptação de TLS): abrir uma doação existente e o perfil público dela, e repetir o login com dados inválidos para ver a mensagem “E-mail ou senha incorretos.”.
  - **Nota (arquivamento em 2026-11-26):** a change foi arquivada com esta tarefa em aberto, por decisão do grupo. O teste com dados reais será feito fora da rede corporativa, e o resultado fica anotado aqui.
