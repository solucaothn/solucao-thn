# Proposta

## Por quê

Quem doa publica pelo `/cadastro-doacao`, mas depois não tem onde ver as próprias doações nem acompanhar o andamento delas. Os endpoints de status, edição e exclusão já existem no Xano, mas nenhuma tela os usa. A doação não pode ser marcada como reservada ou concluída, corrigida nem apagada. O Figma já tem a tela, no frame `Group 6` (`meu-perfil-1`).

## O que muda

- **Nova página `/minhas-doacoes`**, só com login. Sem login, leva a `/login`.
  - O link “Minhas doações” entra no cabeçalho logado da home, ao lado de “Olá, <primeiro nome>” e “Sair”.
  - “Voltar ao início” fica na linha do logotipo, em `#007A42`. O título “Minhas doações” fica à esquerda, em negrito e verde.
  - **Cartão da pessoa:** círculo com a inicial, primeiro nome, “Doações” (disponíveis e reservadas) e “Doações realizadas” (concluídas).
  - **Grade com todas as doações da pessoa**, de qualquer status, 6 por página, das mais novas para as mais antigas. Cada cartão tem foto, título, um selo de status (Disponível, Reservada ou Concluída) e um menu de ações.
  - **Estado vazio:** “Você ainda não tem doações” e o botão “Quero Doar”.
- **Ações sobre a própria doação**, com os endpoints que já existem:
  - **Reservar e concluir** (`PATCH catalog/donations/status`). Concluir pede confirmação, porque uma doação concluída não volta.
  - **Voltar a disponível:** o endpoint de status hoje **recusa** a volta de reservada para disponível. A ação só entra se o grupo aprovar essa transição (dúvida 1 do design).
  - **Apagar** (`DELETE catalog/donations`), com uma confirmação que avisa que as conversas e mensagens da doação também serão apagadas.
  - **Editar:** página `/minhas-doacoes/<id>/editar`, só com os campos de texto: título, descrição, categoria, condição, entrega e preferência de contato. As validações são as do cadastro. As fotos não são editáveis nesta change.
- **Xano:**
  - **Endpoint novo, com login,** que devolve numa só requisição a página das doações da pessoa logada, com o status de cada uma, e os dois contadores. Nunca devolve dados de outras pessoas.
  - **Leitura de uma doação própria para a edição**, de qualquer status. O detalhe público só mostra doações disponíveis (dúvida 4).
  - **O `PATCH catalog/donations` passa a aceitar** condição, entrega e preferência de contato, com as mesmas regras da publicação. Hoje ele só aceita categoria, título e descrição.
- **Apply em duas partes:** primeiro o Xano, com um teste real em script; depois o frontend.

### Do Figma, o que não entra

- Foto de perfil: fica só o círculo com a inicial.
- E-mail, “Sobre”, “Compartilhar link do perfil”, “Editar perfil”, avaliações, selo “Verificado” e botão de chat. Entram em outra change.

## Fora do escopo

- Editar, trocar ou remover fotos.
- Editar a cidade e a UF da doação, que continuam vindo do perfil.
- Interesse, escolha de quem recebe e avaliações.
- Página “Explorar doações”, busca e filtros dentro de “Minhas doações”.
- Mudar o detalhe público ou o perfil público, que continuam mostrando só doações disponíveis.

## Capacidades

### Novas capacidades

- `donation-management`: a gestão das próprias doações por quem doa. Cobre a listagem paginada com status e contadores, a mudança de status, a edição dos campos de texto, a exclusão e as páginas `/minhas-doacoes` e `/minhas-doacoes/<id>/editar`.

### Capacidades modificadas

- `donation-chat-interface`: o requisito “Entrada no chat pelo cabeçalho da home” deixa de dizer que o cabeçalho logado mostra **só** “Olá, <primeiro nome>” e “Sair”. Ele passa a incluir o link “Minhas doações”, e o link “Mensagens” continua fora. As duas páginas novas entram na lista de páginas sem o botão flutuante.

## Impacto

- **Xano:**
  - endpoints novos de listagem das próprias doações e de leitura de uma doação própria, no grupo Catalog;
  - o `donations_PATCH.xs` passa a aceitar mais campos;
  - conforme as dúvidas: o `status_PATCH.xs` (volta a disponível) e o `donations_DELETE.xs` (linhas de `donation_photo` órfãs).
  - Nenhuma tabela muda.
- **Frontend:**
  - um módulo novo, `doafacil/minhas_doacoes.py`, com o cliente, o estado e as duas páginas;
  - as rotas novas em `doafacil/doafacil.py`;
  - o link no cabeçalho logado da home;
  - reaproveitamento do `back_link_header`, do círculo com a inicial, das categorias e das validações do `cadastro_doacao.py`.
- **Script:** `scripts/teste_minhas_doacoes_real.py`, que precisa de login com duas contas.
- **Testes:** `tests/test_my_donations.py` e um ajuste no teste do cabeçalho da home.
- **Documentação:** `docs/design/README.md` e `docs/guia-do-colaborador.md`.
