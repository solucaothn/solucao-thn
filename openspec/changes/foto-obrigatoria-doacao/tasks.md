# Tarefas

## 1. Frontend e testes

- [x] 1.1 Tratar a resposta Xano de falta de fotos em `doafacil/cadastro_doacao.py`, exibindo “Adicione pelo menos uma foto para continuar.” sem limpar os dados do formulário; verificar o comportamento com teste focado.
- [x] 1.2 Atualizar `tests/test_donation_creation.py` para que publicação sem fotos não seja considerada sucesso e cobrir a resposta simulada de falta de fotos, a mensagem e a preservação dos dados; executar `python -m unittest tests.test_donation_creation`.

## 2. Auditoria prévia

- [ ] 2.1 (manual) Auditar no painel do Xano se existem linhas `donation_photo` com `photo` vazio e doações com `donation.photo` vazio; registrar o resultado e confirmar se `donation_photo.photo` pode se tornar obrigatório. Não alterar nem excluir dados durante a auditoria.

## 3. Xano e publicação

- [ ] 3.1 (manual) Mostrar `git status --short --branch` e aguardar confirmação explícita do Higor antes de executar `xano workspace pull -d ./xano`; após o pull, mostrar `git status` e `git diff --stat` em `xano/`, preservando todas as mudanças existentes.
- [ ] 3.2 Consultar a documentação do Xano Developer MCP antes de editar XanoScript; validar cada arquivo alterado no MCP e ajustar `publish_POST` para rejeitar `photos` ausente, nulo ou vazio antes de upload ou `db.add`, mantendo o limite de cinco fotos. Alterar `donation_photo.photo` para obrigatório somente se a auditoria confirmar que não há linhas vazias; conferir os arquivos e a validação do MCP.
- [ ] 3.3 Executar e revisar `xano workspace push -d ./xano --dry-run`; verificar que as alterações se limitam a `publish_POST` e, se autorizada pela auditoria, `donation_photo`. Se houver qualquer alteração adicional, parar e avisar o grupo sem fazer push.
- [ ] 3.4 (manual) Avisar o grupo de que o contrato de `POST /catalog/donations/publish` está mudando e obter o OK explícito do grupo antes da publicação real; registrar a autorização.
- [ ] 3.5 (manual) Obter a confirmação explícita do Higor para o push real depois da revisão do dry-run e do OK do grupo; sem as duas autorizações, não publicar.
- [ ] 3.6 Executar `xano workspace push -d ./xano` somente após as autorizações; conferir o resultado e que apenas os arquivos aprovados foram enviados.

## 4. Verificação manual pós-publicação

- [ ] 4.1 (manual) Chamar diretamente o endpoint sem fotos e verificar HTTP 400, erro `inputerror`, mensagem “Adicione pelo menos uma foto para continuar.” e ausência de doação, linha de foto e arquivo órfão.
- [ ] 4.2 (manual) Publicar uma doação com foto pelo site e verificar que a publicação tem sucesso e que a mensagem de falta de foto não aparece.

## 5. Documentação

- [ ] 5.1 Atualizar `docs/guia-do-colaborador.md` com a validação de fotos obrigatória no backend, resposta de erro, tratamento no site, auditoria condicional da tabela e fluxo de autorização/publicação; conferir que o guia corresponde à change.
