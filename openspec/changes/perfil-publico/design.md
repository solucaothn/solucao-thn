# Design

## Contexto

- **Detalhe no Xano:** o `catalog/donations/detail` (`detail_GET.xs`) busca a doação, responde com o 404 genérico “Doação não encontrada.” quando ela não existe ou não está disponível, e reduz o nome do dono ao primeiro nome. Ele nunca devolve `owner_id`.
- **Doações recentes:** o `catalog/donations/recent` monta os cartões da home com `id`, `created_at`, `title`, `photo` (URL com `PUBLIC_BASE_URL`) e `condition`.
- **Tabela `user`:** tem `name`, `email`, `city`, `state` e `created_at`, este em epoch ms.
- **Frontend:**
  - a home tem o `_parse_donations`, a regra do NOVO (até 7 dias) e o `donation_card`;
  - o detalhe lê o id da rota com `self.router.page.params["id"]` e usa o `back_home_header()` de `chat.py`, com “Voltar ao início” fixo para `/`.
- **Figma:**
  - `perfil-doador-01` (dentro de `Group 8`, 580:2309) mostra 6 cartões em 5 colunas de 245 px;
  - `perfil-doador-02` (562:2381) mostra o estado vazio;
  - nenhum dos dois tem a linha do logotipo; o “Voltar à doação” fica num verde claro, sem contraste AA.
- **Limite:** o Xano permite 10 requisições a cada 20 s.

## Objetivos / Fora do escopo

**Objetivos:**
- Um endpoint só, que traz a identificação e uma página da lista numa requisição.
- Reaproveitar a regra do 404 do detalhe, o cálculo do primeiro nome e o cartão da home.

**Fora do escopo:**
- Guardar a página da lista na URL. A página fica só no estado; recarregar volta à página 1.
- Cache no frontend.

## Decisões

### Parte A — Xano

1. **Endpoint `catalog/donations/donor`**, GET, no grupo Catalog, sem `auth`, arquivo `xano/api/catalog/catalog/donations/donor_GET.xs`.
   - **Entradas:** `int donation_id` e `int page?=1`.
   - Busca a doação com `db.get` e saída mínima: `id`, `owner_id`, `city`, `state`, `status`.
   - Aplica as mesmas duas `precondition` do detalhe (nula e não disponível), com `error_type = "notfound"` e a mensagem “Doação não encontrada.”.
   - Busca o dono com `db.get user` e saída só de `name` e `created_at`. Se o dono não existir, também responde 404.
   - **Alternativa descartada:** um endpoint por usuário. Ele obrigaria o frontend a conhecer o id de quem doa, o que a spec do detalhe proíbe.
2. **Identificação:**
   - `first_name` usa a mesma expressão do detalhe: `name`, `trim`, divisão por espaço, primeira parte.
   - `city` e `state` vêm **da doação de origem** (dúvida 1). É o mesmo dado que o detalhe já mostra no cartão “Quem doa”, então nada novo fica público.
   - `member_since` é o `created_at` do usuário formatado como `"AAAA-MM"` no fuso `America/Sao_Paulo`, com o filtro de formatação de data do XanoScript. O nome exato do filtro será confirmado no Xano Developer MCP antes de escrever. Dia e horário não saem da função.
3. **Lista:**
   - `db.query donation` com `owner_id == $donation.owner_id` e `status == "disponível"`, ordenada por `created_at` decrescente;
   - paginação nativa com `per_page: 12` e metadados (os nomes, como `itemsTotal` e `pageTotal`, serão confirmados no MCP);
   - saída `id`, `created_at`, `title`, `photo` e `condition`, com a foto montada como no `recent_GET.xs`;
   - a doação de origem entra na lista (dúvida 2);
   - a página é normalizada: menor que 1 vira 1. Além da última, a lista vem vazia com o total correto.
4. **Resposta:**
   ```
   {
     donor: {first_name, city, state, member_since},
     items: [{id, created_at, title, photo, condition}],
     page, per_page, total, page_total
   }
   ```
   Não há `owner_id`, id de usuário, e-mail nem nome completo. Não há log de evento, como no detalhe, que também é leitura pública.
5. **Teste real (`scripts/teste_perfil_real.py`)**, no padrão do `teste_chat_real.py`:
   - não precisa de login; lê `XANO_API_URL` do ambiente;
   - pede os ids no terminal;
   - imprime só os códigos de status e a estrutura (chaves e tipos), nunca nomes, e-mails ou URLs;
   - espera 2,5 s entre as requisições.
   - **Cenários:**
     - PP1: 200 com só as chaves permitidas;
     - PP2: os tipos dos campos;
     - PP3: `member_since` no formato `AAAA-MM`;
     - PP4: as chaves proibidas ausentes em todos os níveis;
     - PP5: no máximo 12 itens, total e páginas coerentes;
     - PP6: a página 0 vira a página 1;
     - PP7: uma página além da última vem vazia com o total;
     - PP8: 404 para um id inexistente;
     - PP9: 404 genérico para uma doação indisponível, se o Higor informar uma;
     - PP10: os itens são todos de doações disponíveis, conferidos pelo detalhe de cada um, com a pausa entre as consultas.

### Parte B — Frontend

