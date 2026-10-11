# Design

## Context

Ver proposta em `proposal.md` e contratos em `specs/user-account/spec.md` e `specs/event-logging/spec.md`.

O Xano já possui endpoints de cadastro, login, sessão autenticada e perfil. O usuário tem cidade e estado obrigatórios. A emissão de token está configurada para 86.400 segundos. A função de log atualmente aceita JSON livre e o grava em `event_log.metadata`; chamadas de cadastro, login, sessão e recuperação de senha enviam e-mail ou o objeto de usuário. O endpoint de histórico retorna apenas identificador, data, ator e ação, sem expor `metadata`.

## Goals / Non-Goals

**Goals:**
- Preservar os contratos atuais de autenticação e perfil enquanto os formaliza.
- Impedir que novos eventos gravados pelo logger carreguem metadados pessoais ou segredos.
- Manter a associação do ator no campo próprio do evento.

**Non-Goals:**
- Excluir ou alterar registros de eventos já gravados.
- Alterar os endpoints públicos, o prazo do token ou os campos do perfil.
- Criar interface Reflex ou tratar recuperação de senha além da remoção de seus metadados pessoais nos logs.

## Decisions

1. **Tratar os endpoints existentes como contrato-base.** Cadastro exige nome, e-mail, senha, cidade e estado; login emite token de 24 horas; sessão e perfil permanecem protegidos por autenticação. Isso formaliza comportamento observado sem introduzir mudanças de produto.

2. **Remover o JSON livre da interface da função de gravação de eventos.** As chamadas existentes não precisam de contexto adicional: o identificador do ator fica em `event_log.user_id`, a ação identifica o evento e a tabela já registra a data. Remover a entrada genérica de metadados evita depender de cada chamador para filtrar PII. A alternativa de manter o parâmetro e apenas sanitizar cada chamada foi descartada por permitir que uma chamada futura volte a gravar dados pessoais.

3. **Atualizar todos os chamadores locais do logger.** Isso inclui cadastro, login, consulta de sessão, login por link mágico, redefinição de senha e envio de e-mail de boas-vindas. O envio de boas-vindas atualmente passa metadados vazios; será ajustado apenas para acompanhar a assinatura interna do logger.

4. **Preservar a coluna histórica `event_log.metadata`.** O logger deixará de gravar metadados novos, mas a coluna não será removida e os registros existentes não serão apagados. Isso evita uma migração destrutiva e mantém a mudança limitada à gravação futura.

## Risks / Trade-offs

- Registros históricos podem continuar contendo e-mails ou outros dados pessoais → a mudança impede novas gravações, mas não faz expurgo; avaliar essa necessidade separadamente, com acesso ao ambiente Xano e política de retenção definida.
- O workspace Xano compartilhado pode ter chamadas que não aparecem na cópia local → antes de implementar, sincronizar o workspace e revisar as diferenças e todos os usos reais do logger.
- A remoção do parâmetro interno pode afetar chamadores não encontrados localmente → conferir todos os usos após o pull e validar o XanoScript antes do push.

## Migration Plan

1. Sincronizar o workspace Xano e reconciliar alterações compartilhadas antes de editar.
2. Atualizar a assinatura interna do logger e todos os chamadores para gravar eventos sem metadados.
3. Validar os arquivos XanoScript e executar `xano workspace push -d ./xano --dry-run` para revisar o plano antes de qualquer publicação.
4. Implantar logger e chamadores juntos. Em rollback, restaurar a assinatura e os chamadores como um conjunto; isso não exige alteração nem remoção da coluna ou dos registros existentes.