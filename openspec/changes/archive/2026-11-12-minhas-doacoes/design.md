# Design

## Contexto

O que existe hoje no `xano/`:

- **`PATCH catalog/donations/status`** (`status_PATCH.xs`), com login:
  - aceita `disponível`, `reservada` e `concluída`;
  - recusa com 400 a saída de `concluída` e **a volta de `reservada` para `disponível`**;
  - responde 404 para doação inexistente e 403 para doação de outra pessoa.
- **`PATCH catalog/donations`** (`donations_PATCH.xs`), com login:
  - aceita só `category_id`, `title` e `description`, esta opcional;
  - não confere o status e responde 403 para doação de outra pessoa.
- **`DELETE catalog/donations`** (`donations_DELETE.xs`), com login: numa transação, apaga as mensagens, as conversas e a doação. **Não apaga as linhas de `donation_photo`**, uma pendência já registrada no guia do colaborador (seção 7).
- **`POST catalog/donations/publish`:** valida a categoria e as enumerações. O wizard é mais restrito: só “A combinar”, “E-mail” ou “Chat do DoaFácil”, título até 100 caracteres, descrição obrigatória até 2000 e categorias sem “Alimentos” e “Móveis”.
- **Nenhum endpoint lista as doações de uma pessoa com o status.** O `GET catalog/donations` é público e não filtra pela pessoa.
- **O frontend não usa** nenhum dos três endpoints acima, então mudar o contrato deles não quebra nenhuma tela.

No frontend:

- o cabeçalho logado da home mostra “Olá, <primeiro nome>”, “Sair” e “Quero Doar”;
- a sessão fica só no estado do Reflex (`LoginState.auth_token`), e o estado guarda só o primeiro nome (spec `user-account`);
- dá para reaproveitar:
  - o `back_link_header`;
  - o `avatar_initial`, de `chat.py`;
  - o `_positive_donation_id`, de `detalhe_doacao.py`;
  - o `_fetch_categories` e as constantes `CONDITIONS`, `DELIVERY_METHODS` e `CONTACT_PREFERENCES`, de `cadastro_doacao.py`;
  - a imagem genérica, de `cartoes_doacao.py`.

No Figma, o frame `Group 6` (`meu-perfil-1`, 1512 × 982) tem:

- “Voltar ao inicio”, solto, sem a linha do logotipo;
- o título centralizado;
- à esquerda, o cartão de perfil, de 248 px;
- à direita, uma grade de 3 × 2 cartões de 245 px, com NOVO e “Estado: …”;
- “Página 1 de 3” com um ícone de grade.

Não há selo de status nem menu de ações.

O Xano permite 10 requisições a cada 20 s.

## Objetivos / Fora do escopo

**Objetivos:**
- Uma requisição por carregamento ou troca de página da lista, com os contadores na mesma resposta.
- Reaproveitar os endpoints de status, edição e exclusão, só com os ajustes necessários.
- Toda a autorização no Xano: a pessoa vem sempre do `$auth.id`.

**Fora do escopo:**
- Guardar a página da lista na URL; recarregar volta à página 1.
- Apagar os arquivos de imagem do armazenamento do Xano: só as linhas de `donation_photo` (dúvida 5).
- Edição concorrente: vale a última gravação.

## Decisões

### Parte A — Xano

1. **`GET catalog/donations/mine`** (`xano/api/catalog/catalog/donations/mine_GET.xs`), com `auth = "user"`.
   - **Entrada:** `int page?=1`. Uma página menor que 1 vira 1, como no perfil público.
   - **Primeiro nome:** `db.get user` pelo `$auth.id`, com a mesma expressão do detalhe.
   - **Contadores:** três `db.query ... return = {type: "count"}`, todos com `owner_id == $auth.id`:
     - `active`, com `status` disponível ou reservada;
     - `completed`, com `status` concluída;
     - `total`, com todas as doações da pessoa.

     Uma doação com `status` nulo, que não deveria existir, entra no total, mas em nenhum contador.
   - **Lista:** `db.query donation` com `owner_id == $auth.id`, `sort created_at desc` e `paging: {page, per_page: 6, metadata: false}`. A saída é `id`, `created_at`, `title`, `photo`, `condition` e `status`, com a foto montada como no `recent_GET.xs`.
   - **Resposta:** `{owner: {first_name}, counts: {active, completed}, items, page, per_page, total, page_total}`. `page_total` é calculado como no `donor_GET.xs`. Não há e-mail, `owner_id`, id de usuário nem log de evento, porque é uma leitura.
   - **Alternativa descartada:** paginação nativa com metadados. Os nomes do total não foram confirmados no MCP na change perfil-publico, e o `count` já foi validado lá.
