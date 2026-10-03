# Tasks

## 1. Sincronização e inventário do Xano

- [x] 1.1 Executar `xano workspace pull -d ./xano` e revisar as diferenças locais com as alterações do workspace compartilhado; concluir apenas após reconciliar os arquivos afetados sem descartar trabalho existente.
- [x] 1.2 Inventariar todas as chamadas do logger e gravações diretas em `event_log` após a sincronização; verificar que cadastro, login, sessão, recuperação de senha e boas-vindas estão cobertos.

## 2. Contratos de conta

- [ ] 2.1 Verificar cadastro válido, rejeição de e-mail duplicado e validação de senha; confirmar por chamadas de API e inspeção da configuração que o token emitido expira em 86.400 segundos.
- [ ] 2.2 Verificar login válido e inválido e consulta de sessão com token válido, ausente e expirado; confirmar respostas e campos conforme `specs/user-account/spec.md`.
- [ ] 2.3 Verificar leitura e atualização autenticadas do próprio perfil, incluindo cidade e estado, e rejeição de campos obrigatórios vazios; confirmar os campos de resposta conforme a spec.

## 3. Privacidade dos eventos

- [ ] 3.1 Remover metadados livres da função de gravação e atualizar todos os chamadores identificados; manter a coluna histórica e verificar que novos eventos preservam ator, ação e data sem metadados pessoais.
- [ ] 3.2 Validar os arquivos XanoScript alterados com o Xano Developer MCP e executar os cenários de cadastro, login, sessão, recuperação de senha e boas-vindas em ambiente de teste; inspecionar os novos registros para confirmar ausência de metadados e preservar a resposta do endpoint de histórico.

## 4. Revisão de integração

- [ ] 4.1 Executar `xano workspace push -d ./xano --dry-run` e revisar que o plano contém somente as alterações previstas, sem realizar o push.