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
  2. a segunda versão troca `$aplicar` para `true` e publica de novo. Depois do teste real, a task e a function são removidas pelo painel (veja a decisão 5a, que substitui o “terceiro push”).
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
- **A task ou a function esquecidas no workspace** → a remoção pelo painel e o pull de conferência fazem parte da change. O archive só acontece depois dela.
- **O plano gratuito não aceitar tasks** → a Forma 2 da decisão 5a roda a mesma function pelo painel.
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

## Respostas às dúvidas (tarefa 1.1)

1. **Critério da marcação inicial:** critério duplo. A conta precisa ter o evento `signup_confirmed` **e** ter sido criada a partir de 2026-11-04, no horário de Brasília. O Higor confirmou que a publicação foi nesse dia. O corte é `2026-11-04 00:00 -03:00`, igual a `2026-11-04 03:00:00+0000`, ou `1793761200000` em ms.
2. **Rodadas:** duas, uma contando e outra aplicando, e depois a remoção da task (veja a decisão 5a sobre como remover).
3. **Contadores no perfil público:** manter “Doações” (disponíveis + reservadas) e registrar no README a diferença em relação a “Doações disponíveis · N itens”.
4. **Selo:** pílula `#E8F5EC` com o ícone `badge-check` e o texto `#166B3B`.
5. **Contas antigas:** ficam sem selo nesta change.

### 5a. Duas formas de rodar a marcação (depois da 1.1)

O plano gratuito do Xano já recusou o `storage.create_attachment` (“Please upgrade”), e as tasks podem ter a mesma limitação. Por isso a lógica fica numa **function**, e a task é só um invólucro dela.

- **`xano/function/credibilidade/marcar_email_verificado_inicial.xs`**, a function `Credibilidade/marcar_email_verificado_inicial`:
  - tem a entrada `bool aplicar?=false`;
  - faz a lógica da decisão 5 e devolve só as contagens: `aplicar`, `eventos`, `contas_com_evento`, `a_marcar`, `contas_marcadas`, `ja_verificadas`, `fora_da_data`, `conta_inexistente`, `total_de_contas` e `verificadas_no_fim`;
  - também grava as contagens com `debug.log`;
  - não é endpoint: só pode ser executada por outro stack ou pelo painel.
- **`xano/task/marcar_email_verificado_inicial.xs`**: chama a function com `aplicar` fixo e grava o resultado com `debug.log`. O agendamento roda uma vez, com `starts_on`, `freq: 86400` e `ends_on` uma hora depois. O Higor ajusta o horário antes do push, se for preciso.
- **Forma 1, com a task:**
  1. push da function e da task com `aplicar: false`;
  2. a task roda, e o Higor lê o resultado no histórico;
  3. a task passa a `aplicar: true`, com um novo `starts_on`, e é publicada de novo.
- **Forma 2, sem a task** (se o dry-run ou o push recusarem a task, ou se o plano não rodá-la):
  1. push só da function, excluindo `task/**`;
  2. o Higor roda a function no painel (**Run & Debug**) com `aplicar = false` e lê as contagens;
  3. depois roda com `aplicar = true`.

  Não há endpoint exposto e nem um push a mais entre as rodadas.
- **Forma usada: a 2.** O push saiu com `-e "task/**"`, e a task nunca foi publicada. O arquivo local dela foi apagado. As rodadas no Run & Debug deram estes números (só contagens):

  | Rodada | eventos | contas_com_evento | a_marcar | contas_marcadas | ja_verificadas | fora_da_data | conta_inexistente | total_de_contas | verificadas_no_fim |
  |---|---|---|---|---|---|---|---|---|---|
  | Contagem (`aplicar = false`) | 6 | 6 | 3 | 0 | 0 | 0 | 3 | 3 | — |
  | Aplicação (`aplicar = true`) | — | — | 3 | 3 | — | — | — | 3 | 3 |

  - Os 3 de `conta_inexistente` são eventos de contas que já foram apagadas. A function os ignora, como previsto.
  - Depois da aplicação, `verificadas_no_fim` é igual a `total_de_contas`. Logo, uma nova contagem daria `a_marcar = 0`.
- **Remoção depois do teste real:**
  - O push parcial da CLI é aditivo: apagar o arquivo não apaga o objeto no workspace. Remover exige `--sync --delete`, que apaga **tudo** o que não existe nos arquivos locais. Esse risco é alto num workspace compartilhado com divergências.
  - Por isso a function é apagada pelo Higor **no painel do Xano** (a task não existe, porque foi usada a Forma 2). Depois vêm um pull e a remoção do arquivo local.
  - A function só roda quando chamada, então não oferece risco se ficar até a remoção.
