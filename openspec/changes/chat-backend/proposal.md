# Proposta

## Por quê

O detalhe da doação já oferece um botão “Chat”, mas hoje ele informa que o recurso ainda não está disponível. O backend precisa fornecer conversas privadas e mensagens entre a pessoa que doa e uma pessoa interessada, com autorização, limites e proteção de dados aplicados no Xano antes de qualquer futura integração de interface.

## O que muda

- Criar conversas autenticadas, uma por doação e pessoa interessada, somente para doações disponíveis cuja preferência seja “Chat do DoaFácil”.
- Criar e listar mensagens de texto simples, autorizando somente os participantes e mantendo o histórico paginado.
- Listar as conversas da pessoa autenticada, sem retornar e-mail ou sobrenome.
- Limitar mensagens a 1000 caracteres e 10 envios por pessoa em qualquer janela móvel de 60 segundos.
- Permitir novos envios quando a doação estiver disponível ou reservada; doações concluídas mantêm o histórico somente para leitura.
- Remover conversas e mensagens na mesma operação que apaga a doação.
- Registrar somente os eventos `chat_started` e `chat_message_sent`, usando a função existente de log e sem conteúdo da conversa.
- Não alterar requisitos de capacidades existentes nesta change.

## Capacidades

### Novas capacidades

- `donation-chat`: conversas privadas e mensagens entre a pessoa que doa e uma pessoa interessada, com endpoints autenticados, autorização por participação, paginação, limite de envio, logs sem dados pessoais e remoção junto com a doação.

### Capacidades modificadas

Nenhuma.

## Impacto

- Xano: novas tabelas `chat_conversation` e `chat_message`.
- APIs do grupo Catalog: `POST /catalog/chat/conversations/start`, `POST /catalog/chat/messages`, `GET /catalog/chat/messages` e `GET /catalog/chat/conversations`.
- API existente: `DELETE /catalog/donations` passa a remover conversas e mensagens associadas na mesma operação.
- Logs: reutilização de `Quick Start/log_event` para registrar início de conversa e envio de mensagem.
- Documentação: atualização de `docs/guia-do-colaborador.md`.
- Não inclui interface de chat, alteração do botão no detalhe, presença online, fotos de perfil, moderação ou comunicação em tempo real.
