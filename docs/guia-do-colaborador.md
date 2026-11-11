# Guia do colaborador — DoaFácil

Este guia explica como trabalhar no DoaFácil sem quebrar o que já funciona. Leia inteiro antes de mexer em qualquer coisa. Ele vale para pessoas e para agentes de código (Copilot etc.).

Última atualização: 10/11/2026.

## 1. O que é o projeto

O DoaFácil é uma plataforma web (projeto acadêmico em grupo) que conecta quem quer doar objetos físicos a quem precisa.

Fora do escopo: dinheiro, vaquinha, marketplace, rede social genérica e alimentos.

Fora do MVP: "Pessoas alcançadas" e "Desapego em grupo".

## 2. Tecnologias

- **Frontend:** Reflex (Python). Só Reflex, sem outro framework.
- **Backend:** Xano (plano gratuito). Regras de negócio, autenticação e validação ficam no Xano.
- **Especificação:** OpenSpec.
- **E-mail:** SendGrid, chamado pelo Xano.
- **Versionamento:** Git e GitHub (repositório público: `solucaothn/solucao-thn`).

## 3. Regras de ouro

1. **O repositório é público.** Nunca coloque senha, token, chave de API ou endereço de ambiente em arquivo, commit, chat ou print.
2. **Segredos vivem só em variáveis do workspace do Xano** (por exemplo `SENDGRID_API_KEY` e `SENDGRID_FROM_EMAIL`).
3. **O Xano é compartilhado.** O que você publica lá afeta o grupo todo. Antes de qualquer push ao Xano: pull com a árvore commitada, dry-run revisado e aviso ao grupo.
4. **Um ciclo do OpenSpec por vez** (explore, propose, review, apply, archive).
5. **Nada de force push**, de apagar branches ou de mexer no histórico da `main`.
6. **Conferir sempre** com `git status -sb` antes de commitar. Agentes de código às vezes afirmam o que não verificaram.

## 4. Preparando o ambiente

Pasta do projeto: `Solução-THN` (com hífen). Cuidado com pastas parecidas.

No PowerShell, na raiz do projeto:

```
.venv/Scripts/Activate.ps1
```

Dependências ficam em `requirements.txt`. Ferramentas globais: Xano CLI e OpenSpec.

Para ver o site, a cada terminal novo, defina as duas variáveis de ambiente com os endereços base dos grupos de API do Xano (peça ao grupo; não são segredos, mas **nunca** vão para arquivo ou Git):

- `XANO_API_URL` (grupo Catalog)
- `XANO_AUTH_API_URL` (grupo Authentication)

Depois:

```
reflex run
```

e abra `http://localhost:3000`. Se a porta estiver ocupada, o Reflex usa outra.

Rodar os testes:

```
python -m unittest discover -s tests -v
```

## 5. Estrutura do repositório

- `doafacil/`: código do frontend (`doafacil.py`, `login.py`, `cadastro.py`, `cadastro_doacao.py`, `recuperacao_senha.py`, `detalhe_doacao.py`, `chat.py`).
- `assets/`: CSS de animação, logo, imagens e favicon.
- `tests/`: testes com `unittest`.
- `docs/`: visão geral, modelo de domínio, este guia e `design/` (telas em PNG + README).
- `openspec/`: specs principais e changes (ativas e arquivadas).
- `xano/`: cópia local do workspace do Xano.
- `AGENTS.md`: regras para agentes de código.

## 6. O que já está pronto (na `main`)

- Home pública (carrossel, contagem de doações, "Comece por aqui", seção institucional, rodapé).
- Login (`/login`) e cadastro (`/cadastro`).
- Cabeçalho logado ("Olá, nome" e "Sair").
- Animação de entrada nas páginas.
- Recuperação de senha por código: API no Xano e as três telas (`/recuperar-senha`, `/verificar-email`, `/nova-senha`).
- Cadastro de doação em 5 etapas (`/cadastro-doacao`) e endpoint `catalog/donations/publish`.
- Chat da doação: página `/chat` (lista de conversas e mensagens), botão “Chat” no detalhe da doação e link “Mensagens” no cabeçalho logado da home. Veja “Chat da doação” na seção 8.

## 7. O que ainda falta

