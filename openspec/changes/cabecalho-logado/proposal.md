# Proposal

## Why

Depois do login ou cadastro, a home continua mostrando apenas o cabeçalho de visitante, sem identificar a conta nem oferecer saída da sessão. Esta mudança aproveita o token transitório já mantido pelo Reflex para exibir o primeiro nome da pessoa e permitir logout, sem tornar a home privada nem persistir a sessão.

## What Changes

- Consultar `GET auth/me` com o token atual e manter no estado somente o primeiro nome para exibição.
- Alternar o cabeçalho da home entre o estado visitante (“Entrar”) e o estado autenticado (“Olá, <primeiro nome>” e “Sair”), mantendo “Quero Doar”.
- Ao sair, limpar o token e o nome do estado; se o Xano rejeitar o token, tratar a sessão como deslogada.
- Em falhas de consulta que não sejam rejeição do token, manter a home funcional e exibir “Minha conta”.
- Preservar o carregamento independente das doações recentes e da contagem, sem persistir a sessão.

## Capabilities

### New Capabilities

### Modified Capabilities

- `user-account`: acrescentar a identidade e a saída da sessão no cabeçalho da home.

## Impact

- Frontend Reflex: estado compartilhado em `doafacil/login.py` e cabeçalho em `doafacil/doafacil.py`.
- Backend Xano existente: consumo de `GET auth/me` no grupo Authentication, sem alterações no workspace.
- Configuração: reutilização de `XANO_AUTH_API_URL` já usada pelo login e cadastro.
- Verificação: testes unittest com transporte HTTP simulado e inspeção estrutural do cabeçalho; compilação Reflex.

Fora do escopo: persistência de sessão, páginas protegidas, alterações no Xano e novos dados pessoais além do primeiro nome no estado de exibição.