2. **`GET catalog/donations/mine/item`** (`.../donations/mine/item_GET.xs`), com `auth = "user"` (dúvida 4).
   - **Entrada:** `donation_id`.
   - **Busca:** `db.get donation`, com uma precondição só (`!= null && owner_id == $auth.id`) e o 404 genérico “Doação não encontrada.”.
   - **Resposta:** `id`, `title`, `description`, `category_id`, `condition`, `delivery_method`, `contact_preference` e `status`.
3. **`PATCH catalog/donations`**: o contrato muda (dúvida 6).
   - **Entradas obrigatórias:**
     - `title` (trim, de 1 a 100 caracteres) e `description` (trim, de 1 a 2000);
     - `category_id`;
     - `condition` (enum Ótimo, Bom, Regular), `delivery_method` (enum só com “A combinar”) e `contact_preference` (enum “E-mail” e “Chat do DoaFácil”).
   - **Precondições:**
     - dona e existente, numa precondição só, com o 404 genérico, no lugar do 403;
     - status diferente de `concluída`, com `inputerror`;
     - categoria existente.
   - **Gravação:** os seis campos e `updated_at`. A resposta não traz `owner_id`.
   - A sintaxe do limite de tamanho (`max:`) e do enum de valor único será confirmada no Xano Developer MCP antes de escrever.
4. **`PATCH catalog/donations/status`:** se a dúvida 1 for aprovada, sai o bloco que recusa a volta de `reservada` para `disponível`. O resto continua igual, inclusive o 403 para doação de outra pessoa. O frontend trata 403 e 404 com a mesma mensagem.
5. **`DELETE catalog/donations`** (dúvida 5): dentro da transação, antes do `db.del donation`, entra um `db.bulk.delete donation_photo` com `donation_id == $input.donation_id`.
6. **Teste real (`scripts/teste_minhas_doacoes_real.py`)**, no padrão do `teste_chat_real.py`, reaproveitando o login e os auxiliares dele.
   - **Contas:** a dona e outra pessoa, com a senha pedida por `getpass`.
   - **IDs pedidos no terminal:** uma doação disponível da dona, opcionalmente uma concluída dela e uma doação de teste que possa ser apagada.
   - **Pausas:** 2,5 s entre as requisições.
   - **O que imprime:** só o status HTTP, chaves, tipos e sim/não, nunca nomes, e-mails, URLs ou corpos de resposta.
   - **O que altera:** a edição é desfeita no fim, gravando de novo os valores originais. A doação volta ao status original quando isso é permitido. A exclusão só roda com confirmação.
   - **Cenários:**
     - MD1 a MD6, da lista: 401 sem token; só as chaves permitidas; nenhuma chave proibida; até 6 itens; totais e contadores coerentes; página 0 e página além da última.
     - MD7 a MD9, da leitura: a própria doação dá 200; a de outra pessoa e uma inexistente dão o mesmo 404; sem token dá 401.
     - MD10 a MD14, da edição: válida e depois desfeita; valores inválidos (título vazio, título com 101 caracteres, “WhatsApp”, “Entrega”) dão 400; doação de outra pessoa dá 404; concluída dá 400, se informada.
     - MD15 a MD17, do status: disponível → reservada → disponível; a outra pessoa é recusada; concluída → disponível dá 400, se informada.
     - MD18 e MD19, da exclusão: a outra pessoa é recusada; a própria dona apaga com confirmação, e depois a leitura dá 404.

### Parte B — Frontend

7. **Módulo `doafacil/minhas_doacoes.py`:**
   - **Cliente:** `fetch_my_donations`, `fetch_my_donation`, `change_status`, `update_donation` e `delete_donation`, todos com `Authorization: Bearer`.
   - **Exceções:** sessão inválida (401), não encontrada (404 e 403), recusada (400), limite (429) e serviço.
   - **Validação da lista:** status entre os três valores; contadores, página e totais inteiros não negativos; primeiro nome não vazio. Campos extras são ignorados.
8. **`MyDonationsState(LoginState)`:**
   - **`load_page` (`on_load`):** sem `auth_token`, faz `rx.redirect("/login")` sem requisição; com token, busca a página 1. Um 401 em qualquer requisição limpa a sessão e leva a `/login`, como no chat.
   - **`go_to_page(n)`:** igual ao do perfil público. Ignora cliques fora do intervalo ou durante o carregamento. Com erro, mantém a página anterior.
   - **Ações:**
     - `request_action(kind, id, title)` abre a confirmação, e reservar ou voltar a disponível não pedem confirmação;
     - `confirm_action` faz a requisição e recarrega a página atual. Se a página ficou além da última depois de uma exclusão, recarrega a última. São 2 requisições por ação.
     - `cancel_action` só fecha.
     - `action_busy` bloqueia outra ação, e `notice` e `notice_is_error` mostram o resultado num `role="status"`.
