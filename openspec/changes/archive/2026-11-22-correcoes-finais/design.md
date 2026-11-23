# Design

## Contexto

O motivo está em proposal.md (por quê). Restrições que moldam a solução:

- **O plano grátis do Xano** aceita 10 pedidos a cada 20 s para o site inteiro (spec `backend-request-budget`).
- **As categorias** passam todas por `_parse_categories` (`cadastro_doacao.py`) e pelo cache de 1 h. A gaveta, `/categorias`, a busca da home, a Explorar, o cadastro e a edição usam essa mesma lista.
- **O ícone de cada categoria** vem de `CATEGORY_ICONS` (`explorar.py`). O `rx.icon` precisa de nome fixo, por isso `categorias.py` monta um `rx.match` com os ícones conhecidos. `sofa` está na lista de ícones Lucide do Reflex.
- **No chat**, o `rx.moment` das mensagens só existe com conversa aberta. O da lista fica sempre montado em `/chat`, e cada tique confere a visibilidade da aba antes de consultar. Em tela estreita, `back_to_list` só troca `mobile_view` para `"list"` e a conversa continua ativa. Reabrir uma conversa (`select_conversation`) sempre recarrega as mensagens.
- **O endpoint `publish`** foi criado por outro integrante e pode ter outros consumidores (guia, seção 8). O push é do Higor, só com `-i` do arquivo, dry-run revisado e OK do grupo.

## Objetivos / Fora do escopo

**Objetivos:**
- cumprir as deltas desta change com mudanças pequenas, reaproveitando o que já existe (cache público, `login_url`, o estilo dos botões “Tentar de novo” atuais);
- não fazer nenhum pedido a mais ao Xano por causa das mudanças. As novas tentativas só acontecem por ação da pessoa.

**Fora do escopo:**
- refatorar os botões “Tentar de novo” que já existem (Explorar, Categorias, detalhe e chat);
- mudar a obrigatoriedade da descrição no `publish`: ela continua opcional ali, para não quebrar outros consumidores. Só ganha o limite de 2000;
- limite de tentativas no login;
- apagar as sobras do modelo do Xano.

## Decisões

1. **Categorias sem exclusão por nome.** `EXCLUDED_CATEGORY_NAMES` sai, e `_parse_categories` passa a aceitar todas as categorias válidas.
   - A robustez continua a mesma: itens sem id inteiro ou sem nome são ignorados.
   - Uma categoria apagada simplesmente não vem do backend, e a edição já deixa o campo vazio quando o valor atual não está nas opções.
   - O cache de 1 h faz “Alimentos” sumir e “Móveis” aparecer no máximo 1 h depois do deploy, ou logo após reiniciar o servidor.
   - Alternativa descartada: trocar a lista de exclusões por uma lista de permissões. Ela teria de ser atualizada a cada categoria nova.
2. **Ícone de Móveis:** `CATEGORY_ICONS["moveis"] = "sofa"`, no lugar de `house`. O `rx.match` de `categorias.py` já monta os casos a partir dos valores de `CATEGORY_ICONS`, então o ícone novo entra sozinho.
3. **Convite na Explorar vazia.**
   - **Sem filtros** (`has_filters` falso): a página mostra a frase “Ainda não há doações por aqui. Que tal ser a primeira pessoa a doar?” e o botão “Quero Doar”.
   - **Destino do botão:** é escolhido na interface com `rx.cond(LoginState.auth_token, "/cadastro-doacao", login_url("/cadastro-doacao"))`, sem estado novo. O `login_url` já existe em `rotas.py` e valida o `next`.
   - **Com filtros:** continua só o “Limpar filtros”.
4. **Botão “Tentar de novo” compartilhado.**
   - `retry_button(on_click, class_name)` fica em `cabecalho.py`, ao lado de `donate_link`, com o mesmo visual dos botões atuais: contorno, ícone `rotate-cw`, 44 px de altura e foco visível.
   - A cor é `#166B3B`, que dá 6,1:1 sobre o creme (o `#168447` dá só 4,4:1 ali).
   - Os `_state_message` de `minhas_doacoes.py` e `perfil_doador.py` ganham um argumento opcional `*children`, e só o estado de erro passa o botão.
   - **Na home**, há um botão em cada mensagem (contagem e recentes) e os dois chamam `HomeState.load_home_data`. Com as duas falhando juntas aparecem dois botões, cada um ao lado da sua mensagem, o que é mais claro do que um botão solto. As categorias da home estão no cache de 1 h, então a nova tentativa pede só o que falhou ou expirou.
   - **No perfil de quem doa**, o botão chama `DonorProfileState.load_profile`. O estado “não encontrada” não tem botão.
   - **Em Minhas doações**, o botão chama `MyDonationsState.load_page`.
