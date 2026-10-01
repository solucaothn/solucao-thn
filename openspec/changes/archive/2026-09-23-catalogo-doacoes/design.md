## Context

Consulte `proposal.md` para a motivação e o escopo. A capability
`identidade-autorizacao` já fornece autenticação por token no Xano e integração
do Reflex com os endpoints autenticados. O catálogo deve seguir a mesma
separação: Xano como fonte de verdade para dados, regras e autorização; Reflex
como interface.

## Goals / Non-Goals

**Goals:**

- Modelar doações, categorias e status com integridade referencial no Xano.
- Derivar o proprietário da doação a partir do token autenticado.
- Expor APIs para catálogo público, manutenção do proprietário e leitura de
  categorias.
- Manter o frontend sem decisões de segurança locais.

**Non-Goals:**

- Criar painel administrativo de categorias no Reflex.
- Implementar reserva concorrente por usuários terceiros.
- Introduzir busca avançada, imagens, mensagens ou notificações.

## Decisions

### 1. Doação como recurso próprio do usuário

A tabela de doações terá uma referência obrigatória ao usuário dono. Endpoints
de criação e manutenção usarão a identidade do token (`$auth.id`) para definir
o dono e filtrar/autorizar operações. O payload não poderá escolher livremente
o proprietário.

Alternativa descartada: aceitar `user_id` enviado pelo Reflex, pois isso
permitiria alterar ou criar registros em nome de terceiros.

### 2. Categoria como entidade independente

Categorias serão persistidas em tabela própria, com nome único e estado
gerenciável pelo backend. Doações referenciarão a categoria por identificador
válido. A exclusão de categoria usada será bloqueada para preservar a
integridade referencial; a migração de doações para outra categoria fica fora
do primeiro fluxo.

Alternativa descartada: armazenar o nome da categoria diretamente na doação,
pois isso permitiria inconsistência e duplicidade.

### 3. Status com conjunto fechado

O status será representado por enumeração restrita a `disponível`, `reservada`
e `concluída`, com valor inicial `disponível`. O Xano validará tanto o conjunto
quanto as transições permitidas antes de persistir.

Alternativa descartada: texto livre, pois dificulta listagem, validação e
evolução do ciclo de vida.

### 4. Categorias gerenciadas fora da API nesta change

Categorias serão mantidas diretamente no workspace Xano por um operador humano,
usando as ferramentas administrativas do próprio Xano. Esta change terá apenas
um endpoint de leitura para o Reflex preencher a seleção de categoria; não
criará, editará ou excluirá categorias por API e não introduzirá papéis
administrativos na identidade.

Alternativa descartada: criar endpoints administrativos agora, pois a capability
de identidade ainda não define nem implementa um papel de administrador.

### 5. Listagem com exposição mínima

A listagem retornará somente campos necessários para navegação do catálogo,
incluindo categoria, status e dados descritivos do item. Não retornará e-mail,
localização privada ou outros dados de contato do proprietário.

## Risks / Trade-offs

- **[Integridade referencial]** Categorias usadas não poderão ser excluídas →
  bloquear exclusão e retornar erro explícito.
- **[Concorrência de status]** Atualizações simultâneas podem disputar o status
  → validar transição no backend e registrar a última decisão aceita.
- **[Exposição de dados]** A listagem pode vazar dados pessoais →
  definir resposta pública mínima e testar campos retornados.
- **[Gestão manual]** Categorias dependerão de operação humana no Xano →
  documentar a rotina de manutenção e validar que doações só aceitam categorias
  existentes.

## Migration Plan

1. Criar tabelas e índices de categoria e doação no workspace Xano.
2. Publicar endpoints e validar autorização em ambiente de teste.
3. Popular categorias iniciais manualmente no workspace Xano.
4. Integrar o Reflex aos endpoints de listagem e manutenção.
5. Em caso de rollback, remover a exposição dos endpoints e preservar as
   tabelas até confirmar que não existem dependências de dados.

## Open Questions

- Nenhuma decisão adicional é necessária para iniciar a implementação desta
  change.
