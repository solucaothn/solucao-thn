# Design

## Context

Consulte [proposal.md](./proposal.md) para a motivação e a [spec delta](./specs/password-recovery/spec.md) para o contrato observável. O grupo `authentication` já contém endpoints legados por link mágico; a tabela `user` mantém `password_reset`. Ambos ficam fora das alterações desta change. O padrão de eventos existente aceita apenas `user_id` e `action`.

## Goals / Non-Goals

**Goals:**
- Definir separação entre solicitação, verificação e confirmação de senha.
- Garantir respostas públicas indistinguíveis nos casos de solicitação e verificação previstos na spec.
- Manter a alteração de dados aditiva e compatível com o login existente.

**Non-Goals:**
- Implementar telas, rotas ou lógica no Reflex.
- Migrar, remover ou reaproveitar o fluxo legado por link mágico.
- Alterar a tabela `user`, seus campos ou as variáveis de ambiente do workspace.

## Decisions

### APIs públicas e respostas

- Criar `POST reset/request_code` com entrada `email`; retornar uma única resposta neutra, com status e corpo idênticos para conta existente, inexistente, limitada ou falha de entrega.
- Criar `POST reset/verify_code` com `email` e `code`; o sucesso devolve somente o token temporário necessário para a próxima etapa. Todas as falhas de verificação usam a mesma resposta genérica e o mesmo status.
- Criar `POST reset/confirm_password` com `reset_token`, `password` e `password_confirmation`. Validar a regra da senha no backend, consumir o token uma única vez e não emitir credencial de sessão.
- Não incluir no contrato valores de erro do provedor, e-mail, código ou token além do token de redefinição no sucesso da verificação.

Alternativa considerada: manter um único endpoint ou retornar erros específicos por etapa. Foram rejeitados por dificultarem o uso único do código e poderem revelar a existência da conta.

### Persistência e credenciais temporárias

- Adicionar tabela própria, por exemplo `password_reset_code`, com relação a `user`, hash do código, expiração, tentativas, estado de uso, hash do token de redefinição, expiração/uso do token e timestamps de emissão necessários para os limites. Não gravar endereço de e-mail nessa tabela quando a relação com `user` for suficiente.
- Usar registros por emissão (ou mecanismo equivalente que preserve histórico de uma hora) para aplicar a janela móvel de cinco envios; um único `last_sent_at` não basta para esse limite. Nova emissão invalida códigos pendentes anteriores da conta.
- Usar campos do tipo `password` com `security.check_password` para comparar códigos de baixa entropia, de modo que o Xano armazene hashes adaptativos. Para o token aleatório de 32 bytes, armazenar SHA-256 hexadecimal: sua entropia alta permite busca indexada determinística sem guardar o token em claro. O SHA-256 não é adequado para o código numérico.
- A documentação XanoScript consultada descreve `security.random_number`, `security.random_bytes` e `db.transaction`, mas não declara explicitamente garantias criptográficas do gerador nem o nível de isolamento/serialização concorrente. Por instrução do grupo, a implementação usa `security.random_number` para código entre 100000 e 999999 e `security.random_bytes` com 32 bytes para token; isso é a melhor fonte disponível documentada, mas sua qualidade criptográfica não pôde ser confirmada independentemente. Esse é um risco residual: antes da publicação, confirmar com o Xano/provedor a implementação criptográfica e testar limites/uso concorrente.
- Atualizações de estado e consumo do token são agrupados em `db.transaction`, cuja documentação declara execução atômica. Ainda não foi possível comprovar isolamento contra duas transações concorrentes lendo o mesmo estado; tentativa, limite de envio e token de uso único continuam com risco residual até teste concorrente no Xano. Não tratar transação como prova de serialização.

Alternativa considerada: guardar o código em texto ou usar hash rápido sem chave. Rejeitada por expor códigos/tokens em repouso ou permitir enumeração offline barata do espaço de seis dígitos.

### Nomes e contratos Xano

