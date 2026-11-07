# Design

## Contexto

Consulte a [proposta](./proposal.md) para motivação e a delta [donation-chat](./specs/donation-chat/spec.md) para os contratos observáveis. O modelo atual já associa a doação a `owner_id`, armazena status e preferência de contato; a pessoa tem nome completo na tabela de usuários. O endpoint existente de exclusão apaga uma doação sem cuidar de conversas, que ainda não existem.

## Objetivos / Não objetivos

**Objetivos:**

- Fazer a autorização de conversas e mensagens valer no Xano, em cada operação.
- Garantir unicidade da conversa e resultados seguros sob solicitações concorrentes.
- Limitar o custo e o tamanho das consultas periódicas com paginação.
- Preservar a privacidade de participantes em respostas e logs.
- Remover mensagens e conversas sem deixar registros órfãos ao excluir uma doação.

**Não objetivos:**

- Criar ou alterar qualquer interface, rota de página ou comportamento do botão Chat.
- Implementar WebSocket, presença, fotos de perfil, moderação ou notificações.
- Alterar requisitos de capacidades existentes nesta change.

## Decisões

### Persistência mínima e unicidade no banco

Criar `chat_conversation` com o identificador e data de criação padrão, `donation_id`, `donor_id`, `interested_user_id` e `last_message_at`. Um índice único composto em `(donation_id, interested_user_id)` é a garantia final de uma conversa por interessado e doação. Incluir índices para localizar conversas por cada participante e ordenar pela atividade recente, se compatíveis com o schema do Xano.

Criar `chat_message` com identificador e data de criação padrão, `conversation_id`, `sender_id` e `text`, além do índice composto `(conversation_id, id)` para leitura cronológica paginada. O remetente e os participantes são derivados no backend; IDs recebidos do cliente não definem autoria nem acesso.

O início da conversa consulta primeiro a combinação existente e, quando a criação concorre, depende da unicidade no banco. Se uma criação perder a corrida, o endpoint deve recuperar e retornar a conversa existente apenas após revalidar a participação e a elegibilidade de leitura; não deve retornar erro de duplicidade nem criar outra linha.

### Endpoints autenticados com autorização por participante

Implementar as quatro operações no grupo Catalog: iniciar/obter conversa, enviar mensagem, listar mensagens e listar conversas. Todas exigem autenticação Xano. As consultas de conversa verificam doação, participantes e status no backend; não confiar em `donor_id`, `interested_user_id` ou `sender_id` enviados pelo cliente.

Para evitar enumeração, conversa ou doação inexistente, não acessível ou inelegível usa a mesma resposta HTTP 404 genérica. Sessão inválida usa HTTP 401; texto inválido usa HTTP 400; limite de mensagens excedido usa HTTP 429. Não incluir e-mail nem sobrenome em resposta alguma; para identificar a outra pessoa ou remetente, buscar somente o primeiro nome necessário.

Uma conversa nova exige doação disponível, preferência “Chat do DoaFácil” e pessoa autenticada diferente da dona. Repetir a solicitação de uma conversa já existente por um participante retorna a mesma conversa, mesmo que o status atual tenha passado a reservado ou concluído; o status atual define se é possível enviar ou somente ler.

### Mensagens simples, paginação e polling

Validar no backend que a mensagem contém conteúdo não vazio e tem até 1000 caracteres. Armazenar e devolver como texto, sem interpretação ou execução de HTML; a futura interface deverá renderizá-la como texto. Mensagens só podem ser enviadas quando a doação estiver disponível ou reservada.

As mensagens são lidas por cursor `after_message_id`, em ordem crescente de ID, com padrão 50 e máximo 100 por resposta. A lista de conversas usa páginas, ordenadas por `last_message_at` decrescente, com padrão 20 e máximo 50. O identificador da última conversa da página pode servir como cursor com ordenação estável. Não reler todo o histórico a cada consulta.

Não há envio em tempo real nesta mudança. A interface futura consultará os endpoints periodicamente; esta change fornece paginação e não define a frequência do polling.

### Limite por remetente em janela móvel

Contar no máximo dez mensagens por usuário em qualquer janela móvel de 60 segundos, incluindo todas as conversas. O texto só é gravado se a pessoa for participante, a doação permitir envio e o limite não tiver sido excedido. A implementação não deve criar um mecanismo de rate limit que possa ser contornado alternando conversas.

Antes de escolher o mecanismo de contagem, verificar no Xano Developer MCP as opções disponíveis e como compor a consulta e a gravação. Uma contagem seguida de gravação sem coordenação pode permitir que envios simultâneos excedam o limite; validar concorrência no Xano real. Não ampliar o modelo com outra tabela sem revisão do grupo.

### Registro de eventos

Chamar `Quick Start/log_event` somente após criação nova de conversa e após gravação bem-sucedida de mensagem, com `$auth.id` e respectivamente `chat_started` ou `chat_message_sent`. A função registra a data. Não enviar outros dados ou metadados. Não registrar repetição de abertura, leitura, erro de validação, bloqueio pelo limite ou texto rejeitado.

### Exclusão transacional

Modificar `DELETE /catalog/donations` para, após confirmar que a pessoa autenticada é dona, excluir mensagens das conversas da doação, depois as conversas e a doação, na mesma transação. Se uma etapa falhar, a operação não pode deixar remoção parcial. As respostas posteriores para as conversas removidas devem permanecer no 404 genérico.

## Riscos / Compensações

- **Corrida ao criar conversa única** → confiar no índice único, tratar a colisão recuperando a linha existente e validar no Xano real com solicitações concorrentes.
- **Limite de 10 mensagens ultrapassado por solicitações simultâneas** → confirmar mecanismo que aplica o limite por usuário de forma segura; realizar teste concorrente real antes do push. Se não for possível garantir sem mudar o modelo ou as decisões, parar e pedir decisão do grupo.
- **Consultas periódicas caras no plano gratuito** → limitar página, usar cursores e índices; evitar polling de conversas não abertas e acompanhar volume/custo em validação real.
- **Vazamento por respostas de erro ou campos relacionados** → construir saídas explícitas com primeiro nome apenas e uniformizar o 404; testar as quatro APIs para ausência de e-mail e sobrenome.
- **Exclusão parcial de doação** → executar exclusão de mensagens, conversas e doação atomicamente e testar falha intermediária no Xano antes de publicar.
- **Xano é compartilhado e o endpoint DELETE já tem consumidores** → revisar o dry-run completo, parar diante de qualquer objeto inesperado e obter OK explícito do grupo antes do push real.

## Plano de migração

1. Consultar a documentação do Xano Developer MCP antes de escrever XanoScript; definir e validar as duas tabelas, quatro endpoints e a alteração de `donations_DELETE`.
2. Executar testes automatizados disponíveis para as funções/endpoints e validar cada arquivo `.xs` no MCP.
3. Executar e revisar o dry-run. O escopo esperado contém somente `chat_conversation`, `chat_message`, os quatro endpoints novos e `donations_DELETE`; diante de qualquer diferença adicional, parar e avisar o grupo.
4. Avisar o grupo de que `donations_DELETE` será alterado, obter seu OK explícito e confirmação do Higor antes do push real.
5. Após publicar com autorização, executar os testes manuais de duas contas participantes e uma terceira conta não participante definidos em `tasks.md`, incluindo autorização, privacidade, limites, status e exclusão.
6. Atualizar o guia do colaborador com o contrato e as precauções do backend.

## Perguntas em aberto

Nenhuma decisão de produto está pendente. Os limites de paginação e a necessidade de uma terceira conta de teste foram definidos durante a exploração.
