# Proposal

## Why

O backend Xano já oferece cadastro, login, consulta da sessão autenticada e leitura/atualização do perfil, mas esse comportamento ainda não está formalizado em specs. Além disso, chamadas de autenticação enviam e-mail e outros dados pessoais nos metadados do log de eventos, contrariando as regras de privacidade do projeto.

## What Changes

- Formalizar os contratos existentes de cadastro, login, sessão e perfil, incluindo cidade e estado no perfil e o token de autenticação emitido pelo Xano.
- Definir que metadados de eventos de conta não armazenam e-mail, nome, localização, credenciais, tokens ou outros dados pessoais.
- Remover a entrada de metadados livres do logger e atualizar todas as chamadas existentes; manter a associação do ator no campo `user_id` próprio do evento.
- Preservar os fluxos de autenticação observados. Não incluir expurgo de registros de log históricos nesta mudança.

## Capabilities

### New Capabilities

- `user-account`: cadastro, autenticação, sessão e perfil do usuário.
- `event-logging`: registro de eventos sem dados pessoais nos metadados.

### Modified Capabilities

Nenhuma. O projeto ainda não possui specs consolidadas.

## Impact

- Endpoints Xano de cadastro, login, sessão e perfil; chamadas do logger nos fluxos de autenticação e recuperação de senha.
- `xano/function/quick_start/log_event.xs` e todos os seus chamadores locais; a coluna histórica `event_log.metadata` será preservada.
- Não inclui frontend Reflex, administração, moderação ou outros fluxos de domínio.