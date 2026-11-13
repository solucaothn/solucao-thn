# Design

## Contexto

No `xano/`:

- **Tabela `user`:** tem `name` (o nome completo do cadastro), `email`, `password`, `city`, `state`, `role` e `password_reset`. Não há campo de Sobre.
- **`PATCH auth/profile`** (`profile_PATCH.xs`), com login:
  - aceita `name`, `city` e `state`, todos `trim|min:1`, e não valida a UF;
  - grava com `db.edit` e devolve `id`, `created_at`, `name`, `email`, `city` e `state`;
  - **nenhuma tela usa esse endpoint.**
- **`GET auth/profile`** (`profile_GET.xs`): devolve os mesmos campos. Só o cadastro de doação usa, pelo `_fetch_profile`, que lê a cidade e a UF e ignora o resto.
- **`auth/signup`:** valida no Xano só `trim|min:1` no nome, na cidade e na UF. As 27 siglas existem só no select da tela (`BRAZILIAN_STATES`, em `cadastro.py`).
- **`GET catalog/donations/donor`** (perfil público) e **`GET catalog/donations/mine`:** leem o `name` do usuário e devolvem só o primeiro nome.
- **`donation`:** guarda `city` e `state` copiados do perfil no momento da publicação, então mudar o perfil não muda as doações.
- **`GET catalog/donations/contact-email`:** devolve o e-mail de quem doa a pessoas logadas quando a doação tem a preferência “E-mail”. Isso pesa na dúvida 4.

No frontend:

- **Cabeçalho da home:** “Olá, <primeiro nome>” vem do `LoginState.account_name`, preenchido pelo `auth/me`. O estado guarda só o primeiro nome (spec `user-account`).
- **Validação do cadastro de conta:** `validate_signup_data`, em `login.py`, com as mensagens “Informe seu nome.”, “Informe sua cidade.” e “Selecione seu estado.”.
- **Dá para reaproveitar:**
  - o `back_link_header`;
  - o `avatar_initial`;
  - o `_edit_select` de `minhas_doacoes.py` (select branco com foco visível);
  - o `MyDonationsState.set_flash`;
  - o padrão de cliente e estado dos módulos `minhas_doacoes.py` e `perfil_doador.py`.
- **Scripts de teste real:** o `teste_perfil_real.py` (PP1) e o `teste_minhas_doacoes_real.py` (MD2) conferem as chaves **exatas** de `donor` e de `owner`. Os dois vão falhar quando o `about` entrar.

No Figma, o frame `Group 7` (`editar-perfil-1`) tem:

- “Voltar ao perfil” e o título “Editar perfil”, em verde e negrito;
- à esquerda, a prévia do perfil (248 px) com a legenda “Prévia — é assim que seu perfil aparece para quem recebe a doação”;
- à direita, o formulário em seções:
  - “Foto”;
  - “Dados públicos”, com Nome (mostrando o nome completo, “Ana Beatriz Lima”) e Sobre, com o placeholder “Conte um pouco sobre você” e “0/300 caracteres”;
  - “Localização”, com Cidade e Estado lado a lado;
  - “Conta”, com o e-mail em cinza e a ajuda;
- o quadro amarelo-claro “Quem vê estas informações”;
- “Cancelar” e “Salvar alterações”.

O Xano permite 10 requisições a cada 20 s.

## Objetivos / Fora do escopo

**Objetivos:**
- Abrir a edição com 1 requisição (`GET auth/profile`) e salvar com 1 (`PATCH`).
- Toda a validação vale também no Xano. A pessoa vem sempre do `$auth.id`.
- Um único componente de “Sobre” (texto simples, quebras preservadas) para a prévia, o perfil público e o cartão de “Minhas doações”.

**Fora do escopo:**
- A foto e qualquer upload.
- Mudar o e-mail ou a senha.
- Atualizar `city` e `state` das doações já publicadas.
- Filtro automático de conteúdo do Sobre.

## Decisões

### Parte A — Xano

