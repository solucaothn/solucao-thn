# Proposal

## Why

As telas planejadas de recuperação usam um código de seis dígitos, mas o Xano disponível hoje implementa um fluxo legado por link mágico, sem os controles e as respostas neutras necessários. Esta mudança especifica uma API de recuperação por código, com expiração, uso único, limites de tentativas e proteção contra enumeração de contas.

## What Changes

- Criar uma capability `password-recovery` para solicitar e-mail com código, verificar o código e confirmar uma nova senha.
- Acrescentar armazenamento próprio para códigos e tokens de redefinição, sem alterar `user` nem utilizar `user.password_reset`.
- Definir envio de e-mail por função interna do Xano e registro de eventos sem dados sensíveis.
- Preservar neutras as respostas públicas de solicitação e verificação, inclusive diante de falhas no envio.
- Planejar validação da sintaxe e dos recursos de segurança do Xano antes da implementação; esta change não altera o workspace.

## Capabilities

### New Capabilities

- `password-recovery`: recuperação de senha por código de seis dígitos e token temporário de redefinição.

### Modified Capabilities

Nenhuma.

## Impact

- APIs públicas futuras no grupo `authentication/reset`: `request_code`, `verify_code` e `confirm_password`.
- Nova tabela e funções internas futuras no workspace Xano, além do envio pelo SendGrid usando as variáveis de ambiente já existentes.
- Documentação e especificações OpenSpec.
- Não altera o frontend Reflex, endpoints legados, tabela `user`, nem envia alterações ao Xano nesta etapa.
