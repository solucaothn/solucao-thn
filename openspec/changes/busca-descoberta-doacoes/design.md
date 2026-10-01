## Context

O catálogo de doações já possui uma listagem pública no Xano e um endpoint
público de leitura de categorias. Esta change adiciona descoberta sem criar
uma nova fonte de dados, sem alterar a autorização das operações do
proprietário e sem expor informações privadas.

## Goals / Non-Goals

**Goals:**

- Permitir busca por texto em título e descrição.
- Permitir filtro por uma categoria.
- Manter a consulta pública para visitantes e usuários autenticados.
- Aplicar filtros, validações e ordenação no Xano.
- Reutilizar as categorias e a resposta pública existentes.
- Atualizar a listagem do Reflex somente com a resposta do backend.

**Non-Goals:**

- Filtrar por status nesta change.
- Criar paginação, limite configurável ou busca incremental.
- Buscar por localização ou dados do proprietário.
- Criar endpoints administrativos de categoria.
- Implementar reserva, contato, mensagens ou recomendação.

## Decisions

### 1. Extender a listagem pública existente

O endpoint público de doações será ampliado com parâmetros opcionais de busca e
categoria, em vez de criar um endpoint paralelo. Sem parâmetros, seu
comportamento continuará equivalente à listagem básica atual.

Alternativa descartada: criar uma rota de busca separada, pois duplicaria
contratos e aumentaria o risco de respostas públicas divergentes.

### 2. Consulta textual no Xano

O Xano será responsável por normalizar o termo e aplicar a correspondência em
`title` e `description`. O Reflex não filtrará a lista em memória e não será
considerado fonte de verdade.

Alternativa descartada: carregar todos os registros e filtrar no cliente, pois
seria ineficiente e poderia produzir resultados inconsistentes.

### 3. Uma categoria por consulta

O contrato aceitará no máximo um `category_id` opcional. O Xano validará que a
categoria existe antes de aplicar o filtro; a ausência do parâmetro significa
todas as categorias.

Alternativa descartada: múltiplas categorias, pois não são necessárias para o
primeiro fluxo e exigiriam uma forma adicional de serialização e validação.

### 4. Todos os status e ordenação recente

A busca não adicionará filtro de status e continuará incluindo os três estados
do catálogo. O Xano ordenará por `created_at` descendente para tornar a
descoberta previsível.

Alternativa descartada: restringir implicitamente a itens disponíveis, pois a
decisão de escopo definiu que doações concluídas continuam visíveis.

### 5. Resposta pública inalterada

Os filtros não alterarão os campos retornados. A consulta continuará sem
`owner_id`, e-mail, cidade, estado ou qualquer dado de contato.

Alternativa descartada: incluir dados do proprietário para facilitar contato,
pois isso violaria a separação de segurança e o contrato público existente.

### 6. Submit explícito no Reflex

O Reflex terá um formulário de busca com texto e categoria. A requisição será
disparada no submit ou com Enter, sem debounce, e o botão de limpar restaurará
os filtros vazios e a listagem básica.

Alternativa descartada: buscar a cada tecla, pois adicionaria chamadas,
latência e complexidade sem necessidade para o escopo inicial.

## Risks / Trade-offs

- **[Desempenho de texto]** Correspondência em dois campos pode crescer com o
  volume → aplicar a consulta no Xano e manter a mudança sem paginação por
  enquanto.
- **[Termo vazio]** Filtros opcionais podem gerar consultas equivalentes →
  normalizar espaços e preservar a listagem sem filtros.
- **[Categoria inválida]** Um identificador manipulável pode ser enviado →
  validar a existência no Xano antes de consultar.
- **[Exposição]** Novos parâmetros não devem ampliar dados retornados →
  reutilizar a seleção explícita de campos públicos.

## Migration Plan

1. Definir no Xano os parâmetros opcionais e a consulta filtrada da listagem.
2. Validar busca textual, categoria, combinação, ausência de filtros e
   ordenação diretamente no endpoint.
3. Integrar os parâmetros no cliente HTTP do Reflex.
4. Adicionar formulário, limpeza e estados de erro na interface.
5. Executar testes públicos sem token e confirmar que a resposta não expõe
   dados privados.

## Open Questions

- Nenhuma decisão de escopo permanece aberta para iniciar a implementação.
