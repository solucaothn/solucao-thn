# Tasks

## 1. Preparação e modelo de dados

- [x] 1.1 Pull de 32 documentos já executado e commitado pelo usuário; confirmado pelo usuário e pelo `git status`. Não repetir o pull nem alterar/incluir os oito arquivos Xano existentes que aparecem modificados somente por LF/CRLF.
- [x] 1.2 Consultar no Xano Developer MCP e validar a sintaxe de hash adaptativo/`security.check_password`, geração aleatória e operação transacional; usar os recursos disponíveis, registrar limitações de garantias criptográficas/concorrência no design e validar os novos arquivos no workspace sem interromper por ausência de garantia explícita.
- [x] 1.3 Criar a tabela aditiva de recuperação, sem alterar ou utilizar `user.password_reset`, e validar todos os arquivos `.xs` novos/alterados com o Xano Developer MCP e o validador XanoScript.
- [x] 1.4 Documentar na change os nomes, entradas, respostas neutras e regras dos três endpoints e da função interna; verificar que a documentação corresponde à spec `password-recovery` e não contém valores de ambiente.

## 2. Solicitação e entrega do código

- [x] 2.1 Implementar a função interna SendGrid com `api.request`, usando somente `$env.SENDGRID_API_KEY` e `$env.SENDGRID_FROM_EMAIL`; validar sintaxe e conferir no código que destinatário, assunto e texto seguem a spec sem link nem registro de dados sensíveis.
- [ ] 2.2 Implementar `POST reset/request_code`, emissão de seis dígitos, validade, invalidação de emissão anterior e limites por conta de 30 segundos/cinco por hora; validar sintaxe e confirmar por teste que status e corpo são idênticos para conta elegível, inexistente, limitada e falha simulada de e-mail. Implementação e validação de sintaxe concluídas; faltam testes de comportamento no Xano.
- [ ] 2.3 Testar que uma solicitação elegível envia a mensagem apenas para o e-mail da conta e que erros de entrega não alteram a resposta pública; verificar no painel/logs que não há e-mail, código, token, hash ou chave nos registros.

## 3. Verificação e troca de senha

- [ ] 3.1 Implementar `POST reset/verify_code`, hash do código, expiração, contagem de tentativas e invalidação ao quinto erro; validar sintaxe e testar código correto, código errado e resposta idêntica para e-mail inexistente, expirado, usado ou bloqueado. Implementação e validação de sintaxe concluídas; faltam testes de comportamento no Xano.
- [ ] 3.2 Implementar `POST reset/confirm_password`, hash e consumo único do token, validação da regra de senha/confirmação, invalidação dos códigos pendentes e ausência de token de sessão; validar sintaxe e testar token expirado/usado, senha inválida, confirmação diferente e sucesso. Implementação e validação de sintaxe concluídas; faltam testes de comportamento no Xano.
- [ ] 3.3 Verificar a resistência a concorrência nos incrementos de tentativas, limites de emissão e consumo do token. Nota: nesta execução não há ambiente para teste concorrente; os trechos críticos serão envolvidos em transações Xano, mas falta comprovar isolamento/atomicidade sob concorrência com testes no Xano.

## 4. Verificação integrada e sincronização

- [ ] 4.1 No painel do Xano, testar e registrar os resultados de código correto, código incorreto cinco vezes, código expirado, reenvio antes de 30 segundos e limite de cinco envios por hora.
- [ ] 4.2 No painel do Xano, comparar status e corpo para e-mail inexistente e existente, confirmar recebimento real do e-mail e testar token usado/expirado, senha fraca, confirmação diferente e conclusão sem emissão de sessão; inspecionar logs sem expor valores sensíveis.
- [x] 4.3 Executar somente `xano workspace push -d ./xano --dry-run`, revisar e apresentar a saída integral; não executar push real.
- [ ] 4.4 Validar a change com `openspec validate recuperacao-senha-api --type change` e, após implementação e aprovação manual, arquivar/sincronizar a nova capability para `openspec/specs/password-recovery/spec.md`, verificando que os requisitos e cenários foram preservados.