- Explorar Doações (ainda sem design).
- Detalhe da doação e Minhas doações.
- **Pendência:** `DELETE /catalog/donations` apaga mensagens, conversas e a doação, mas não as linhas de `donation_photo` dessa doação. As fotos ficam órfãs no banco. Corrigir numa change própria, combinada com o grupo.
- Interesse, avaliações e administração (sem tabelas ainda).
- Páginas "Como funciona" e "Categorias".
- Botões e links da home que ainda não levam a lugar nenhum.

Em aberto com o grupo: status e transições da doação, mensagens entre usuários, avaliações, moderação e o destino dos 3 endpoints antigos do modelo do Xano (`request_reset_link`, `magic-link-login` e `update_password`).

## 8. Decisões já tomadas (não reabrir sem o grupo)

- Login só por e-mail (sem CPF).
- Cadastro: nome, e-mail, cidade, estado, senha e confirmar senha (sem telefone).
- Senha: mínimo de 8 caracteres, com letra e dígito. E-mail em minúsculas e único.
- Localização da doação = cidade e estado do perfil de quem doa.
- Etiqueta NOVO = doação criada nos últimos 7 dias.
- Condição da doação: Ótimo, Bom ou Regular.
- A home mostra só doações disponíveis.
- Sessão: o token fica só no estado do Reflex. Recarregar a mesma aba mantém o login; abrir outra aba ou reiniciar o servidor desloga.
- Logs de evento guardam só `user_id`, ação e data. Nunca e-mail, nome, código, token ou senha.
- Recuperação de senha: código de 6 dígitos, válido por 10 minutos, 5 tentativas por código, reenvio após 30 segundos, no máximo 5 envios por hora. As respostas são neutras (não revelam se a conta existe). Trocar a senha não cria sessão: a pessoa volta ao login com um aviso verde.
- Toda página nova tem animação de entrada, conforme o `AGENTS.md`.

### Confirmação de e-mail no cadastro

A conta só é criada depois que a pessoa confirma o código enviado ao e-mail. O fluxo usa:

- `POST /auth/signup`: valida os dados e inicia ou atualiza a pendência. Não cria conta nem sessão e não devolve token de autenticação.
- `POST /auth/signup_resend`: solicita outro código para o e-mail da pendência.
- `POST /auth/signup_verify`: recebe e-mail, código e senha; cria a conta somente se o código e a senha forem válidos. A resposta não cria sessão nem contém token.
- Tabela `signup_pending`: mantém os dados necessários ao cadastro pendente, o hash do código, tentativas, horários de envio e expiração. Não armazena a senha.
- Função `Signup/send_confirmation_code`: envia o código de cadastro pelo SendGrid; não reutiliza o envio de recuperação de senha.

O código tem seis dígitos, vale por 10 minutos e pode ser tentado até cinco vezes. Um novo envio só é permitido após 30 segundos e há no máximo cinco envios por hora. A pendência expira 24 horas depois do último envio permitido e só é removida quando acessada após expirar. Os limites e a validação são aplicados no Xano.

As respostas de `auth/signup` são neutras mesmo quando o e-mail já pertence a uma conta: o status e o corpo não revelam essa condição, embora o tempo de resposta possa diferir. E-mail existente não deve gerar pendência nem envio de código.

A senha é enviada ao Xano para validação no início e novamente na verificação, mas nunca é gravada no Xano. Após o início aceito, fica somente no estado transitório do Reflex até a verificação, e é apagada ao concluir ou ao usar “Usar outro e-mail”. O valor de “Confirmar senha” chega transitoriamente ao servidor Reflex junto ao envio do formulário, mas não é guardado no estado nem enviado ao Xano. O código também não fica no estado Reflex.

O estado de cadastro pendente é transitório no servidor Reflex: reiniciar o servidor ou abrir outra aba pode perdê-lo. Se a guarda da tela `/verificar-email` não encontrar o e-mail no estado, redireciona para `/recuperar-senha`; iniciar novamente o cadastro permite obter um novo estado de fluxo. No fluxo de cadastro, “Usar outro e-mail” limpa e-mail e senha e retorna a `/cadastro`.

Nas validações Xano desse fluxo, e-mail e código usam verificações de comprimento com `strlen` em vez de padrões de regex com barra invertida. A senha segue as regras da conta: mínimo de oito caracteres, com letra e dígito.

