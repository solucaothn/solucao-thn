## Why

A plataforma precisa de um catálogo confiável para que usuários autenticados
publiquem itens para doação e acompanhem o ciclo de disponibilidade. Hoje não
há um recurso de domínio que registre doações, organize-as por categoria ou
permita que o dono mantenha seus anúncios.

## What Changes

- Criar o recurso de doação, associado ao usuário autenticado que é seu dono.
- Permitir cadastro, edição e exclusão de doações somente pelo proprietário.
- Associar cada doação a uma categoria válida.
- Disponibilizar categorias previamente gerenciadas por um operador humano
  diretamente no workspace Xano, sem endpoint administrativo nesta change.
- Controlar os estados `disponível`, `reservada` e `concluída`.
- Disponibilizar listagem básica de doações.
- Criar a interface Reflex para os fluxos do catálogo, consumindo APIs do Xano.
- Aplicar persistência, regras de negócio e autorização exclusivamente no Xano.

Fora do escopo:

- Reserva ou conclusão por outro usuário.
- Busca avançada, filtros geográficos, paginação elaborada ou ordenação customizada.
- Upload de imagens.
- Mensagens, avaliações, doações recorrentes ou notificações.
- Cadastro, edição e exclusão de categorias via API; categorias serão mantidas
  diretamente no Xano por um operador humano nesta fase.

## Capabilities

### New Capabilities

- `catalogo-doacoes`: cadastro, manutenção, categorização, status e listagem
  básica de doações do usuário.

### Modified Capabilities

- Nenhuma.

## Impact

- Workspace Xano: novas tabelas, endpoints de doações e consulta de categorias.
- Frontend Reflex: telas e estado para criar, editar, excluir e listar
  doações, além de selecionar categorias e atualizar status permitido.
- Integração autenticada existente: o token e a identidade validados pelo Xano
  serão pré-requisitos para operações do dono.
- Nenhuma alteração planejada na capability `identidade-autorizacao`; esta
  change não introduz papéis administrativos.
