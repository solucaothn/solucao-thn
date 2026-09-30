## Why

O catálogo de doações já permite cadastro, manutenção, categorização e
listagem básica, mas encontrar um item específico exige percorrer todos os
registros. A plataforma precisa de uma forma simples e pública de descoberta
que aproveite os campos já existentes nas doações e categorias.

## What Changes

- Adicionar busca textual pública por título e descrição.
- Adicionar filtro público por uma categoria por vez.
- Manter todos os status existentes na busca, incluindo `disponível`,
  `reservada` e `concluída`.
- Retornar a listagem básica atual quando nenhum filtro for informado.
- Ordenar os resultados pelos mais recentes primeiro.
- Executar a consulta e os filtros no Xano, preservando a resposta pública sem
  dados privados do proprietário.
- Adicionar ao Reflex um formulário de busca executado no envio ou ao
  pressionar Enter.

Fora do escopo:

- Filtro por status nesta change.
- Busca por localização, proprietário, e-mail ou outros dados privados.
- Busca enquanto o usuário digita ou debounce.
- Seleção de múltiplas categorias.
- Paginação, limite configurável ou busca avançada.
- Alteração nas regras de cadastro, edição, exclusão ou autorização de
  doações.
- Gestão de categorias por API.

## Capabilities

### New Capabilities

- `busca-descoberta-doacoes`: consulta pública de doações por texto e
  categoria.

### Modified Capabilities

- `catalogo-doacoes`: ampliar a listagem básica existente com parâmetros
  opcionais de busca, sem alterar sua exposição pública ou regras de posse.

## Impact

- Workspace Xano: ampliar o endpoint público de listagem de doações para
  aceitar termo textual e categoria, aplicar a consulta no backend e ordenar
  por data de criação decrescente.
- Frontend Reflex: adicionar estado, formulário e atualização da listagem com
  filtros, mantendo categorias carregadas pelo endpoint existente.
- Segurança: nenhuma autorização nova é introduzida; a resposta continua
  limitada aos campos públicos já definidos para o catálogo.
- Integração: usuários autenticados e visitantes usarão a mesma consulta
  pública.
