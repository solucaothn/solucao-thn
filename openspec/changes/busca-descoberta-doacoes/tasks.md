## 1. Contrato e consulta no Xano

- [x] 1.1 Adicionar parâmetros opcionais de termo e `category_id` ao endpoint
  público de doações, com normalização do termo e validação da categoria.
- [x] 1.2 Implementar busca em título e descrição, combinação dos filtros e
  retorno sem filtros equivalente à listagem básica.
- [x] 1.3 Ordenar resultados por `created_at` descendente e preservar todos os
  status do catálogo.
- [x] 1.4 Verificar que a resposta continua limitada aos campos públicos e não
  inclui dados do proprietário.

## 2. Cliente e estado Reflex

- [x] 2.1 Estender o cliente Xano para enviar termo e categoria opcionais sem
  persistir dados sensíveis no navegador.
- [x] 2.2 Adicionar estado e setters para os filtros, estado de busca e limpeza
  da consulta.
- [x] 2.3 Integrar busca, combinação de filtros, consulta sem filtros e erros
  explícitos do backend.

## 3. Interface de descoberta

- [x] 3.1 Criar formulário com campo de texto, seleção de categoria, submit e
  ação para limpar filtros.
- [x] 3.2 Atualizar a listagem existente com os resultados retornados pelo
  Xano, mantendo status, categoria e dados públicos.
- [x] 3.3 Verificar comportamento para resultados, lista vazia, categoria
  inválida e indisponibilidade da API.

## 4. Segurança e integração

- [x] 4.1 Testar as consultas como visitante sem token e como usuário
  autenticado, confirmando que ambas permanecem públicas.
- [ ] 4.2 Testar termo, categoria, combinação, ausência de filtros, todos os
  status e ordenação mais recente primeiro contra o Xano.
- [x] 4.3 Executar build/testes do Reflex e confirmar que nenhum filtro ou
  resultado é decidido apenas no cliente.