5. **Chat.**
   - `POLL_INTERVAL_MS` passa a 25 000.
   - **“Conversa à mostra”** quer dizer `active_conversation_id > 0` e `mobile_view == "conversation"`. No desktop, abrir uma conversa já põe `mobile_view = "conversation"`, e nada volta para `"list"` sem `back_to_list`, cujo controle só aparece em tela estreita.
   - **A lista** (`list_poll_tick` e `list_poll_if_visible`) não consulta com conversa à mostra. O `rx.moment` da lista continua sempre montado; só o tique não faz nada.
   - **As mensagens** (`poll_tick` e `poll_if_visible`) também não consultam com `mobile_view == "list"`. No celular, com a lista à mostra, a conversa conta como fechada (spec, cenário “Voltar para a lista em tela estreita”). Assim, a cada momento só uma das duas atualizações roda: no máximo um pedido a cada 25–30 s por aba, contra os 6 por minuto de hoje.
   - **`back_to_list`** vira um evento assíncrono: troca a vista e consulta a página 1 da lista uma vez, mesclando como a atualização automática (`_merge_first_page`). Um 429 ou erro nessa consulta é silencioso, como na automática; um 401 leva ao login.
   - **O botão “Atualizar conversas”** continua consultando a qualquer momento.
   - Alternativa descartada: desmontar o `rx.moment` da lista com conversa aberta. Funcionaria igual, mas o tique que retorna cedo é mais simples de testar e já é o padrão do arquivo.
6. **Perfil de quem doa no cache público.**
   - Novo espaço `DONOR = "quem-doa"` em `cache_publico.py`, incluído em `DONATION_NAMESPACES`. Assim, `invalidate_donations()` o descarta junto com os outros.
   - `fetch_donor_profile` passa a usar `cache_publico.cached(DONOR, endpoint, load)`. A chave é o endpoint, que já tem o `donation_id` e a página.
   - Os erros (404, 429, outro status, JSON inválido) são exceções, por isso não ficam guardados.
   - A resposta guardada é só o perfil público, já filtrado por `_parse_donor_profile`, sem e-mail.
   - **Editar o perfil também descarta o cache.** Salvar o perfil, trocar a foto e remover a foto (`editar_perfil.py`) chamam `cache_publico.invalidate_donations()`. O nome, a foto e o Sobre aparecem no perfil de quem doa e no detalhe, então sem isso a mudança levaria até 60 s para aparecer.
7. **`publish_POST.xs`.** Só os inputs mudam, copiando o `donations_PATCH.xs`:
   - `title filters=trim|min:1|max:100`;
   - `description? filters=trim|max:2000`;
   - `delivery_method` com `values = ["A combinar"]`;
   - `contact_preference` com `["E-mail", "Chat do DoaFácil"]`.
   
   O Xano valida os inputs antes do stack, então um título com 101 caracteres é recusado antes da precondição das fotos. O arquivo é validado no Xano Developer MCP. O push fica com o Higor: `xano workspace push -d ./xano -i "api/catalog/catalog/donations/publish_POST.xs" --dry-run`, que deve mostrar só um item, o UPDATE da query `catalog/donations/publish`.
8. **Script real só de entrada inválida.** `scripts/teste_publicar_limites_real.py` reaproveita `base_url`, `json_ou_none`, `login`, `registrar` e `resumo` do `teste_chat_real.py`. Ele envia, autenticado e **sem fotos**:
   - **P1:** título de 101 caracteres. Espera HTTP 400 sem a mensagem “Adicione pelo menos uma foto”, ou seja, recusado pelo título.
   - **P2, controle:** título de 100 caracteres. Espera HTTP 400 com a mensagem das fotos, ou seja, o título passou.
   
   Sem fotos, nenhuma das duas requisições cria doação, nem se o deploy não tiver acontecido. Nesse caso, a P1 falha com a mensagem das fotos e o script explica. O script não imprime token, e-mail nem corpo de resposta.
9. **Testes:**
   - `test_acabamento.py:133` passa a usar `"/\\evil.example"`, o mesmo valor de hoje sem o escape inválido;
   - `:239` troca `alpha.getdata()` por `alpha.tobytes()`, que dá um byte por pixel num canal `L` e existe em qualquer versão do Pillow.

## Riscos / Concessões

- **[O cache de categorias de 1 h atrasa a troca Alimentos/Móveis]** → Reiniciar o servidor no deploy, ou esperar 1 h. Fica anotado no roteiro manual.
- **[No desktop, a lista não se atualiza sozinha com conversa aberta, e uma conversa nova de outra pessoa só aparece pelo ⟳ ou ao recarregar]** → É o comportamento pedido. O total de não lidas no botão flutuante segue a regra de 60 s nas outras páginas.
- **[Outro consumidor do `publish` que envie “WhatsApp”, “Retirada”, “Entrega” ou textos longos passa a receber 400]** → O site não envia esses valores desde as changes anteriores. O dry-run e o aviso ao grupo antes do push são obrigatórios (guia, seção 8).
- **[O `back_to_list` passa a fazer um pedido]** → É um pedido por ação da pessoa, no lugar das consultas automáticas da lista e das mensagens que paravam de existir.

## Plano de implantação

1. Reflex: o deploy normal, reiniciando o servidor para limpar os caches.
2. Xano (Higor):
   1. dry-run com `-i` só do `publish_POST.xs`;
   2. conferir que aparece 1 UPDATE;
   3. OK do grupo;
   4. push;
   5. rodar `python scripts/teste_publicar_limites_real.py`.
3. Volta atrás: o Reflex volta pelo commit anterior; o Xano, com push do arquivo anterior com `-i`.
