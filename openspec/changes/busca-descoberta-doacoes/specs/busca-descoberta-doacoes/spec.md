# busca-descoberta-doacoes Specification

## Purpose

Permitir que visitantes e usuários autenticados encontrem doações do catálogo
por texto e categoria, com consulta pública executada no Xano e exposição
limitada aos dados já públicos.

## ADDED Requirements

### Requirement: Busca textual pública

O sistema SHALL aceitar um termo opcional de busca e procurar correspondências
nos campos `title` e `description` da doação, sem exigir autenticação.

#### Scenario: Termo encontra doações

- **WHEN** um visitante informa um termo que aparece no título ou na descrição
- **THEN** o backend retorna as doações correspondentes

#### Scenario: Termo não encontra doações

- **WHEN** um visitante informa um termo sem correspondências
- **THEN** o backend retorna uma lista vazia bem-formada

#### Scenario: Termo é normalizado

- **WHEN** o cliente envia um termo com espaços no início ou no fim
- **THEN** o backend remove os espaços periféricos antes de consultar

### Requirement: Filtro por categoria

O sistema SHALL aceitar uma categoria opcional por identificador e retornar
somente doações associadas a essa categoria.

#### Scenario: Categoria existente

- **WHEN** um visitante seleciona uma categoria existente
- **THEN** o backend retorna somente doações daquela categoria

#### Scenario: Categoria inexistente

- **WHEN** o cliente informa um identificador de categoria inexistente
- **THEN** o backend rejeita o filtro com erro de entrada explícito

#### Scenario: Filtro sem categoria

- **WHEN** nenhuma categoria é informada
- **THEN** o backend não restringe os resultados por categoria

### Requirement: Combinação e ausência de filtros

O sistema SHALL permitir combinar um termo textual com uma categoria e SHALL
retornar a listagem básica quando nenhum filtro for informado.

#### Scenario: Texto e categoria combinados

- **WHEN** o visitante informa termo e categoria
- **THEN** o backend retorna somente doações que atendem simultaneamente aos
  dois filtros

#### Scenario: Consulta sem filtros

- **WHEN** o visitante envia a consulta sem termo e sem categoria
- **THEN** o backend retorna a listagem pública básica existente

### Requirement: Status e ordenação dos resultados

O sistema SHALL incluir doações de todos os status já suportados pelo catálogo
e SHALL ordenar os resultados pela criação mais recente primeiro.

#### Scenario: Doações concluídas permanecem pesquisáveis

- **WHEN** existem doações disponíveis, reservadas e concluídas que atendem ao
  filtro
- **THEN** o backend retorna todas elas, sem filtro implícito de status

#### Scenario: Resultados recentes primeiro

- **WHEN** duas ou mais doações atendem à consulta
- **THEN** a doação com criação mais recente aparece antes das anteriores

### Requirement: Exposição pública mínima

O sistema SHALL manter na resposta apenas os campos públicos já definidos para
o catálogo e SHALL continuar sem retornar `owner_id`, e-mail, localização ou
dados de contato do proprietário.

#### Scenario: Consulta pública sem autenticação

- **WHEN** um visitante sem token consulta o catálogo filtrado
- **THEN** o backend retorna os resultados públicos sem exigir autenticação e
  sem dados privados do proprietário

### Requirement: Interface de descoberta no Reflex

O Reflex SHALL oferecer entrada para texto e seleção de uma categoria, enviar a
consulta ao endpoint público no submit ou ao pressionar Enter e exibir o
resultado retornado pelo Xano.

#### Scenario: Usuário executa uma busca

- **WHEN** o usuário envia o formulário de descoberta
- **THEN** o Reflex chama o endpoint público com os filtros informados e
  atualiza a listagem com a resposta do backend

#### Scenario: Usuário limpa a busca

- **WHEN** o usuário remove o termo e a categoria e envia novamente
- **THEN** o Reflex solicita a listagem básica e exibe os resultados retornados

#### Scenario: Erro do backend

- **WHEN** o Xano rejeita a consulta ou fica indisponível
- **THEN** o Reflex exibe uma mensagem de erro explícita e não inventa
  resultados locais