1. **Tabela `user`:** campo novo `text about? filters=trim`, opcional. As contas existentes ficam com o `about` nulo, sem migração. O limite de 300 caracteres é validado no endpoint.
2. **`PATCH auth/profile`:**
   - **Entradas:**
     - `name` e `city`: `trim|min:1`, como hoje e como no cadastro;
     - `state`: um enum com as 27 siglas (dúvida 2);
     - `about`: `text? about? filters=trim|max:300`, opcional.
   - **Sobre sempre gravado:** com texto, grava o texto (sem os espaços das pontas, até 300 caracteres). Vazio, nulo ou omitido grava `""`, que apaga o Sobre. A tela sempre envia o formulário inteiro.
   - **Gravação:** com `db.edit`, com `about: $input.about ?? ""` no `data` e o `output` só com os campos do perfil.
   - Esta decisão foi revista depois do teste real 4.1: a primeira versão (omitido mantém, `""` apaga) não funcionava, porque o Xano trata `""` de uma entrada opcional como omitida.
   - **Resposta:** os campos de hoje mais o `about`. O e-mail continua na resposta, porque é da própria pessoa.
   - **Log de evento:** nenhum, como no `GET`.
3. **`GET auth/profile`:** a saída ganha o `about`.
4. **`GET catalog/donations/donor`:** o `db.get user` passa a ler o `about`, e a resposta passa a `donor: {first_name, city, state, member_since, about}`. A cidade e a UF continuam sendo as da doação de origem.
5. **`GET catalog/donations/mine`:** o `db.get user` passa a ler o `about`, e a resposta passa a `owner: {first_name, about}`.
6. **Teste real (`scripts/teste_editar_perfil_real.py`)**, no padrão dos anteriores e reaproveitando os auxiliares do `teste_chat_real.py`.
   - **Entrada:** login de uma conta e, opcionalmente, o ID de uma doação disponível dela, para o perfil público.
   - **Restauração:** os valores originais de nome, cidade, UF e Sobre são gravados de novo no fim, num `finally`.
   - **Cenários EP1 a EP12:**
     - EP1: `GET` sem token dá 401;
     - EP2: `GET` com o `about`;
     - EP3: `PATCH` válido devolve os campos;
     - EP4: o `GET` reflete a mudança e o e-mail não muda;
     - EP5: um Sobre com 300 “á” é aceito, e com 301 dá 400;
     - EP6: uma UF “XX” dá 400;
     - EP7: nome ou cidade vazios dão 400, sem alterar;
     - EP8: um Sobre omitido e um Sobre `""` apagam o texto;
     - EP9: um Sobre com `<b>` volta igual;
     - EP10: o `mine` traz o `owner.about` igual;
     - EP11: o `donor` traz o `about` igual, sem e-mail;
     - EP12: mudar a cidade não muda a cidade da doação no detalhe público.
   - **Os dois scripts antigos** passam a aceitar o `about` nas chaves de `donor` (PP1) e de `owner` (MD2).

### Parte B — Frontend

7. **Componente `about_text(value)`**, em `doafacil/cartoes_doacao.py` ou num módulo pequeno de perfil:
   - um `rx.text` com `white_space="pre-wrap"` e `overflow_wrap="anywhere"`, em `#2A2A2A`;
   - envolvido num `rx.cond(value != "", …)`, para não mostrar nada com o Sobre vazio;
   - usado na prévia, no perfil público e no cartão de “Minhas doações”.
8. **Módulo `doafacil/editar_perfil.py`:**
   - **Cliente:** `fetch_profile` e `update_profile`, com `XANO_AUTH_API_URL` e `/auth/profile`, e as exceções de 401, 400, 429 e serviço.
   - **Validação:** nome, e-mail, cidade e UF como texto; o `about` como texto ou nulo, que vira `""`. Campos extras são ignorados.
