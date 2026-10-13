# Tasks

## 1. Consulta autenticada da conta

- [x] 1.1 Implementar a chamada simulável a `GET auth/me` com `Authorization: Bearer`, validação da resposta e extração somente do primeiro nome; verificar com testes unittest usando HTTP mock para sucesso, token rejeitado, falha transitória e resposta inválida.
- [x] 1.2 Acrescentar ao `LoginState` o carregamento do nome e o logout, sem token não deve chamar o endpoint; verificar por testes que 401/403 limpa token e nome, falha transitória usa “Minha conta” e logout limpa ambos.

## 2. Cabeçalho autenticado

- [x] 2.1 Alternar o cabeçalho entre visitante e autenticado, mantendo “Quero Doar” e o estilo responsivo; acrescentar testes estruturais para os rótulos, controles e eventos, e atualizar somente a descrição do cabeçalho em `docs/design/README.md` com a nota de que é acréscimo ausente do Figma.

## 3. Integração e verificação

- [x] 3.1 Registrar o carregamento da conta como handler independente do carregamento público da home; verificar com testes que a página mantém os handlers e o conteúdo público mesmo quando a consulta autenticada falha.
- [x] 3.2 Executar `python -m unittest discover -s tests -v` e `.venv\Scripts\reflex.exe compile --dry`; corrigir falhas relacionadas à change.
- [ ] 3.3 Conferir manualmente em janela estreita e larga, com Xano: cabeçalho após login/cadastro, fallback “Minha conta”, rejeição de token, logout na home; depois de recarregar, a sessão da aba continua, enquanto uma aba nova ou o servidor reiniciado abrem sem sessão.
