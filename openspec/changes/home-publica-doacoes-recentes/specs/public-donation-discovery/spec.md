# Spec Delta

## Purpose

Define a consulta pública das doações disponíveis que podem ser apresentadas na home, incluindo a contagem em circulação e os dados visuais opcionais dos itens. A capacidade mantém doações existentes compatíveis quando ainda não possuem foto ou condição.

## ADDED Requirements

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
