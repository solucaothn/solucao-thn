# Proposal

## Why

Abaixo de 992 px o site não tem menu: os links do cabeçalho da home ficam só no desktop e somem. Fora da home, da `/explorar` e da `/categorias`, o cabeçalho tem só o logotipo e “Voltar”, sem acesso à conta, a “Quero Doar” nem às mensagens. No celular, quem está no detalhe de uma doação ou em Minhas doações não tem como ir a outra parte do site, a não ser voltando.

## What Changes

- **Menu do celular (abaixo de 992 px):** um botão ☰, com o rótulo “Abrir menu” e 44 px de área de toque, abre um painel lateral.
  - **Padrão do painel:** é o mesmo `rx.dialog` lateral da gaveta de Categorias. Prende o foco, fecha com o X, com Esc e com clique fora, e devolve o foco ao ☰.
  - **Itens para todos:** Explorar doações, Como funciona, Categorias (leva a `/categorias`) e Quero Doar.
  - **Com sessão:** a foto ou a inicial e o primeiro nome, depois Minhas doações, Mensagens (com o total de não lidas quando já estiver carregado), Editar perfil e Sair.
  - **Sem sessão:** Entrar.
- **Cabeçalho comum:** as páginas que hoje têm só o logotipo, ou o logotipo e “Voltar”, ganham à direita os controles do site:
  - no desktop, “Entrar” ou o menu da conta, e “Quero Doar”;
  - abaixo de 992 px, só o ☰.
  - Os links “Voltar” e as posições atuais continuam iguais, e o logotipo fica centralizado.
  - Isso vale para o detalhe da doação, o perfil de quem doa, o chat, Minhas doações, Editar doação, Editar perfil, o cadastro de doação e as páginas institucionais.
- **Home, `/explorar` e `/categorias`:** o desktop (992 px ou mais) fica igual. Abaixo de 992 px, a barra mostra o logotipo, “Entrar” ou o menu da conta e o ☰. “Quero Doar” e os links do menu passam para o painel.
- **Exceções:**
  - As telas de login, cadastro de conta e recuperação de senha mantêm o cabeçalho só com o logotipo, porque são fluxos de autenticação. Um menu com “Entrar” ou “Sair” ali só competiria com o formulário.
  - No cadastro de doação, “Quero Doar” não aparece no cabeçalho do desktop, porque é a própria página.
- **Mensagens no painel:** “Mensagens” entra no painel do celular, inclusive nas páginas que não têm o botão flutuante (detalhe, chat, Minhas doações, Editar doação e cadastro de doação). Isso muda a regra atual “o cabeçalho MUST NOT mostrar Mensagens”, que passa a valer para a barra e para o menu da conta, e não para o painel.
- **Diferenças com o Figma:** ficam registradas no `docs/design/README.md`. O Figma não desenha o celular nem controles de conta nessas páginas.
- **Fora do escopo:**
  - mudar o desktop da home, da `/explorar` e da `/categorias`;
  - mudar os fluxos de autenticação;
  - atualizar o total de não lidas automaticamente;
  - qualquer mudança no Xano.

## Capabilities

### New Capabilities

- `backend-request-budget`: menos pedidos ao Xano (10 a cada 20 s no plano grátis). Os dados públicos ficam guardados no servidor por 60 s, o 429 tem uma nova tentativa, e o cancelamento não vira erro.
- `site-navigation`: o menu do celular (☰ e painel) e o cabeçalho comum com os controles do site nas páginas com logotipo centralizado.

### Modified Capabilities

- `public-home`: a apresentação e o menu da conta passam a separar o desktop (como hoje) do celular (barra com conta e ☰).
- `donation-explore`: o cabeçalho de Explorar abaixo de 992 px passa a mostrar a conta e o ☰, com “Quero Doar” no painel.
- `institutional-pages`: a estrutura comum passa a incluir os controles do site no cabeçalho.
- `donation-chat-interface`: “Mensagens” passa a ser permitido no painel do menu do celular.
- `donation-creation`: a seta de retorno do cadastro passa para a linha do logotipo (rodada 3).
- `donation-detail`: a falha do detalhe ganha “Tentar novamente”.
- `donation-categories`: as categorias são buscadas uma vez e reaproveitadas, e a falha ganha “Tentar de novo” (rodada 1 do roteiro: limite de 10 pedidos a cada 20 s do Xano).

## Impact

- **Código:**
  - `doafacil/cabecalho.py`;
  - um módulo novo, `doafacil/navegacao.py` (painel e cabeçalho centralizado);
  - `doafacil/chat.py`: o `back_link_header` e o `back_home_header` mudam de módulo;
  - `doafacil/doafacil.py`, `explorar.py`, `categorias.py` e `institucional.py`;
  - `detalhe_doacao.py`, `perfil_doador.py`, `minhas_doacoes.py`, `editar_perfil.py` e `cadastro_doacao.py`.
- **`on_load`:** as páginas com o cabeçalho novo que ainda não carregam a conta ganham o `LoginState.load_account`. Isso acrescenta um `GET auth/me` por carregamento quando há sessão; a foto continua sendo pedida uma vez por sessão. Nenhuma página ganha a consulta de não lidas.
- **Testes:** `tests/test_cabecalho.py`, um teste novo do menu e ajustes nos testes de cabeçalho das páginas.
- **Documentação:** `docs/design/README.md` e o guia do colaborador.
- **Sem mudanças** no Xano, nas APIs e nas dependências.