9. **Cartão da doação (`my_donation_card`):** segue a aparência do cartão da home (foto com degradê, título e “Condição: …” em branco), mas é outro componente, porque tem selo e menu.
   - **Selo de status** no canto superior esquerdo, no lugar do NOVO (dúvida 3), com fundo opaco, para o contraste não depender da foto:
     - “Disponível”: `#E3F5EA` com texto `#166B3B`;
     - “Reservada”: `#FFF1D6` com texto `#7A4B00`;
     - “Concluída”: `#ECECEC` com texto `#3D3D3D`.

     O contraste é conferido no apply.
   - **Menu:** `rx.dropdown_menu` com um botão de 44 px (ícone `ellipsis-vertical`) no canto superior direito, rotulado “Ações da doação <título>”. Os itens dependem do status (spec “Ações por status”).
   - **“Ver anúncio”** (`/doacao/<id>`) só nas doações disponíveis, porque o detalhe público dá 404 para as outras (dúvida 3).
10. **Confirmação:** um `rx.alert_dialog` só, no nível da página, com o título da doação e o aviso de cada ação. Ele prende o foco, fecha com Esc e devolve o foco.
11. **Página `/minhas-doacoes`:**
    - **Cabeçalho:** `back_link_header("/", "Voltar ao início", "#007A42")`.
    - **Título:** `h1` “Minhas doações” em `#166B3B`, negrito, à esquerda, com `page-fade-enter`.
    - **Layout:** no computador (`md`), duas colunas, com o cartão da pessoa (até 280 px) à esquerda e a grade à direita. No celular, uma coluna.
    - **Grade:** 3 colunas no `lg`, 2 no `sm` e 1 no celular. Com 6 por página, isso dá o 3 × 2 do Figma.
    - **Cartão da pessoa:** branco, borda `#D9D9D9` e cantos de 8 px. Tem o círculo `#F2F2F2` com a inicial em `#555555`, o primeiro nome e dois números em `#166B3B` com os rótulos “Doações” e “Doações realizadas” em `#555555`.
    - **Paginação:** como a do perfil público, sem o ícone de grade do Figma.
    - **Estado vazio:** um cartão branco com “Você ainda não tem doações” e o botão “Quero Doar” (`#007A42`), que leva a `/cadastro-doacao`.
12. **Link no cabeçalho da home:** `rx.link("Minhas doações", href="/minhas-doacoes")` antes de “Olá, …”, em `#168447`, o verde dos textos do cabeçalho.
    - No celular, aparece só o ícone `package`, com o rótulo acessível “Minhas doações” e 44 px de área de toque, para não quebrar o cabeçalho a 360 px.
    - O teste atual que confere “só Olá e Sair” é atualizado.
13. **Página `/minhas-doacoes/<id>/editar` (`EditDonationState(LoginState)`):**
    - **`load_edit` (`on_load`):**
      - sem token, leva a `/login`;
      - com id inválido, mostra “Doação não encontrada” sem requisição;
      - senão, busca as categorias (`_fetch_categories`) e a doação. São 2 requisições.
      - Uma doação concluída mostra “Esta doação foi concluída e não pode mais ser editada.” sem formulário.
    - **Formulário:**
      - título com limite de 100 caracteres e descrição com limite de 2000;
      - os selects de categoria, condição, entrega e contato, com as opções do cadastro;
      - as mesmas mensagens e regras do `_validate_step`, sem a regra de cidade e UF;
      - um valor atual fora das opções deixa o campo vazio.
    - **Cores:**
      - os campos de texto reaproveitam os ids do cadastro (`donation-title` e `donation-description`), e as regras de cor do placeholder e do texto digitado que já estão no `app.style` valem aqui também. As duas páginas nunca aparecem juntas, então os ids não se repetem numa página.
      - os selects têm ids próprios (`edit-donation-*`) e um componente próprio (`_edit_select`), com o estilo no `Select.Trigger`: fundo branco, borda `#C8C8C8`, 40 px de altura, cantos de 8 px, texto `#1F1F1F`, placeholder `#333333` e foco visível em `#007A42`.
      - o `_select_field` do cadastro põe o estilo no `Select.Root`, que não desenha nada, e o botão ficava com o fundo cinza padrão, parecendo desativado (roteiro 9.2). O cadastro não foi alterado nesta change.
    - **Salvar:** uma requisição. No sucesso, grava o aviso e redireciona para `/minhas-doacoes`, que mostra o aviso uma vez. Um erro mantém os valores.
    - **Cabeçalho:** `back_link_header("/minhas-doacoes", "Voltar a Minhas doações", "#007A42")`.
    - **Animação:** o cartão do formulário usa `auth-card-enter`.
14. **Rotas:** `/minhas-doacoes` e `/minhas-doacoes/[id]/editar`, com os `on_load` acima. Nenhuma das duas tem o botão flutuante do chat.

