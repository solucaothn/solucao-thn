# Tarefas

## 1. Preparação do workspace compartilhado

- [x] 1.1 (manual) Mostrar `git status --short --branch` e obter confirmação explícita do Higor antes de executar `xano workspace pull -d ./xano`; após o pull, mostrar `git status` e `git diff --stat` em `xano/`, preservando todas as alterações preexistentes.

## 2. Implementação do backend Xano

- [x] 2.1 Consultar a documentação do Xano Developer MCP antes de escrever XanoScript; criar `chat_conversation` e `chat_message`, implementar os quatro endpoints autenticados da delta e alterar `donations_DELETE` para exclusão atômica; validar no MCP cada arquivo `.xs` criado ou alterado e verificar que os GUIDs existentes foram preservados.
- [x] 2.2 Validar no Xano Developer MCP a autorização por participante, a criação concorrente idempotente, as respostas 401/404/400/429, a paginação e a contagem de mensagens da pessoa nos últimos 60 segundos antes da gravação. Confirmar que o limite é de melhor esforço, sem isolamento serializável, aceitando excedente de uma ou duas mensagens sob concorrência. Verificar os testes automatizados Xano disponíveis sem publicar alterações.

## 3. Revisão do dry-run

- [x] 3.1 (manual) Executar e revisar integralmente `xano workspace push -d ./xano --dry-run`; confirmar que aparecem somente as duas tabelas novas, os quatro endpoints novos e a alteração em `donations_DELETE`. Se houver qualquer outra alteração, parar e avisar o grupo sem fazer o push real.

## 4. Aprovação do grupo

- [x] 4.1 (manual) Avisar o grupo de que `DELETE /catalog/donations` passará a remover mensagens e conversas associadas, apresentar o dry-run revisado e obter o OK explícito do grupo antes do push real; registrar a autorização.

## 5. Publicação no Xano

- [x] 5.1 (manual) Obter a confirmação explícita do Higor para o push real depois da revisão do dry-run e do OK do grupo; executar `xano workspace push -d ./xano` somente após as duas autorizações e conferir que somente os objetos aprovados foram enviados.

## 6. Verificação manual com contas de teste

- [x] 6.1 (manual) Com uma conta dona, uma conta interessada e uma terceira conta não participante, verificar início de conversa, repetição retornando a mesma conversa, isolamento e 404 genérico para pessoa não participante; confirmar que nenhuma resposta dos quatro endpoints contém e-mail ou sobrenome.
- [x] 6.2 (manual) Verificar rejeição de texto vazio e acima de 1000 caracteres, exibição literal de conteúdo parecido com HTML, limite de 10 envios em janela móvel de 60 segundos e resposta 429 sem gravar a mensagem excedente.
- [x] 6.3 (manual) Verificar que doação reservada permite envio, concluída permite somente leitura, preferência “E-mail” impede conversa nova com 404 genérico e exclusão da doação remove conversa e mensagens.
- [x] 6.4 (manual) Conferir no histórico de execução e nos eventos que somente criação nova e envio bem-sucedido geram, respectivamente, `chat_started` e `chat_message_sent`, contendo apenas usuário, ação e data, sem texto, título, ID de conversa, e-mail, nome, sobrenome ou token; confirmar que leituras não geram eventos.

## 7. Documentação

- [x] 7.1 Atualizar `docs/guia-do-colaborador.md` com tabelas, endpoints, autorização, erros genéricos, limites, privacidade, logs, exclusão junto com a doação e sequência segura de validação/publicação no Xano; conferir que a documentação não sugere implementação de interface nesta change.