- Tabela nova: `password_reset_code`, com uma linha por usuário, hash de senha do código, validade, tentativas, estado de uso, hash SHA-256 do reset token, validade/uso do token e cinco timestamps de envio para aplicar a janela horária.
- Função interna: `Password Recovery/send_recovery_code`, recebendo somente e-mail da conta, código e validade; chama SendGrid e devolve apenas um indicador interno de sucesso, sem propagar corpo do provedor.
- APIs públicas: `POST reset/request_code` recebe `email` e responde sempre `{success: true}`; `POST reset/verify_code` recebe `email` e `code`, devolve `reset_token` apenas no sucesso e uma resposta genérica idêntica nas falhas; `POST reset/confirm_password` recebe `reset_token`, `password` e `password_confirmation`, não cria sessão e não devolve credencial.
- O endpoint de solicitação captura falha da função de e-mail e mantém a resposta neutra. Registros pelo `log_event` recebem somente `user_id` e ação.

### Limites e envio de e-mail

- Aplicar no servidor o intervalo mínimo de 30 segundos e o máximo de cinco envios por hora por conta. Um limite adicional por IP é desejável se puder ser implementado com recursos já disponíveis, sem depender do cronômetro da interface; não substituir os limites por conta.
- Enviar por função interna, com `api.request` para `POST https://api.sendgrid.com/v3/mail/send`, usando exclusivamente `$env.SENDGRID_API_KEY` e `$env.SENDGRID_FROM_EMAIL`. Não colocar valores dessas variáveis em arquivos, respostas, logs ou exemplos.
- Montar assunto e texto fixos em português; enviar ao e-mail recuperado da conta e incluir apenas código e validade, sem links.
- Tratar erro HTTP e falha de rede sem alterar a resposta neutra de `request_code`. Registrar a falha, quando possível, somente como ação segura e `user_id` por `log_event`; nunca registrar corpo da chamada/resposta, e-mail, código, token, hash ou chave.

Alternativa considerada: endpoint público para disparo de e-mail ou função utilitária com configuração/remetente em texto no código. Rejeitada por ampliar a superfície pública e expor configuração.

### Endpoints legados

Esta change não altera os endpoints `request_reset_link`, `magic_link_login` ou `update_password`, nem a função `generate_magic_link`; `user.password_reset` permanece como está e não participa do novo fluxo. A decisão de mantê-los ativos ou desativá-los pertence ao grupo e fica pendente para antes da publicação do novo fluxo. Recomendação: após validar o fluxo por código, avaliar a desativação dos endpoints de link mágico que possam contornar a política nova, em change aprovada separadamente, sem removê-los silenciosamente nesta etapa.

O cadastro atual revela e-mail já cadastrado; essa decisão de UX permanece fora do escopo desta change e não deve ser confundida com as respostas neutras da recuperação.

## Risks / Trade-offs

- [Hash rápido de código de baixa entropia permite busca offline] → Usar hash adaptativo/seguro no Xano e validar seu comportamento antes da implementação.
- [Concorrência pode ultrapassar limites ou consumir token mais de uma vez] → Exigir mecanismo atômico/transacional e testar solicitações concorrentes.
- [SendGrid indisponível impede entrega, mas a resposta deve continuar neutra] → Registrar apenas evento seguro e verificar recebimento real em teste manual.
- [Falha também na invalidação do código após erro de entrega] → Tentar marcar o código como usado sem alterar a resposta pública; se a gravação de invalidação falhar, o código permanece limitado a cinco tentativas e expira em 10 minutos. Essa condição ainda precisa de teste no Xano.
- [Endpoints legados podem continuar permitindo fluxos menos seguros] → Não alterá-los sem decisão do grupo; decidir seu estado antes de disponibilizar o fluxo novo.
- [Múltiplos registros de emissão preservam dados de controle] → Reter apenas o necessário para limites e remover registros expirados conforme mecanismo de limpeza validado no Xano.

## Migration Plan

1. Antes de qualquer edição futura no workspace, executar `xano workspace pull -d ./xano` e confirmar que a árvore commitada está sincronizada; não sobrescrever alterações compartilhadas.
2. Implementar somente adições, consultar e validar a sintaxe no Xano Developer MCP e executar os testes/manuais listados em `tasks.md`.
3. Executar `xano workspace push -d ./xano --dry-run`, revisar integralmente o resultado e avisar o grupo antes de qualquer push real. Push real não está autorizado por esta proposta.
4. Se a validação falhar, não publicar os novos endpoints; como a mudança é aditiva, desativar os novos endpoints e retirar somente os artefatos aditivos em uma reversão revisada, preservando usuários, senhas e endpoints legados.