## Riscos / Trade-offs

- **[O contrato do `PATCH catalog/donations` muda]** Os campos novos passam a ser obrigatórios, e o 403 vira 404. → Nenhuma tela usa o endpoint hoje. O teste real cobre o contrato novo.
- **[Voltar a disponível reexpõe a doação]** Ela volta para a home, o detalhe e o perfil, e as conversas continuam abertas. → É o comportamento esperado quando uma reserva não se concretiza. Depende da dúvida 1.
- **[Arquivos de imagem ficam no armazenamento depois da exclusão]** → Só as linhas de `donation_photo` são apagadas. A limpeza do armazenamento fica para outra change.
- **[Limite de 10 requisições a cada 20 s]** → São 1 requisição por página, 2 por ação (a ação e a recarga) e 2 para abrir a edição. Não há consulta automática. O 429 vira uma mensagem simples.
- **[Cabeçalho da home apertado no celular]** → No celular, o link vira só um ícone com rótulo acessível. Isso é conferido a 360 px no roteiro manual.
- **[Selo sobre foto]** → O selo tem fundo opaco e cor de texto escura, então o contraste não depende da foto.

## Dúvidas para o Higor

1. **Voltar a disponível:** o `status_PATCH.xs` hoje recusa a volta de reservada para disponível.
   - **Recomendo liberar essa transição,** porque uma reserva que não se concretiza é comum. Isso muda o endpoint (decisão 4), e a spec já está escrita assim.
   - **Se não for liberada,** a ação sai do menu e da spec, e o `status_PATCH.xs` fica como está.
2. **Edição por status:** recomendo permitir a edição de doações disponíveis e reservadas, e recusar as concluídas no backend, que ficam como histórico. A spec já está assim. Outra opção: só as disponíveis.
3. **Cartões:** recomendo:
   - **sem o NOVO,** que não faz sentido nas próprias doações, com o selo de status no lugar dele;
   - **“Ver anúncio” só nas doações disponíveis,** porque o detalhe público dá 404 para as reservadas e as concluídas;
   - **sem a “Condição: …”,** porque o pedido lista foto, título, selo e menu.

   Confirma?
4. **Segundo endpoint novo:** a página de edição precisa ler a doação mesmo reservada, e o detalhe público só mostra as disponíveis. Recomendo o `GET catalog/donations/mine/item` (decisão 2), só para a dona e com o 404 genérico. Outra opção seria a listagem trazer todos os campos, mas a edição não funcionaria ao recarregar a página nem por link direto.
5. **Fotos órfãs:** o `DELETE` não apaga as linhas de `donation_photo`, pendência registrada no guia. Como esta change coloca o botão “Apagar” na tela, recomendo corrigir aqui (decisão 5). Os arquivos no armazenamento ficam para outra change. Se a resposta for não, sai da spec a parte “e os registros das fotos adicionais”.
6. **Contrato do `PATCH`:** recomendo:
   - trocar o 403 por 404 genérico para doação de outra pessoa;
   - deixar a descrição e os três campos novos obrigatórios;
   - restringir a entrega e o contato às opções do cadastro.

   Nenhuma tela usa o endpoint hoje. Confirma?

### Respostas do Higor

1. Liberar a volta de reservada para disponível (decisão 4).
2. Editar só doações disponíveis e reservadas; as concluídas são recusadas pelo backend.
3. Sem o NOVO, com o selo de status no lugar dele, e “Ver anúncio” só nas disponíveis. **A linha “Condição: …” fica no cartão.** Por isso, a listagem também devolve `condition` (decisão 1), e a spec foi ajustada.
4. Criar o `GET catalog/donations/mine/item`.
5. O `DELETE` apaga as linhas de `donation_photo` nesta change.
6. O `PATCH` fica como recomendado: 404 genérico, descrição e campos novos obrigatórios, entrega e contato restritos às opções do cadastro.

## Consulta ao Xano Developer MCP (tarefa 2.1)

- **Tamanho do texto:** `filters=trim|min:1|max:100` (e `max:2000` na descrição). Na doc, `min` e `max` são o tamanho mínimo e máximo do texto. O `trim` vem antes, então só espaços também é recusado.
- **Texto obrigatório:** um `text` obrigatório recusa `""` e `null` na validação da plataforma, antes do `stack`, com 400.
- **Enum:** `enum <nome> { values = [...] }`. Com um valor só, a lista tem um elemento: `values = ["A combinar"]`.
- **“Ou” no `where`:** com `||` entre parênteses, como no `donations_GET.xs`.
- **Exclusão em lote:** `db.bulk.delete <tabela> { where = ... }`, que já é usada no `donations_DELETE.xs`.
- **A conferir no teste real:** se o `max:100` conta caracteres ou bytes. O MD11 envia um título com 100 “á”, que precisa ser aceito.