### Fotos obrigatórias na publicação de doações

A foto da doação é obrigatória tanto no wizard quanto no backend. O endpoint `POST /catalog/donations/publish` recusa `photos` ausente, nulo ou vazio com erro `inputerror` (HTTP 400) e a mensagem “Adicione pelo menos uma foto para continuar.”. Essa validação ocorre antes de qualquer upload ou gravação. O limite continua sendo de cinco fotos.

O corpo do erro contém os campos `code` (`ERROR_CODE_INPUT_ERROR`), `message` e `payload`. O site procura a mensagem “Adicione pelo menos uma foto para continuar.” em qualquer campo textual do JSON de erro e, quando a encontra, mostra a mesma mensagem sem limpar os dados do formulário nem marcar a doação como publicada. Outros erros continuam usando o tratamento genérico.

O campo `donation_photo.photo` é obrigatório. A auditoria confirmou que não havia linhas dessa tabela sem foto antes da alteração. Doações antigas com `donation.photo` vazio não foram alteradas.

O endpoint `publish` foi criado por outro integrante e pode ter outros consumidores. Antes do push real de mudanças nele, avise o grupo, obtenha o OK explícito do grupo e a confirmação necessária para publicar. Revise o dry-run e interrompa a publicação se ele mostrar alterações fora do escopo aprovado.

### Chat da doação (backend)

O chat entre quem doa e quem tem interesse tem o backend no Xano (abaixo) e a tela em `/chat` (veja “Tela do chat” no fim desta seção).

Tabelas:

- `chat_conversation`: uma conversa por par doação + interessado (índice único), com `donor_id`, `interested_user_id` e `last_message_at`. Os campos `donor_last_read_message_id` e `interested_last_read_message_id` guardam o id da última mensagem lida por cada participante (0, ou vazio, quando ainda não leu nada).
- `chat_message`: mensagens da conversa, com `sender_id`, `text`, `created_at` e `edited_at` (horário da última edição; vazio se a mensagem nunca foi editada).

Endpoints (grupo Catalog, todos exigem login; sem login, HTTP 401):

- `POST /catalog/chat/conversations/start` (`donation_id`): inicia a conversa ou devolve a que já existe para essa pessoa e doação. A resposta traz `donation_title` e `donation_status`.
- `GET /catalog/chat/conversations` (`page` e `limit` opcionais; padrão 20, máximo 50): lista as conversas em que a pessoa participa, da mais recente para a mais antiga. Cada item traz `donation_title`, `donation_status` e `unread_count`, o número de mensagens não lidas pela pessoa logada naquela conversa.
- `GET /catalog/chat/unread_total` (sem parâmetros): devolve só `{unread_total}`, a soma das não lidas de todas as conversas da pessoa. Serve para o contador do link “Mensagens” da home e não traz mensagens, nomes nem ids de conversa.
- `GET /catalog/chat/messages` (`conversation_id`; `limit` opcional, padrão 50, máximo 100): lê as mensagens da conversa. A resposta vem sempre em ordem de envio e traz `donation_title`, `donation_status`, `has_older` e `has_newer`. Há três modos:
  - **sem cursor:** as últimas N mensagens; `has_older` diz se há mensagens mais antigas;
  - **`before_message_id`:** as N anteriores a essa mensagem, para o “Carregar anteriores”; `has_older` diz se ainda há mais;
  - **`after_message_id`:** só as posteriores a essa mensagem, para a atualização automática; `has_newer` diz se há mais do que o limite.

  Mandar os dois cursores juntos dá HTTP 400.

  Esse `GET` também **marca a conversa como lida** para quem lê, até a mensagem mais nova devolvida (veja “Mensagens não lidas” abaixo).

  A resposta também traz, em todos os modos:
  - `other_last_read_message_id`: a última mensagem que a **outra** pessoa leu (0 se nenhuma), para o “visto”;
  - `server_time`: o horário do servidor no início da consulta;
  - `edited_messages`: só no modo `after_message_id` com o parâmetro opcional `edited_since` (o `server_time` da consulta anterior). Traz as mensagens já exibidas (`id <= after_message_id`) editadas desde então, com 5 s de folga. Sem `edited_since`, vem vazia.
