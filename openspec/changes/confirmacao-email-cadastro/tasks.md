# Tarefas

## 1. Frontend Reflex e testes relacionados

- [x] 1.1 Atualizar o início do cadastro para tratar a resposta sem token, manter e-mail e senha somente no estado transitório Reflex após a resposta e navegar para `/verificar-email`; atualizar `tests/test_signup.py` para remover as expectativas de criação imediata, token e resposta distinguível de e-mail já cadastrado. Verificar com `python -m unittest discover -s tests -p test_signup.py`.
- [x] 1.2 Adaptar a tela compartilhada `/verificar-email` para distinguir cadastro de recuperação, usar `signup_resend` e `signup_verify` no cadastro, enviar e-mail, código e senha na verificação, e apagar a senha ao concluir ou ao acionar “Usar outro e-mail”; acrescentar testes para código de seis dígitos, payloads, neutralidade simulada, reenvio antes/depois de 30 segundos, falha de rede e navegação. Verificar com os testes de cadastro e recuperação.
- [x] 1.3 Após a verificação bem-sucedida, limpar os dados transitórios e redirecionar ao login com aviso verde de cadastro confirmado, sem definir token; acrescentar testes de estado, ausência de sessão, navegação e limpeza do aviso ao digitar, tentar entrar, sair ou recarregar.
- [x] 1.4 Executar `python -m unittest discover -s tests` e confirmar que os testes de recuperação de senha continuam passando sem mudanças em seus contratos. Os testes com `httpx.MockTransport` validam o comportamento do frontend e respostas simuladas, não comprovam o contrato real nem os limites aplicados pelo Xano.

## 2. Xano

- [ ] 2.1 (manual) Conferir e mostrar `git status --short --branch`, registrando as alterações preexistentes em `xano/`; pedir confirmação explícita do Higor e só então executar `xano workspace pull -d ./xano`. Depois do pull, mostrar novamente o status e as diferenças em `xano/`. O Copilot não marca esta tarefa.
- [ ] 2.2 Consultar o Xano Developer MCP antes de escrever XanoScript; implementar a tabela única de cadastros pendentes, alterar somente `auth/signup`, criar `auth/signup_resend`, `auth/signup_verify` e a função SendGrid própria; tratar uma chamada inicial repetida atualizando dados e enviando novo código apenas dentro dos limites, sem resetar histórico quando bloqueada; depois do pull, conferir o `git diff` de `signup_POST.xs` e registrar se há apenas quebra de linha ou mudança real; incluir esse arquivo e os novos arquivos Xano no commit da change, sem adicionar nenhum dos outros 18 arquivos modificados de `xano/` ao `git add`; fazer `signup_verify` criar a conta copiando do `signup_POST.xs` atual todos os campos e regras da conta, incluindo `role` e e-mail em minúsculas; validar os arquivos `.xs` no MCP e conferir que não foram alterados `send_welcome_email_POST`, a recuperação de senha ou tabelas/endpoints de doação.
- [ ] 2.3 (manual) Executar `xano workspace push -d ./xano --dry-run`, revisar e mostrar a saída completa; se houver qualquer alteração em `donation_photo` ou `password_reset_code`, parar sem prosseguir e avisar o grupo. O Copilot não marca esta tarefa.
- [ ] 2.4 (manual) Apresentar ao grupo o dry-run revisado, avisar que `auth/signup` muda o contrato usado por outros consumidores e obter o OK do grupo antes de publicar. O Copilot não marca esta tarefa.
- [ ] 2.5 (manual) Imediatamente antes do push real, obter confirmação explícita do Higor e publicar somente as alterações aprovadas desta change. O Copilot não marca esta tarefa.

## 3. Documentação

- [ ] 3.1 Atualizar a seção da tela 12 em `docs/design/README.md` para documentar seu uso também na confirmação de cadastro, textos distintos por fluxo e acréscimos que não estão no Figma; verificar que a descrição de recuperação continua correta.
- [ ] 3.2 Atualizar `docs/guia-do-colaborador.md` com o fluxo de confirmação, os novos endpoints, a senha não persistida, os limites e a sequência de segurança para alterações no workspace Xano; conferir que o guia não contradiz os artifacts.

## 4. Verificação manual pós-publicação

- [ ] 4.1 (manual) Após o push, testar no Xano o início, reenvio e verificação, incluindo conta criada somente após código válido, nenhuma sessão emitida, resposta neutra para e-mail já cadastrado e código inválido, cinco tentativas, validade de 10 minutos, cooldown de 30 segundos, cinco envios por hora e expiração de 24 horas com remoção somente no acesso. O Copilot não marca esta tarefa.
- [ ] 4.2 (manual) Depois de um teste real de início, reenvio e verificação, conferir o histórico de execução do Xano para garantir que senha e código não aparecem; se algum deles aparecer, interromper a publicação/uso do fluxo e avisar o grupo. O Copilot não marca esta tarefa.
- [ ] 4.3 (manual) No navegador, testar confirmação bem-sucedida sem criar sessão, “Usar outro e-mail” limpando a senha e voltando ao cadastro, aviso verde no login e regressão completa da recuperação de senha. O Copilot não marca esta tarefa.
