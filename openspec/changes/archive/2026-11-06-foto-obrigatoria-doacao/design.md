# Design

## Contexto

Consulte a [proposta](./proposal.md) para a motivação e a delta de [donation-creation](./specs/donation-creation/spec.md) para o contrato atualizado. Hoje o wizard exige foto, mas o endpoint Xano aceita `photos` ausente ou vazio e pode persistir uma doação com capa nula. O frontend converte respostas HTTP de erro da publicação em uma falha genérica. A coluna `donation_photo.photo` está atualmente opcional.

## Objetivos / Não objetivos

**Objetivos:**

- Fazer a exigência de uma a cinco fotos valer tanto no wizard quanto no endpoint.
- Rejeitar uma solicitação sem foto antes de qualquer upload ou gravação.
- Apresentar no wizard a mensagem já usada para a etapa 3 e preservar os dados preenchidos.
- Evitar que a alteração condicional do schema da tabela torne inválidos registros existentes.

**Não objetivos:**

- Alterar doações antigas com `donation.photo` vazio.
- Alterar limites ou formatos de imagem, fluxo de publicação com fotos ou outras regras do endpoint.
- Alterar consumidores externos sem coordenação com o grupo.

## Decisões

### Validar a lista de fotos antes de efeitos

O endpoint rejeitará `photos` ausente, nulo ou com zero itens na validação inicial, antes de `storage.create_image` e de qualquer `db.add`. O limite já existente de cinco fotos permanece. A alternativa de deixar a falha para o banco ou para o processamento do arquivo foi descartada porque poderia permitir efeitos parciais, registros sem imagem ou arquivos sem uma doação associada.

O erro será `inputerror` (HTTP 400) com “Adicione pelo menos uma foto para continuar.”, conforme a decisão do grupo. A resposta precisa ser observada no Xano real para confirmar o formato efetivo do corpo de erro.

### Mapear a rejeição específica no frontend

O helper de publicação atualmente transforma respostas HTTP de erro em uma exceção genérica. O frontend deverá reconhecer a resposta 400 correspondente à falta de fotos e mostrá-la como erro do wizard, sem limpar campos, seleção ou estado de publicação. Outras falhas continuam usando a mensagem genérica existente. Os testes unitários usarão respostas simuladas para ambos os caminhos; não comprovam o contrato real do Xano.

### Tornar `donation_photo.photo` obrigatório somente após auditoria

Antes de qualquer alteração Xano, uma tarefa manual verifica no painel se há linhas `donation_photo` com `photo` vazio e se há doações com `donation.photo` vazio. Se não houver linhas de `donation_photo` com foto vazia, a coluna poderá voltar a ser obrigatória (`image photo`). Se houver alguma, a coluna permanece opcional nesta change; não apagar nem preencher dados para forçar a migração.

A auditoria de `donation.photo` serve para registrar o estado das capas existentes. Esses dados antigos não serão alterados, independentemente do resultado. A validação do endpoint é necessária em qualquer dos resultados da auditoria; a exigência da coluna é uma proteção adicional para novas linhas quando compatível com os dados existentes.

### Publicação compartilhada

Como o endpoint foi criado por outro integrante e pode ter consumidores além do site, a revisão da mudança deve incluir aviso e OK explícito do grupo antes do push real. O dry-run deverá conter somente mudanças em `publish_POST` e, se autorizada pela auditoria, `donation_photo`; diante de qualquer outro arquivo ou objeto alterado, interromper e avisar o grupo.

## Riscos / Compensações

- **Consumidores existentes enviam publicação sem foto** → identificar e avisar os consumidores conhecidos; obter o OK do grupo antes de alterar o contrato.
- **Há linhas com foto vazia na tabela de fotos** → manter `donation_photo.photo` opcional nesta change; não excluir nem corrigir dados antigos automaticamente.
- **Formato real do erro 400 difere do esperado** → confirmar a resposta no Xano após a publicação e ajustar o mapeamento somente com evidência do contrato real.
- **Mock aceita um comportamento que o Xano real não implementa** → separar os testes de frontend com respostas simuladas da validação pós-publicação no endpoint real.
- **Dry-run inclui alterações alheias** → não publicar; parar e avisar o grupo se aparecer qualquer alteração além do endpoint de publicação e, condicionalmente, da tabela de fotos.

## Plano de migração

1. Atualizar o tratamento frontend e os testes com respostas simuladas, substituindo o teste que atualmente considera válida uma publicação sem fotos.
2. Fazer a auditoria manual no painel de `donation_photo.photo` vazio e `donation.photo` vazio; registrar o resultado para decidir se a coluna da tabela pode ser tornada obrigatória.
3. Antes do pull Xano, mostrar o status do Git e aguardar confirmação explícita do Higor; preservar as alterações preexistentes.
4. Consultar a documentação e validar XanoScript no Xano Developer MCP antes de editar. Alterar somente `publish_POST`; alterar `donation_photo` apenas se a auditoria permitir.
5. Executar e revisar o dry-run. Se houver alterações além de `publish_POST` e, condicionalmente, `donation_photo`, parar e avisar o grupo.
6. Avisar o grupo, obter seu OK para a mudança contratual e confirmação explícita do Higor antes do push real. Publicar somente os arquivos aprovados.
7. Após o push, chamar diretamente o endpoint sem fotos e confirmar HTTP 400, a mensagem definida e ausência de doação, linha de foto e arquivo órfão; publicar pelo site com foto e confirmar sucesso sem a mensagem de falta de foto.

## Perguntas em aberto

Nenhuma decisão de produto está pendente. A condição para alterar a coluna `donation_photo.photo` será resolvida pela auditoria manual antes da edição.