9. **`EditProfileState(LoginState)`:**
   - **Variáveis:** `view_state`, `load_error`, `name`, `email`, `city`, `uf`, `about`, `form_error` e `is_saving`. Usa `uf` em vez de `state` para não confundir com o estado do Reflex.
   - **Computadas:** `preview_first_name`, `preview_initial`, `preview_location` e `about_count` (“N/300”).
   - **`load_profile` (`on_load`):** sem token, leva a `/login`; senão, faz 1 requisição. Um 401 limpa a sessão e leva a `/login`.
   - **`save`:**
     - valida com as mesmas regras e mensagens do cadastro de conta (nome e cidade não vazios, UF entre as 27) e o Sobre com até 300 caracteres;
     - envia os quatro campos e atualiza o `account_name` com o primeiro nome novo;
     - depois, conforme a dúvida 5.
     - Um erro mantém os valores.
10. **Página `/perfil/editar`:**
    - **Cabeçalho:** `back_link_header("/minhas-doacoes", "Voltar a Minhas doações", "#007A42")`.
    - **Título:** `h1` “Editar perfil” em `#166B3B`, negrito, à esquerda, com `page-fade-enter`.
    - **Layout:** no computador, duas colunas, com a prévia (até 280 px) e a legenda à esquerda e o formulário à direita. No celular, uma coluna, com a prévia em cima.
    - **Prévia:** um cartão branco com borda `#D9D9D9`, o círculo `#F2F2F2` com a inicial `#555555`, o primeiro nome, “Cidade, UF” e o Sobre.
    - **Formulário:** um cartão branco com `auth-card-enter`.
      - **“Dados públicos”:** Nome (`input`), com a ajuda “Só o primeiro nome aparece para outras pessoas.” (dúvida 1), e Sobre (`text_area` com `max_length=300`, o placeholder “Conte um pouco sobre você” e o contador “N/300” com `aria-live="polite"`).
      - **“Localização”:** Cidade e Estado (`_edit_select` com as 27 siglas), lado a lado a partir de `md` e um abaixo do outro no celular.
      - **“Conta”:** E-mail num `input` `read_only` com fundo `#F2F2F2` e texto `#555555` (6,7:1), com `aria-describedby` apontando para “O e-mail é usado para entrar e não pode ser alterado.”.
    - **Quadro “Quem vê estas informações”:** fundo `#FFF3D6`, borda `#2A2A2A`, título `#166B3B` e texto `#2A2A2A`. O texto depende da dúvida 4.
    - **Ações:** “Cancelar”, um link com contorno para `/minhas-doacoes`, e “Salvar alterações” (`#007A42`).
    - **Ids próprios:** os campos usam `profile-*`, com o estilo no próprio componente. Não reaproveitam ids do cadastro, que carregam regras do `app.style`.
11. **Perfil público (`perfil_doador.py`):** o parser lê `donor.about`, o estado ganha `about`, e o cartão de identificação mostra o `about_text` abaixo de “No DoaFácil desde …”.
12. **Minhas doações (`minhas_doacoes.py`):**
    - o parser lê `owner.about`, e o estado ganha `about`;
    - o cartão da pessoa mostra o `about_text` e, abaixo, o botão “Editar perfil”, um link com contorno `#007A42` e 44 px para `/perfil/editar`.
13. **Rota:** `/perfil/editar` com `on_load=EditProfileState.load_profile`, sem o botão flutuante do chat.

## Riscos / Trade-offs

- **[O Sobre é público e livre]** → É mostrado sempre como texto simples, sem HTML. A dúvida 3 propõe uma dica contra dados de contato. Não há moderação nesta change.
- **[Os scripts de teste antigos conferem as chaves exatas]** → Eles são ajustados nesta change (decisão 6), antes do teste real.
- **[O nome muda, mas o token e o cabeçalho ficam com o nome antigo]** → O `save` atualiza o `account_name` na hora. As outras abas recebem o nome novo no próximo `auth/me`.
- **[Mudar a cidade não muda as doações]** → É o comportamento desejado (decisão 5 do pedido). O quadro informativo e a ajuda deixam isso claro (dúvida 4).
- **[Limite de 10 requisições a cada 20 s]** → São 1 requisição para abrir e 1 para salvar.

## Dúvidas para o Higor