- `POST /catalog/chat/messages` (`conversation_id`, `message_text`): envia uma mensagem.
- `PATCH /catalog/chat/messages` (`message_id`, `message_text`): edita uma mensagem própria (veja “Edição de mensagens” abaixo).

Cada mensagem (na leitura, no envio e na edição) traz `sent_by_me`, verdadeiro quando foi a pessoa logada que enviou. É assim que a tela decide o lado da mensagem, em vez de comparar nomes, que podem se repetir. O campo é calculado pela sessão, e a resposta não traz identificadores de usuário. Cada mensagem também traz `edited_at`, vazio enquanto não for editada.

Regras:

- **404 genérico:** conversa ou doação inexistente, de outra pessoa ou fora das condições recebe sempre a mesma resposta “Conversa não encontrada.”, para não revelar o que existe. Isso inclui a dona tentando abrir conversa na própria doação.
- **Quem pode conversar:** só a dona e a pessoa interessada. Conversa nova só em doação disponível, com contato “Chat do DoaFácil”. Enviar mensagem só com a doação disponível ou reservada.
- **Só o primeiro nome:** as respostas identificam a outra pessoa e o remetente apenas pelo primeiro nome. Nunca trazem e-mail nem sobrenome.
- **Status visível só para participantes:** `donation_status` aparece nos endpoints do chat para as duas pessoas da conversa. É o mesmo status já público no detalhe da doação. A resposta de um envio recusado continua com o 404 genérico, sem dizer o status.
- **Tamanho:** de 1 a 1000 caracteres depois de tirar espaços das pontas; fora disso, HTTP 400. O tamanho é validado antes do limite de envio. O texto é guardado e devolvido como texto, e a interface precisa mostrá-lo como texto, sem interpretar HTML.
- **Limite de envio:** 10 mensagens por pessoa em 60 segundos, somando todas as conversas; acima disso, HTTP 429 com “Limite de mensagens atingido. Tente novamente em instantes.”. É de melhor esforço: sob envios simultâneos pode passar uma ou duas a mais.
- **Logs:** só `chat_started` (conversa nova), `chat_message_sent` (envio aceito) e `chat_message_edited` (edição que mudou o texto), com `user_id`, ação e data. Leituras (inclusive a marcação de lida), repetições, edições sem mudança e erros não geram evento.
- **Apagar a doação apaga as conversas:** `DELETE /catalog/donations` remove as mensagens, as conversas e a doação na mesma transação. Depois disso, quem tentar ler a conversa recebe o 404 genérico. As linhas de `donation_photo` não são apagadas (pendência registrada na seção 7).

> **Atenção ao limite da plataforma:** o plano gratuito do Xano limita a **instância inteira** a 10 requisições a cada 20 segundos, somando todos os endpoints e todas as pessoas. Acima disso, o próprio Xano responde HTTP 429 com uma mensagem diferente da do chat. Telas com atualização automática (por exemplo, buscar mensagens novas) precisam de intervalo longo entre as consultas, senão derrubam o resto do site.

Mensagens não lidas:

- **O que conta:** mensagens enviadas pela **outra** pessoa com id maior que a última lida por quem consulta. As mensagens da própria pessoa nunca contam.
- **Quando marca como lida:** dentro do `GET /catalog/chat/messages`, em qualquer modo, sem requisição a mais. O campo de quem lê só avança: carregar mensagens anteriores ou uma consulta sem nada novo não grava nada, e o campo da outra pessoa não muda.
- **“Visto” (decisão aprovada pelo Higor na `chat-visto-edicao`):** a leitura de mensagens revela até onde a outra pessoa leu, com `other_last_read_message_id`. É só o id da última mensagem lida, sem horário, e só dentro da conversa. A lista de conversas, o total, o envio e a edição continuam sem nenhum dado de leitura da outra pessoa. A regra antiga, “nenhuma resposta revela até onde a outra pessoa leu”, deixou de valer.
- **Campo vazio vale 0:** depois do pull, a tabela aparece sem o padrão (`int donor_last_read_message_id?`). Os endpoints leem esses campos com `?? 0`, então uma conversa sem leitura gravada conta todas as mensagens da outra pessoa como não lidas. As conversas anteriores a esta mudança começaram assim.
- **Custo:** o `GET conversations` faz uma contagem por item da página, e o `unread_total` faz uma por conversa da pessoa. São consultas no banco, não requisições HTTP a mais.