- **Notas do MCP (tarefa 2.1):**
  - `bool x?=false` é um campo opcional com default, e a doc pede campos novos no fim do `schema`;
  - `db.query` aceita `return = {type: "count"}` e `output`;
  - `conditional` usa `elseif`;
  - `map`, `unique` e `count` existem como filtros;
  - o `debug.log` aparece no histórico de requisições, e a doc pede para não registrar dados pessoais;
  - a task usa `schedule = [{starts_on, freq, ends_on}]` (UTC);
  - a doc da CLI diz que o push padrão é parcial e aditivo e que `--delete` exige `--sync`;
  - a doc não diz se uma task pode ser disparada na hora pelo painel. Se puder, o Higor usa isso no lugar de esperar o `starts_on`;
  - as linhas antigas leem `null` no campo novo, por isso toda resposta usa `($x.email_verified == true)`.

## Apêndice: a function que foi rodada

Este é o registro da function `Credibilidade/marcar_email_verificado_inicial`, como foi publicada e rodada no Run & Debug (Forma 2). Ela foi rodada com `aplicar = false` e depois com `aplicar = true`, e os números estão na decisão 5a. Depois do teste real, o Higor a apagou pelo painel do Xano, e o arquivo local `xano/function/credibilidade/marcar_email_verificado_inicial.xs` foi removido. O código fica aqui só como registro: ele não deve ser publicado de novo.

```xanoscript
// Marcação inicial do e-mail verificado (change perfil-credibilidade).
// TEMPORÁRIA: apagar pelo painel depois do teste real.
//
// Marca email_verified = true somente nas contas com as duas provas:
// - um event_log "signup_confirmed" (gravado só pelo auth/signup_verify);
// - created_at a partir de 2026-11-04 00:00 (Brasília) = 1793761200000 ms.
// Nunca grava false, nunca mexe em outro campo e pode ser repetida sem efeito
// novo. Com aplicar = false, só conta. O log e a resposta têm só números:
// nenhum e-mail, nome ou id.
function "Credibilidade/marcar_email_verificado_inicial" {
  input {
    bool aplicar?=false
  }

  stack {
    var $inicio {
      value = 1793761200000
    }

    db.query event_log {
      where = $db.event_log.action == "signup_confirmed"
      return = {type: "list"}
      output = ["user_id"]
    } as $eventos

    var $ids {
      value = $eventos
        |map:$$.user_id
        |unique
    }

    var $a_marcar {
      value = 0
    }

    var $contas_marcadas {
      value = 0
    }

    var $ja_verificadas {
      value = 0
    }

    var $fora_da_data {
      value = 0
    }

    var $conta_inexistente {
      value = 0
    }

    foreach ($ids) {
      each as $user_id {
        db.get user {
          field_name = "id"
          field_value = $user_id
          output = ["id", "created_at", "email_verified"]
        } as $conta

        conditional {
          if ($conta == null) {
            var.update $conta_inexistente {
              value = $conta_inexistente + 1
            }
          }

          elseif ($conta.email_verified == true) {
            var.update $ja_verificadas {
              value = $ja_verificadas + 1
            }
          }

          elseif ($conta.created_at < $inicio) {
            var.update $fora_da_data {
              value = $fora_da_data + 1
            }
          }

          else {
            var.update $a_marcar {
              value = $a_marcar + 1
            }

            conditional {
              if ($input.aplicar) {
                db.edit user {
                  field_name = "id"
                  field_value = $conta.id
                  data = {email_verified: true}
                  output = ["id"]
                } as $marcada

                var.update $contas_marcadas {
                  value = $contas_marcadas + 1
                }
              }
            }
          }
        }
      }
    }

    db.query user {
      return = {type: "count"}
    } as $total_de_contas

    db.query user {
      where = $db.user.email_verified == true
      return = {type: "count"}
    } as $verificadas_no_fim

    var $resultado {
      value = {
        aplicar          : $input.aplicar
        eventos          : $eventos|count
        contas_com_evento: $ids|count
        a_marcar         : $a_marcar
        contas_marcadas  : $contas_marcadas
        ja_verificadas   : $ja_verificadas
        fora_da_data     : $fora_da_data
        conta_inexistente: $conta_inexistente
        total_de_contas  : $total_de_contas
        verificadas_no_fim: $verificadas_no_fim
      }
    }

    debug.log {
      value = $resultado
    }
  }

  response = $resultado
  guid = "atyrRi7FECZDivCnUpnmzLgDVbg"
}
```
