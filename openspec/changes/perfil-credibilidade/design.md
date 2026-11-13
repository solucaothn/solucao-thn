# Design: perfil-credibilidade

## Contexto

O motivo da change está em `proposal.md`. Abaixo fica o estado atual que define a abordagem.

- **Tabela `user`** (`xano/table/user.xs`): não tem nenhum campo de verificação. Os campos atuais são `name`, `email`, `password`, `city`, `state`, `about`, `photo`, `role` e `password_reset`.
- **Criação de contas:**
  - Desde a change `confirmacao-email-cadastro` (commit `cd794bd`, de 2026-11-04 20:19 -0300, arquivada em 2026-11-05), o **único** `db.add user` do workspace fica no `auth/signup_verify`, depois do código certo.
  - Esse ponto grava em `event_log` o evento `action = "signup_confirmed"`, com o `user_id` da conta criada. O evento existe desde a primeira versão (`cd794bd`).
  - O cadastro antigo (`auth/signup`, antes de `cd794bd`) criava a conta direto e gravava `action = "signup"`.
  - Nada no workspace apaga ou altera linhas de `event_log`.
- **Contadores:**
  - Só o `catalog/donations/mine` conta as doações: `active` (disponíveis + reservadas) e `completed` (concluídas), com dois `db.query ... count`.
  - O `donations/donor` conta só as disponíveis, para a lista. O `detail` e o `auth/profile` não contam nada.
- **E-mail:** o `mine` não devolve o e-mail, que só existe no `auth/profile`. A spec proíbe o e-mail nessa resposta e o e-mail e o selo no cartão.
- **Specs que proíbem o que esta change pede:** a prévia (“MUST NOT mostrar … contadores”), o perfil público (“MUST NOT apresentar selo de e-mail verificado”) e o detalhe (“ocultos … indicadores de conta ou e-mail verificados”). Os deltas trocam essas proibições.
- **Tasks no projeto:** ainda não há nenhuma task (`xano/task/`). A doc do MCP confirma o formato `task "<nome>" { stack {...} schedule = [{starts_on, freq, ends_on}] }`.
- **Frontend:**
  - os cartões estão em `doafacil/minhas_doacoes.py` (`_owner_card`), `perfil_doador.py` (`_identity_card`), `detalhe_doacao.py` (`_donor_card_content`) e `editar_perfil.py` (`_preview`);
  - o rótulo no singular (“Doação”, “Doação realizada”) já existe em “Minhas doações”;
  - o `avatar()` compartilhado fica em `doafacil/perfil_publico.py`.

## Objetivos e não objetivos

**Objetivos:**

- O selo nunca aparece para uma conta que não confirmou o e-mail. Na dúvida, a conta fica sem selo.
- A marcação inicial é única, idempotente, auditável só com contagens e reversível.
- Os contadores e o selo vêm nas quatro respostas que já existem, com os mesmos nomes de campo em todas.
- O mesmo componente de contadores e de selo serve às quatro telas.

**Não objetivos:**

- Uma forma de contas antigas confirmarem o e-mail depois.
- Mostrar a data da verificação.
- Guardar o selo em cache no frontend.
- Mudar o chat ou os cartões da home.

## Decisões

### 1. Campo `bool email_verified?=false` em `user`

- O campo é opcional e começa falso.
- As contas que já existem podem ler `null` até a marcação inicial. Por isso toda resposta devolve `($user.email_verified == true)`, um booleano estrito, e nunca `null`. A sintaxe do default e da comparação será validada no MCP.
- O `PATCH auth/profile` não aceita o campo: a entrada já é fechada (nome, cidade, estado e Sobre). Um teste real confirma que um `email_verified=false` enviado é ignorado.

**Alternativas consideradas:**

- *`timestamp email_verified_at`*: daria mais informação, mas a decisão 3 pede um booleano e a data não aparece em lugar nenhum.
- *Calcular o selo em cada resposta pela data de criação:* evita a migração, mas espalha a regra pelos quatro endpoints e não serve para contas futuras criadas de outro jeito.

### 2. `signup_verify` grava `email_verified: true` no `db.add user`

O campo entra no mesmo `data` que já existe, dentro da transação. Nenhuma outra lógica do endpoint muda.

### 3. Nomes dos campos nas respostas

O `active` e o `completed` têm o mesmo significado da `mine`.

| Endpoint | Contadores | Selo | E-mail |
|---|---|---|---|
| `GET auth/profile` | `counts: {active, completed}` | `email_verified` | já existe |
| `GET catalog/donations/mine` | `counts` (já existe) | `owner.email_verified` | `owner.email` (novo) |
| `GET catalog/donations/donor` | `donor.counts: {active, completed}` | `donor.email_verified` | nunca |
| `GET catalog/donations/detail` | `donor_counts: {active, completed}` | `donor_email_verified` | nunca |