6. **Módulo `doafacil/perfil_doador.py`**, no padrão do `detalhe_doacao.py`:
   - **Cliente:** `fetch_donor_profile(client, base_url, donation_id, page)` com as exceções de não encontrado, de limite (429) e de serviço.
   - **Validação:** a identificação é validada (primeiro nome não vazio; cidade e UF texto; `member_since` no formato `AAAA-MM`). Os itens passam pelo `_parse_donations` da home, que já valida, aplica a foto genérica, o rótulo “Condição: …” e o NOVO. Campos extras da resposta são ignorados, então nada além do permitido chega ao estado.
   - **Estado `DonorProfileState(rx.State)`:**
     - `view_state` (`loading`, `ready`, `not_found` ou `error`);
     - `donation_id`;
     - `first_name`, `initial`, `location` (“Cidade, UF”) e `member_since_label` (“outubro de 2020”, com uma tabela de meses em português);
     - `items`, `total`, `page`, `page_total`, `page_loading` e `page_error`.
   - **Eventos:**
     - `load_profile` (`on_load`) valida o id como no detalhe e busca a página 1;
     - `go_to_page(n)` ignora cliques durante o carregamento e fora do intervalo.
     - Numa troca de página com erro, os itens anteriores ficam e aparece a mensagem `page_error`.
7. **Cabeçalho:** o `back_home_header()` vira um caso de `back_link_header(href, label, color)` em `chat.py`, com os mesmos estilos (44 px, só a seta no celular, rótulo acessível).
   - O chat e o detalhe continuam iguais.
   - O perfil usa “Voltar à doação”, `#007A42` e `href = /doacao/<id>`. Com id inválido, o link vai para `/`.
8. **Página** (frames do Figma, sem a foto, o selo e a faixa do topo):
   - **Fundo:** creme `#FFF6E8`, com conteúdo de até 1396 px e espaçamento lateral de 16 px no celular.
   - **Cartão de identificação:** branco, borda `#D9D9D9`, cantos de 8 px.
     - Círculo `#F2F2F2` com a inicial em `#555555`, de 120 px no computador e 72 px no celular.
     - Primeiro nome num `h1` em `#166B3B`.
     - “Cidade, UF” em `#2A2A2A`; “No DoaFácil desde …” em `#555555`.
     - No celular, o círculo fica acima do texto.
   - **Doações:**
     - `h2` “Doações disponíveis” em `#166B3B` e o contador “1 item” ou “N itens” em `#555555`;
     - grade com `repeat(auto-fill, minmax(220px, 1fr))`: 5 colunas a 1512 px e 1 a 360 px;
     - o `donation_card` da home, que já leva a `/doacao/<id>`.
   - **Paginação** (só com `page_total > 1`): os botões “Anterior” e “Próxima” e o texto “Página N de M” com `aria-live="polite"`.
   - **Estado vazio:** cartão branco centralizado com “Nenhuma doação disponível no momento” (`#166B3B`, negrito), a frase “Quando <nome> publicar uma nova doação, ela aparece aqui.” e o link “Explorar outras doações” (`#007A42`) para `/`.
   - **Animação:** `page-fade-enter` só nos títulos fixos, como no detalhe; os dados do Xano não animam.
9. **Detalhe:** o cartão “Quem doa” é envolvido por um `rx.link` para `/doacao/<id>/quem-doa`.
   - Rótulo acessível “Ver perfil de <primeiro nome>”.
   - Ganha uma linha “Ver perfil” com `chevron-right` em `#007A42`, para mostrar que é clicável.
   - No hover, a borda fica `#007A42`; o foco tem contorno visível.
10. **Rota:** `app.add_page(donor_profile_page, route="/doacao/[id]/quem-doa", on_load=DonorProfileState.load_profile)`.

## Riscos / Trade-offs

- **[A doação de origem pode deixar de estar disponível com o perfil aberto]** → A próxima troca de página recebe 404. A página então mostra “Doação não encontrada”, como faria ao recarregar.
- **[O nome dos metadados de paginação e do filtro de data no XanoScript]** → Validar no Xano Developer MCP antes de escrever, e conferir no teste real (PP3 e PP5).
- **[Limite de 10 requisições a cada 20 s]** → Uma requisição por página e nenhuma consulta automática. O 429 vira uma mensagem simples.
- **[“Membro desde” expõe mês e ano do cadastro]** → É uma decisão do Higor. O dia e o horário não saem do Xano.

## Dúvidas para o Higor

1. **Cidade e UF do perfil:** da doação de origem (recomendado, porque é o que o detalhe já mostra e não expõe nada novo) ou do cadastro da conta (`user.city` e `user.state`, que hoje não são públicos)?
2. **A doação de origem entra na lista?** Recomendo que sim: a lista são as doações disponíveis da pessoa e o contador conta todas. Nesse caso, porém, o estado vazio quase nunca aparece, porque o perfil só abre a partir de uma doação disponível. Ele ficaria só como defesa. Se a doação de origem sair da lista, o título passaria a “Outras doações disponíveis” e o estado vazio vira o caso comum de quem tem uma doação só.
3. **NOVO:** a mesma regra da home, até 7 dias. Confirma?