Edição de mensagens (`PATCH /catalog/chat/messages`):

- **Quem e quando:** só quem enviou, até 15 minutos depois do envio, com a doação disponível ou reservada. O texto novo segue as regras do envio: de 1 a 1000 caracteres depois do trim, sempre como texto simples.
- **Ordem das checagens e respostas:**

  | Ordem | Situação | Resposta |
  |---|---|---|
  | 1 | Tamanho inválido | 400 |
  | 2 | Mensagem inexistente, de outra pessoa ou de conversa de que a pessoa não participa | 404 genérico “Conversa não encontrada.” |
  | 3 | Doação concluída | 404 genérico, como no envio |
  | 4 | Mais de 15 minutos | 400 “O prazo para editar esta mensagem terminou.” |

  Uma mensagem de outra pessoa recebe sempre o 404, mesmo fora do prazo, então o 400 do prazo não revela nada.
- **Texto igual ao atual:** responde 200 com a mensagem, sem gravar, sem mudar `edited_at` e sem log.
- **Sem limite próprio de edições:** valem o prazo de 15 minutos e o limite da plataforma.
- **Resposta:** a mensagem no mesmo formato da leitura, com `edited_at` preenchido.
- **Como a edição chega à outra pessoa:** pela atualização automática que já existe. O frontend manda `edited_since` (o `server_time` da resposta anterior), e as editadas vêm em `edited_messages`. Não há requisição a mais, e o horário vem só do servidor.

Publicar mudanças no chat segue a seção 11: validar no MCP, dry-run revisado, aviso ao grupo e só então o push.

> **Mudança de schema em tabela existente:** o dry-run não mostra campos novos numa tabela que já existe. Depois do push, abra a tabela no painel do Xano e confira se os campos existem, com o tipo certo e o valor esperado nas linhas antigas. Se não aparecerem, crie-os pelo painel com o mesmo nome e tipo e rode um pull para alinhar o arquivo.

#### Tela do chat

O código fica em `doafacil/chat.py`: cliente dos endpoints, `ChatState` e a página `/chat`. Os testes estão em `tests/test_chat.py`, com respostas simuladas no formato real dos endpoints.

Como se entra no chat:

- **Quem tem interesse:** clica em “Chat” no detalhe da doação. O botão inicia a conversa (ou reabre a que já existe) e abre `/chat?conversa=<id>`. Se a doação não aceitar conversa, inclusive quando é a própria pessoa que doou, aparece a mensagem neutra “Não é possível conversar sobre esta doação pelo chat.”.
- **Quem doa:** usa o link “Mensagens” no cabeçalho logado da home (no celular, só o ícone).
- **Sem login:** `/chat` e o botão “Chat” levam ao `/login`. Uma sessão recusada pelo Xano (401) também é limpa e leva ao `/login`.

Atualização automática:

- **Mensagens:** só com uma conversa aberta e a aba visível, a cada 15 segundos. Pede só as mensagens novas (`after_message_id`).
- **Lista de conversas:** com a aba visível, a cada 30 segundos, com ou sem conversa aberta. Pede a página 1, que traz contadores, ordem e conversas novas. Os itens dela entram no topo, e as conversas já carregadas com “Carregar mais conversas” continuam abaixo, sem repetir. O botão “Atualizar conversas” continua funcionando.
- **Quando não roda:** com a aba oculta ou fora de `/chat` não há consultas automáticas. A das mensagens também para sem conversa aberta.
- **Depois de um 429:** qualquer 429 numa consulta automática, das mensagens ou da lista, pausa **as duas** por 60 segundos, sem mostrar erro.
- **Carga no Xano:** com uma conversa aberta, cerca de 6 requisições por minuto por aba (4 das mensagens e 2 da lista); sem conversa aberta, cerca de 2. Não diminua esses intervalos, por causa do limite da plataforma acima.

Contador de não lidas:

- **Na lista:** cada conversa com mensagens não lidas mostra o número num círculo verde `#007A42` à direita, com “99+” acima de 99. Com zero não aparece.
- **Ao abrir uma conversa:** o contador dela some na hora, sem esperar a próxima atualização. Enquanto ela estiver aberta, a lista força 0 para ela, mesmo que uma atualização chegue antes da leitura das mensagens novas. A leitura em si é gravada pelo `GET messages`.
- **Na home:** o link “Mensagens” mostra o total (`GET /catalog/chat/unread_total`), consultado **uma vez por carregamento da home** (`ChatState.load_unread_total`, depois do `LoginState.load_account` no `on_load`). É 1 requisição a mais, só com login. Não há atualização automática; o total se renova ao voltar para a home.
- **Sem login ou com erro:** sem login, nenhuma consulta é feita. Erro ou 401 deixam o total em 0, sem aviso, e a home continua normal.
- **Código e testes:** o formato está em `format_unread` e os rótulos acessíveis em `unread_label` e `messages_link_label`, todos em `doafacil/chat.py` e cobertos por `tests/test_chat.py`.

Textos de erro do envio:

| Situação | Texto |
|---|---|
| 429 do chat (mensagem “Limite de mensagens atingido…”) | “Você enviou muitas mensagens em pouco tempo. Aguarde um minuto.” |
| 429 da plataforma (`ERROR_CODE_TOO_MANY_REQUESTS` com outra mensagem) | “O site está com muitos acessos agora. Tente de novo em instantes.” |
| 400 | “A mensagem precisa ter entre 1 e 1000 caracteres.” |
| 404 | “Não foi possível enviar. Esta conversa não está mais disponível para novas mensagens.” (a conversa passa a somente leitura) |

Em todos os casos o texto digitado continua no campo. Numa doação concluída, o campo e o botão “Enviar” ficam desativados, com aviso de somente leitura. O texto das mensagens é sempre mostrado como texto simples, nunca como HTML.

“Visto” nas próprias mensagens:

- **Onde fica:** na linha do horário, embaixo da bolha, nas mensagens de quem está logado. ✓ cinza `#6b6b6b` quando a outra pessoa ainda não leu (“Enviada”) e ✓✓ verde `#007A42` quando ela já leu (“Lida”). Nas mensagens da outra pessoa não aparece nada.
- **De onde vem:** do `other_last_read_message_id` de cada resposta do `GET messages`. Uma mensagem própria com `id` menor ou igual a ele foi lida. O valor guardado em `other_last_read_id` só aumenta, para não piscar com duas abas, e volta a zero ao trocar de conversa.
- **Atualização:** junto com a atualização automática da conversa (15 s). Não há requisição a mais.

Edição de mensagem:

- **Lápis:** aparece nas próprias mensagens enviadas há até 15 minutos, fora de conversa somente leitura.
  - Quando aparece: no computador, ao passar o mouse; no celular, ao tocar na bolha; também ao receber foco pelo teclado. Essa visibilidade fica em `assets/chat.css`.
  - O prazo é recalculado a cada resposta da atualização automática, então o lápis some sozinho perto do fim. O backend é quem decide: um 400 esconde o lápis daquela mensagem na hora.
- **Editar:**
  - o lápis leva o texto para o campo de baixo, com a faixa “Editando mensagem”;
  - “Enviar” vira “Salvar” e aparece “Cancelar”;
  - Enter salva; Esc ou “Cancelar” saem sem chamar o backend;
  - trocar de conversa ou a doação ser concluída também encerram a edição.
- **Depois de salvar:** a bolha troca o texto e mostra “(editada)” na linha do horário.
- **A edição chegando à outra pessoa:** a consulta automática manda `edited_since` (o `server_time` da resposta anterior) e aplica `edited_messages` pelo id. O “Carregar anteriores” não muda esse horário, para não perder edições. Nenhuma requisição a mais.

Textos de erro da edição (o texto digitado continua no campo):

| Situação | Texto |
|---|---|
| 400 (o tamanho já foi conferido antes, então é o prazo) | “Não foi possível editar. O prazo de 15 minutos terminou.”, e o campo volta ao modo de envio com o texto |
| 404 | “Não foi possível editar esta mensagem.”, e o campo volta ao modo de envio |
| 429, vazio ou acima de 1000 caracteres | os mesmos textos e regras do envio |
| outro erro | “Não foi possível salvar a edição. Tente novamente.” |

