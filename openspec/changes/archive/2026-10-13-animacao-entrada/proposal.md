# Proposal

## Why

As telas de login e cadastro aparecem de forma abrupta ao serem abertas. Uma entrada curta e suave para os cartões pode tornar a navegação mais agradável sem alterar o conteúdo, o layout ou o comportamento dos formulários.

## What Changes

- Adicionar uma animação CSS de entrada, executada uma vez, aos cartões de login e cadastro.
- Combinar opacidade crescente com uma subida leve, com duração aproximada de 0,3 segundo e aceleração ease-out.
- Desativar completamente a animação quando a pessoa prefere movimento reduzido.
- Registrar no README do design que a animação é um acréscimo ausente do Figma, apenas nas descrições de login e cadastro.

## Capabilities

### New Capabilities

<!-- Nenhuma nova capability. -->

### Modified Capabilities

- `user-account`: especificar a animação de entrada nos cartões das telas públicas de login e cadastro, incluindo movimento reduzido.

## Impact

- Frontend Reflex: estilos globais em `doafacil/doafacil.py` e cartões em `doafacil/login.py` e `doafacil/cadastro.py`.
- Testes unittest dos componentes e estilos das telas de autenticação.
- `docs/design/README.md`, seções 04 e 05.
- Sem mudanças em APIs, Xano, dependências ou lógica de autenticação/cadastro.