O detalhe segue o padrão plano que já usa (`donor_first_name`, `donor_photo`).

### 4. Contagens

- São duas consultas `count` por resposta: ativas (`disponível` ou `reservada`) e concluídas.
- O `owner_id` vem da doação (no `donor` e no `detail`) ou do `$auth.id` (no `profile`). São as mesmas cláusulas `where` da `mine`, copiadas.
- No `donor`, a contagem das disponíveis para a lista continua separada. Ela não é juntada à de ativas, para não mudar o `total` e a paginação.

**Alternativa considerada:** uma única consulta das doações da pessoa, contada no XanoScript. Ela traria linhas sem necessidade, e o `count` do banco é mais barato.

### 5. Marcação inicial por uma task temporária, em duas rodadas

Arquivo: `xano/task/marcar_email_verificado_inicial.xs`.

- **Critério** (decisão 3, com mais segurança): a conta fica verdadeira quando cumpre as duas condições:
  - existe um `event_log` com `action = "signup_confirmed"` e `user_id` igual ao dela;
  - foi criada a partir de **2026-11-04 00:00 no horário de Brasília** (`2026-11-04 03:00:00+0000`), o dia em que a confirmação foi publicada.
- **Por que as duas condições:**
  - o evento prova que a conta passou pelo código, porque só o `signup_verify` o grava;
  - a data cumpre a decisão 3 e protege contra um evento gravado à mão;
  - uma conta criada pelo cadastro antigo no próprio dia 04 tem o evento `signup`, e não `signup_confirmed`, e fica de fora;
  - um evento que falte deixa a conta sem selo, que é o lado seguro.
- **Lógica:**
  - lê os `event_log` `signup_confirmed`, só com o `user_id`;
  - para cada `user_id` sem repetição, lê a conta só com o `created_at` e o `email_verified`;
  - grava `true` só se a conta cumprir a data e ainda não for verdadeira;
  - nunca grava `false` e nunca mexe em outro campo. Repetir a task não muda nada.
- **Auditoria:** um `debug.log` só com números:
  - `eventos`, `contas_marcadas`, `ja_verificadas`, `fora_da_data`, `conta_inexistente` e `total_de_contas`;
  - os não verificados saem como `total_de_contas - verificadas`;
  - nenhum e-mail, nome ou id.
- **Duas rodadas:**
  1. a primeira versão publicada tem `var $aplicar { value = false }` e só conta. O Higor lê o log da execução no Xano e confere se os números batem com o esperado (por exemplo, as contas de teste dos scripts);
  2. a segunda versão troca `$aplicar` para `true` e publica de novo. Depois do teste real, um terceiro push **apaga a task**.
- **Agendamento:** `starts_on` alguns minutos depois do push, `freq` de 86400 e `ends_on` uma hora depois do início, para rodar uma vez. Se o Xano permitir rodar a task na hora pelo painel, o Higor pode usar isso no lugar de esperar. A sintaxe será confirmada no MCP.
- **Reversão:** uma task igual, com o mesmo critério, gravando `false`. Como antes da change ninguém tinha o campo, voltar todo mundo a `false` também é seguro.

**Alternativas consideradas:**

- *Endpoint temporário, mesmo restrito a admin:* fica exposto na internet enquanto existir. Recusada.
- *Editar a tabela à mão no painel do Xano:* sem registro, sujeita a erro e contra a regra de que as mudanças passam pelos arquivos e pelo CLI. Recusada.
- *Só a data, como na decisão 3 literal:* depende de saber a hora exata do push e marcaria uma conta criada pelo cadastro antigo no dia 04. Fica como alternativa na dúvida 1.
- *Uma rodada só, já aplicando:* um push a menos, mas sem conferir os números antes. Fica como alternativa na dúvida 2.

### 6. Frontend: componentes compartilhados em `doafacil/perfil_publico.py`

- **`verified_badge(flag)`:**
  - com `flag` falso, renderiza nada (`rx.fragment`);
  - com `flag` verdadeiro, mostra uma pílula com o ícone `badge-check` do Lucide (`aria-hidden`) e o texto “E-mail verificado”;
  - cores propostas: texto e ícone `#166B3B` sobre fundo `#E8F5EC`, com borda `#B7DEC4`. O `#166B3B` sobre o `#E8F5EC` dá cerca de 6:1 (AA). O valor exato será medido no teste de contraste.
