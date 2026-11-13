# Proposta

## Por quê

Hoje não há como corrigir o nome, a cidade ou a UF depois do cadastro, nem contar algo sobre si para quem vai receber uma doação. O endpoint `PATCH auth/profile` existe no Xano, mas nenhuma tela o usa. O perfil público e o cartão de “Minhas doações” mostram só o primeiro nome e a localização. O Figma já tem a tela, no frame `Group 7` (`editar-perfil-1`).

## O que muda

- **Nova página `/perfil/editar`**, só com login. Sem login, leva a `/login`.
  - Chega-se a ela pelo botão “Editar perfil” no cartão da pessoa em `/minhas-doacoes`.
  - “Voltar a Minhas doações” fica na linha do logotipo, em `#007A42`.
  - **Campos:**
    - Nome, com a mesma validação do cadastro (dúvida 1);
    - Sobre, novo e opcional, com até 300 caracteres, o contador “N/300” e exibido como texto literal;
    - Cidade e Estado (UF), com a mesma validação do cadastro;
    - E-mail, só leitura, com “O e-mail é usado para entrar e não pode ser alterado.”.
  - **Prévia à esquerda**, como no Figma, mas sem e-mail e sem contadores: inicial, primeiro nome, “Cidade, UF” e Sobre. Ela acompanha o que a pessoa digita.
  - **Quadro “Quem vê estas informações”** (texto na dúvida 4).
  - **Ações:**
    - “Salvar alterações” grava e mostra “Alterações salvas.” (dúvida 6);
    - “Cancelar” volta a `/minhas-doacoes` sem salvar.
  - Mudar a cidade ou a UF **não altera** as doações já publicadas, que guardam a localização do momento da publicação.
- **Sobre em outros lugares:**
  - no perfil público, abaixo de “No DoaFácil desde …”;
  - no cartão da pessoa em `/minhas-doacoes`.

  Vazio, não mostra nada.
- **Xano:**
  - campo novo `about` na tabela `user` (texto, opcional, até 300 caracteres);
  - o `PATCH auth/profile` passa a aceitar e validar o `about`. O `GET auth/profile` passa a devolvê-lo;
  - o `GET catalog/donations/donor` (perfil público) e o `GET catalog/donations/mine` passam a devolver o `about`.
- **Apply em duas partes:** primeiro o Xano, com um teste real em script; depois o frontend.

### Do Figma, o que não entra

- A seção “Foto” (“Alterar foto”, “Remover foto”) e a foto na prévia. Ficam para uma change própria.
- O e-mail, os contadores, “Editar perfil”, “Compartilhar link do perfil” e o selo na prévia.

## Fora do escopo

- Foto de perfil.
- Trocar e-mail ou senha nesta tela.
- Atualizar a cidade e a UF das doações já publicadas.
- Moderação ou filtro automático do texto de Sobre.
- Mostrar o Sobre no detalhe da doação.

## Capacidades

### Novas capacidades

Nenhuma. A edição do perfil já é um requisito de `user-account`.

### Capacidades modificadas

- `user-account`:
  - “Consulta e atualização do perfil” passa a incluir o Sobre e as validações da edição;
  - entra a página `/perfil/editar`;
  - o cabeçalho da home passa a mostrar o primeiro nome novo depois de salvar.
- `donor-public-profile`: a resposta e a página do perfil público passam a incluir o Sobre.
- `donation-management`: a listagem passa a incluir o Sobre da própria pessoa. O cartão da pessoa em `/minhas-doacoes` passa a mostrar o Sobre e o botão “Editar perfil”, que até agora estavam proibidos.

## Impacto

- **Xano:**
  - `xano/table/user.xs`, com o campo `about`;
  - `profile_PATCH.xs` e `profile_GET.xs`;
  - `donations/donor_GET.xs` e `donations/mine_GET.xs`.
- **Frontend:**
  - um módulo novo, `doafacil/editar_perfil.py`, com o cliente, o estado e a página;
  - a rota nova em `doafacil/doafacil.py`;
  - o Sobre no `perfil_doador.py` e no `minhas_doacoes.py`;
  - o botão “Editar perfil” no cartão de “Minhas doações”;
  - a atualização do `account_name` no `LoginState` depois de salvar.
- **Quem já usa esses endpoints:**
  - o `GET auth/profile` é usado pelo cadastro de doação (`_fetch_profile`), que lê só a cidade e a UF e ignora os campos extras;
  - o `PATCH auth/profile` não é usado por nenhuma tela;
  - os dois scripts de teste real conferem as chaves exatas das respostas, por isso o `teste_perfil_real.py` (PP1) e o `teste_minhas_doacoes_real.py` (MD2) precisam aceitar o `about`.
- **Script:** `scripts/teste_editar_perfil_real.py`.
- **Testes:** `tests/test_edit_profile.py` e ajustes em `tests/test_donor_profile.py` e `tests/test_my_donations.py`.
- **Documentação:** `docs/design/README.md` e `docs/guia-do-colaborador.md`.
