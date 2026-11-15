## ADDED Requirements

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