- **`donation_counts(active, completed)`:** os dois números em `#166B3B` com os rótulos “Doações” e “Doações realizadas”, no singular com 1. O código atual de “Minhas doações” passa a usar esse componente.
- **Parsers:**
  - o `email_verified` precisa ser `bool`, e qualquer outro tipo é resposta inválida;
  - os contadores precisam ser inteiros `>= 0`.
- **Onde cada tela usa:**
  - **Prévia:** os contadores e o selo vêm do `GET auth/profile`. Não acompanham a digitação e não fazem requisição nova.
  - **“Minhas doações”:** o e-mail entra abaixo do primeiro nome, em `#555555`, com `overflow-wrap: anywhere`, e o selo abaixo do e-mail, como no frame `Group 6`.
  - **Perfil público:** os contadores e o selo ficam abaixo de “No DoaFácil desde …”, antes do Sobre.
  - **“Quem doa”:** os contadores ficam numa linha abaixo do nome e da cidade, e o selo abaixo deles. O cartão continua sendo um link único.
- **Figma:** a posição e o estilo exatos do e-mail e do selo saem do frame `Group 6`, lido no apply. Nesta proposta, o MCP do Figma não respondeu.

## Riscos e trade-offs

- **Divergência entre o selo e a realidade** → o critério duplo e a rodada de contagem. Na dúvida, a conta fica sem selo.
- **Uma conta de 2026-11-04 criada pelo cadastro antigo** → fica de fora pelo critério do evento.
- **Linhas de `event_log` apagadas no futuro** → não afetam quem já foi marcado. Uma conta nova é marcada no próprio `signup_verify`, sem depender do evento.
- **Os contadores públicos revelam quantas doações estão reservadas,** somadas às disponíveis → é a decisão 2 do grupo. O detalhe por status nunca é exposto.
- **Duas contagens a mais** no `donor`, no `detail` e no `profile` → as consultas usam o `owner_id` e o status. A latência é medida no teste real. Se ficar ruim, um índice em `donation.owner_id` entra numa change própria.
- **A task esquecida no workspace** → a tarefa de apagá-la faz parte da change. O archive só acontece depois do push que a apaga.
- **Scripts reais que conferem as chaves exatas** (PP1, MD2, EP2, EP3 e EP11) → são ajustados na Parte A.
- **O perfil público mostra dois números parecidos,** “Doações N” (ativas) e “Doações disponíveis · M itens” (só disponíveis) → veja a dúvida 3.

## Plano de migração

1. **Parte A, no Xano:**
   - o campo, o `signup_verify`, as quatro respostas e a task em modo contagem;
   - dry-run e push feitos pelo Higor;
   - leitura do log da contagem;
   - a task em modo aplicar, com dry-run e push;
   - o teste real;
   - o push que apaga a task.
2. **Parte B, no frontend:** os componentes, as quatro telas, os testes e a documentação.
3. **Reversão:**
   - os campos novos nas respostas são aditivos. O frontend antigo ignora chaves a mais, mas os scripts de teste real precisam do ajuste da Parte A;
   - o selo é desligado pela task de reversão (decisão 5).

## Dúvidas para o grupo

1. **Critério da marcação inicial.**
   - *Recomendo:* o evento `signup_confirmed` **e** a data a partir de 2026-11-04 (Brasília).
   - *Alternativa:* só a data, como na decisão 3 literal. Nesse caso, falta confirmar a hora exata do push no histórico do Xano.
   - Confirme também que a publicação foi em 2026-11-04, a data do commit `cd794bd`. A change foi arquivada em 2026-11-05.
2. **Rodadas da task.**
   - *Recomendo:* duas, uma só contando e outra aplicando, com um terceiro push para apagar a task.
   - *Alternativa:* uma rodada só, já aplicando, e o push para apagar.
3. **Contadores no perfil público.**
   - Ao lado de “Doações disponíveis · N itens”, o “Doações” soma as disponíveis e as reservadas, então os números podem diferir.
   - *Recomendo:* manter, como na decisão 2, e registrar a diferença no README.
   - *Alternativa:* no perfil público, o rótulo “Doações ativas”.
4. **Estilo do selo.**
   - *Recomendo:* a pílula verde-clara (`#E8F5EC`), com o ícone `badge-check` e o texto `#166B3B`, ajustada ao frame `Group 6` no apply.
   - *Alternativa:* só o ícone e o texto, sem fundo.
5. **Contas antigas.**
   - Confirme que, nesta change, as contas anteriores ficam sem selo para sempre.
   - Uma “verificar meu e-mail” para elas seria uma change própria.
