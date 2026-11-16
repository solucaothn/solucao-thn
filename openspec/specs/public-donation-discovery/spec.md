# public-donation-discovery Specification

## Purpose

Define a consulta pública das doações disponíveis que podem ser apresentadas na home, incluindo a contagem em circulação e os dados visuais opcionais dos itens. A capacidade mantém doações existentes compatíveis quando ainda não possuem foto ou condição.

## Requirements

### Requirement: Foto e condição opcionais da doação
O sistema SHALL permitir que uma doação tenha uma foto e uma condição opcional, com condição limitada a Ótimo, Bom ou Regular.

#### Scenario: Doação sem dados visuais
- **WHEN** uma doação existente não possui foto nem condição
- **THEN** o sistema mantém a doação válida e disponível para consulta pública, retornando esses campos sem valor

#### Scenario: Condição válida
- **WHEN** uma doação possui condição Ótimo, Bom ou Regular
- **THEN** o sistema aceita e retorna a condição registrada

#### Scenario: Condição fora dos valores permitidos
- **WHEN** uma condição diferente de Ótimo, Bom ou Regular é informada
- **THEN** o sistema rejeita esse valor

### Requirement: Listagem pública de doações recentes
O sistema SHALL permitir consulta sem autenticação das quatro doações disponíveis mais recentes, em ordem decrescente de criação, retornando os dados necessários aos cartões da home e representando foto como URL pública consumível pelo navegador ou nulo.

#### Scenario: Consultar doações recentes sem autenticação
- **WHEN** uma pessoa consulta as doações recentes sem token de autenticação
- **THEN** o sistema retorna até quatro doações com status disponível, ordenadas da mais recente para a mais antiga
- **AND** cada resultado contém identificador, data de criação, título, foto e condição
- **AND** a foto de cada resultado é uma URL pública ou nula

#### Scenario: Excluir doações indisponíveis
- **WHEN** existem doações disponíveis, reservadas e concluídas
- **THEN** a listagem retorna somente as que possuem status disponível

#### Scenario: Doação recente sem foto ou condição
- **WHEN** uma doação disponível sem foto ou condição está entre as quatro mais recentes
- **THEN** o sistema a inclui na resposta com os campos ausentes sem valor

### Requirement: Contagem pública de doações em circulação
O sistema SHALL permitir consulta sem autenticação da quantidade total de doações com status disponível.

#### Scenario: Contar doações disponíveis
- **WHEN** uma pessoa consulta a contagem sem token de autenticação
- **THEN** o sistema retorna a quantidade de todas as doações disponíveis, sem limitar a contagem aos itens da listagem recente

#### Scenario: Nenhuma doação disponível
- **WHEN** não existe doação com status disponível
- **THEN** o sistema retorna a contagem zero

### Requirement: Contagem pública de doações concluídas
A consulta pública de contagem SHALL devolver também a quantidade total de doações com status concluída, sem autenticação e sem dados pessoais, mantendo a contagem de disponíveis como está.

#### Scenario: Contar doações concluídas
- **WHEN** uma pessoa consulta a contagem sem token de autenticação
- **THEN** o sistema retorna, além da quantidade de doações disponíveis, a quantidade de todas as doações concluídas

#### Scenario: Nenhuma doação concluída
- **WHEN** não existe doação com status concluída
- **THEN** o sistema retorna a quantidade de concluídas igual a zero

#### Scenario: Resposta só com contagens
- **WHEN** o sistema responde à consulta de contagem
- **THEN** a resposta MUST conter somente as quantidades, sem identificadores, nomes, e-mails ou outros dados de doações ou pessoas

### Requirement: Busca pública de doações disponíveis
O sistema SHALL permitir, sem autenticação, buscar doações disponíveis com filtros opcionais de texto, categoria e UF, em páginas de 12, da mais nova para a mais antiga, retornando só os dados dos cartões e os totais da paginação.

#### Scenario: Busca sem filtros
- **WHEN** uma pessoa consulta a busca sem filtros e sem token
- **THEN** o sistema retorna a primeira página das doações com status disponível, ordenadas da mais nova para a mais antiga
- **AND** a resposta contém, para cada doação, somente id, data de criação, título, URL pública da foto (ou nulo) e condição, além de `page`, `per_page`, `total` e `page_total`

#### Scenario: Filtros combinados
- **WHEN** a consulta informa qualquer combinação de texto, categoria e UF
- **THEN** o sistema retorna só as doações disponíveis da categoria e da UF informadas cujo título ou descrição contém o texto, sem diferenciar maiúsculas de minúsculas
- **AND** os totais refletem só as doações filtradas

#### Scenario: Nenhuma doação de outros status
- **WHEN** existem doações reservadas ou concluídas que atendem aos filtros
- **THEN** elas MUST NOT aparecer nos resultados nem nos totais

#### Scenario: Página fora do intervalo
- **WHEN** a consulta pede uma página maior que o total de páginas
- **THEN** o sistema retorna a lista vazia com os totais corretos

#### Scenario: Entrada inválida
- **WHEN** a página é menor que 1 ou a UF não tem duas letras
- **THEN** o sistema rejeita a consulta com erro de entrada, sem retornar doações

#### Scenario: Sem dados pessoais
- **WHEN** o sistema responde à busca
- **THEN** a resposta MUST NOT conter dono, nome, e-mail, cidade, descrição ou outros dados pessoais

### Requirement: Nenhuma listagem pública fora das regras de descoberta
O backend MUST NOT expor endpoint público que liste doações fora das consultas públicas definidas nesta capacidade (doações recentes, contagens e busca de disponíveis). Nenhuma consulta pública pode devolver dados de doações reservadas ou concluídas.

#### Scenario: Listagem antiga de doações
- **WHEN** qualquer cliente chama `GET catalog/donations`, com ou sem filtros, com ou sem sessão
- **THEN** o backend MUST responder “não encontrado”
- **AND** MUST NOT devolver título, descrição, status ou qualquer outro dado de doação

#### Scenario: Descoberta pública preservada
- **WHEN** uma pessoa consulta as doações recentes, as contagens ou a busca pública
- **THEN** essas consultas MUST funcionar como antes, só com doações disponíveis nas listagens

#### Scenario: Edição e exclusão no mesmo caminho preservadas
- **WHEN** a pessoa dona edita (`PATCH catalog/donations`) ou apaga (`DELETE catalog/donations`) uma doação sua
- **THEN** essas operações MUST continuar existindo, com as mesmas regras e respostas