1. **Nome completo ou primeiro nome:** o cadastro guarda o **nome completo** em `user.name`, e o Figma mostra “Ana Beatriz Lima” no campo. Só o primeiro nome aparece para outras pessoas.
   - **Recomendo** que o campo “Nome” edite o nome completo, com a ajuda “Só o primeiro nome aparece para outras pessoas.” A validação é a do cadastro: não vazio.
   - **A outra opção** é um campo “Primeiro nome”, que troca só a primeira palavra. Isso é mais confuso e mexe no sobrenome guardado.
2. **UF no backend:** o `auth/signup` não valida a UF no Xano, só o select da tela. Recomendo que o `PATCH auth/profile` aceite só as 27 siglas (enum), recusando com 400. É mais rígido que o cadastro, mas protege o dado que aparece no perfil.
3. **Sobre:** recomendo:
   - **manter as quebras de linha,** que contam nos 300 caracteres;
   - **mostrar abaixo do campo a dica** “Não coloque telefone, endereço ou e-mail: este texto é público.”

   Confirma as duas?
4. **Texto do quadro:** o texto pedido diz que o e-mail “nunca aparece para outras pessoas”. Mas, numa doação com a preferência “E-mail”, ele é mostrado a pessoas logadas que pedem contato (endpoint `contact-email` e aviso do cadastro de doação). O texto também diz que cidade e estado aparecem “junto das suas doações”, e elas mostram a cidade do momento da publicação. Proponho:

   > “Seu primeiro nome, cidade, estado e o texto de Sobre aparecem no seu perfil público. Suas doações mostram o primeiro nome e a cidade e o estado do momento em que foram publicadas. Seu e-mail é usado para entrar e só é mostrado a pessoas logadas que pedirem contato numa doação sua com a preferência “E-mail”.”

   Usamos esse texto ou outro?
5. **Depois de salvar:** recomendo voltar a `/minhas-doacoes`, com o aviso “Alterações salvas.” no topo, como já acontece na edição da doação. A outra opção é ficar em `/perfil/editar`, com o aviso acima dos botões.

### Respostas do Higor

1. O campo Nome edita o nome completo, com a ajuda “Só o primeiro nome aparece para outras pessoas.”
2. O `PATCH auth/profile` aceita só as 27 siglas e recusa o resto com 400.
3. O Sobre mantém as quebras de linha e mostra a dica “Não coloque telefone, endereço ou e-mail: este texto é público.”
4. O quadro usa o texto proposto na dúvida 4. O texto original estava errado sobre o e-mail. O cenário da spec foi atualizado com o texto exato.
5. Depois de salvar, a página volta a `/minhas-doacoes` com “Alterações salvas.”, pelo `MyDonationsState.set_flash`.

## Consulta ao Xano Developer MCP (tarefa 2.1)

- **Campo novo na tabela:** `text? about? filters=trim`, nulo e opcional, como o `city` e o `state` da tabela `donation`. As contas existentes ficam com o valor nulo.
- **Entrada do `PATCH`:** `text? about? filters=trim|max:300`.
  - Na doc, um campo nulo e opcional aceita `""` e `null` e pode ser omitido.
  - **Correção depois do teste real 4.1:** o Xano trata `""` de uma entrada opcional como omitida (vira nulo no `stack`). Por isso, a regra final é: vazio, nulo ou omitido gravam `""`.
  - O `max:300` conta caracteres, como o MD11 da change minhas-doacoes mostrou com o `max:100`.
- **Enum:** a lista com as 27 siglas, uma por linha, em `values`.
- **Primeira versão (substituída):** `var` com `|set:"about":...` num `conditional` e `db.patch`. O `db.patch` não aceita `output` e devolveria a conta inteira, com a senha, e por isso era seguido de um `db.get`.
- **Versão final:** sem o `conditional`, o `PATCH` volta ao `db.edit` com `output`, como era antes da change. Isso tira a consulta extra e não devolve a senha. O `??` já é usado no `detail_GET.xs` (`$owner.name ?? ""`), e o arquivo passa no validador do MCP.