**Carga no Xano:** o “visto” e a chegada das edições não somam requisições; cada edição salva é 1 requisição, como um envio. Cada tecla no campo manda um evento ao servidor do Reflex, para o Esc, mas nenhuma requisição ao Xano.

#### Testar o chat contra o Xano real

O script `scripts/teste_chat_real.py` roda os cenários do chat contra o Xano publicado. Ele fica fora de `tests/`, então o `unittest` não o executa.

Antes de rodar, tenha:

- **3 contas de teste:** a dona da doação, uma interessada e uma não participante que nunca tenha tido conversa.
- **1 doação da dona**, disponível e com contato “Chat do DoaFácil”.
- As variáveis `XANO_API_URL` e `XANO_AUTH_API_URL` definidas no terminal (seção 4).

Com o `.venv` ativo, na raiz do projeto:

```
python scripts/teste_chat_real.py
```

O script pede e-mail e senha de cada conta e depois o ID da doação. **A senha não aparece ao digitar**, nem como asteriscos: digite e aperte Enter. Nada é gravado em arquivo, e tokens e e-mails não são impressos. Cada cenário mostra OK ou FALHOU com o status HTTP; nas falhas, só os campos `code` e `message` do erro.

Cuidados:

- **O script cria dados reais:** uma conversa e cerca de 15 mensagens na doação informada, incluindo uma resposta da dona e uma mensagem editada.
- **“Visto” e edição (cenários VE1 a VE11):** rodam também no modo rápido.
  - A interessada envia uma mensagem: o envio devolve `edited_at` vazio.
  - Antes de a dona ler, `other_last_read_message_id` é menor que essa mensagem (✓); depois, é maior ou igual (✓✓).
  - A interessada edita a mensagem (200, com `edited_at`), e a dona recebe a edição em `edited_messages` ao consultar com `after_message_id` e `edited_since`. Sem `edited_since`, a lista vem vazia.
  - Texto igual não muda `edited_at`.
  - A dona editando a mensagem da interessada e um id inexistente dão 404.
  - Texto vazio ou com 1001 caracteres dá 400, e a edição sem token, 401.
  - **VE11, fora do prazo:** só roda se houver, entre as últimas 100 da conversa, uma mensagem própria da interessada com mais de 15 minutos (de uma execução anterior). Senão, é pulado com aviso; rode de novo mais tarde com a mesma doação.
  - **9f, doação concluída:** dentro do cenário 9, que é opcional; editar a mensagem da 9b depois de concluir a doação dá 404.
- **Não lidas (cenários NL1 a NL8):** rodam também no modo rápido (`TESTE_CHAT_RAPIDO=1`).
  - A interessada envia 2 mensagens.
  - A dona deve ver `unread_count` 2 na conversa e o `unread_total` subir 2; depois de ler, os dois voltam.
  - As mensagens da própria interessada não contam para ela.
  - Carregar mensagens anteriores não faz a leitura voltar atrás.
  - O total sem token dá 401.
  - O `unread_total` soma todas as conversas da conta, então o script o compara com o valor medido antes dos envios, e não com 2.
- **Paginação (cenários 8c a 8h):** usa as próprias mensagens da execução, sem envios extras. Precisa de pelo menos 7 mensagens na conversa (3 últimas, 3 anteriores e 1 a mais para `has_older`). Se houver menos, os cenários 8d a 8g são pulados com um aviso.
- **Espere pelo menos 1 minuto entre execuções.** As mensagens da execução anterior ainda contam no limite de 10 por 60 segundos e fazem os cenários falharem.
- O script tem pausas entre as requisições por causa do limite da plataforma, então leva alguns minutos. Não rode outros testes no Xano ao mesmo tempo.
- Opcionalmente, o script pede o ID de uma segunda doação, disponível, com contato por “E-mail” e sem conversa da interessada, para conferir que ela não abre conversa. Enter pula.
- **O cenário 9 conclui a doação, e isso não tem volta.** O script pergunta antes; com `s`, espera cerca de 1 minuto e marca a doação como reservada e depois concluída. Uma doação concluída não serve para uma nova execução.
- **O cenário 10 apaga a doação.** No fim, o script pergunta “Apagar a doação de teste agora? (s/N)”. Só responda `s` se for uma doação de teste; qualquer outra resposta mantém a doação.

## 9. Design

- As telas ficam em `docs/design` como PNG. O `README.md` dessa pasta **prevalece sobre as imagens**.
- O agente de código não lê o Figma; ele lê os PNG.
- Fidelidade ao Figma é importante: cor principal verde, fundo creme, cabeçalho branco, rodapé escuro, fonte LINE Seed JP.
- Ao adicionar imagens, confira a numeração para não repetir número de outra pessoa e **não use espaço no nome do arquivo**.

## 10. Fluxo de trabalho com OpenSpec e Git

Uma entrega, do começo ao fim:

1. Criar uma branch própria a partir da `main` (`feat/...`, `docs/...` ou `chore/...`).
2. Propor a change no OpenSpec (`/opsx-propose`; só cria os artifacts).
3. Revisar a proposta, depois implementar (`/opsx-apply <change>`).
4. Rodar os testes e testar no navegador.
5. Commitar marcando arquivo por arquivo ou por pasta. **Nunca `git add .`**.
6. Push da branch.
7. Abrir o pull request no GitHub, conferir a aba **Files changed** e só então mesclar.
8. `git switch main` e `git pull`.
9. Arquivar a change (`/opsx-archive <change>`), commitar e repetir o fluxo de pull request.

Não confunda: **pull** traz do GitHub para o seu PC, **push** leva do seu PC para o GitHub, **pull request** é o pedido para juntar a sua branch na `main`.

## 10.1 Arquivos do Xano que nunca entram em commit

Depois de um `xano pull`, 8 arquivos aparecem como modificados só por causa da quebra de linha (LF/CRLF). Eles **nunca** entram em commit:

- `xano/api/authentication/auth/login_POST.xs`
- `xano/api/authentication/auth/me_GET.xs`
- `xano/api/authentication/auth/signup_POST.xs`
- `xano/api/authentication/message/send_welcome_email_POST.xs`
- `xano/api/authentication/reset/magic_link_login_POST.xs`
- `xano/api/authentication/reset/update_password_POST.xs`
- `xano/function/quick_start/log_event.xs`
- `xano/table/user.xs`

Se a formatação real de algum deles precisar mudar, isso vai num commit separado e combinado com o grupo.

## 11. Trabalhando com o Xano

- Antes de editar o Xano, confira o status e peça confirmação explícita antes de rodar `xano workspace pull -d ./xano`; preserve todas as alterações preexistentes.
- Consulte o Xano Developer MCP antes de escrever XanoScript e valide nele cada arquivo `.xs` alterado ou criado.
- Rode `xano workspace push -d ./xano --dry-run` e revise a saída completa. Se aparecer alteração não aprovada — especialmente em `donation_photo` ou `password_reset_code` — pare e avise o grupo.
- Avise o grupo e obtenha o OK antes de publicar mudanças que afetam consumidores compartilhados. Obtenha a confirmação explícita necessária imediatamente antes do push real.
- Depois da aprovação, faça o push apenas das alterações previstas. Ao preparar commits, revise cada caminho e adicione arquivos individualmente; nunca use `git add .` em `xano/`, pois o workspace contém alterações compartilhadas que podem não pertencer à tarefa.
- Depois do push, confira o estado do workspace e versione somente os arquivos Xano aprovados para a change.

## 12. Dicas para agentes de código

- Ler `docs/`, `AGENTS.md` e as specs antes de agir.
- Escopo pequeno. Não ampliar o que foi pedido.
- Sem commit, push ou force push sem pedido explícito.
- Não mexer em `xano/` sem pedido explícito.
- Responder em português do Brasil.
- No fim de cada tarefa, mostrar o resumo, o `git status` e o `git diff --stat`.
- Teste manual no navegador é feito por uma pessoa, não pelo agente.

## 13. Problemas comuns

- **Porta ocupada:** o Reflex usa outra porta; veja a mensagem no terminal.
- **Comando quebrado na colagem:** use comandos curtos, um por vez.
- **E-mail de recuperação caiu no spam:** é esperado no ambiente de teste.
- **E-mail não chega:** confira se o endereço de teste está digitado certo e veja os registros de e-mail do SendGrid.
- **Acento quebrado no terminal:** use `-Encoding UTF8` ao ler arquivos com `Get-Content`.
