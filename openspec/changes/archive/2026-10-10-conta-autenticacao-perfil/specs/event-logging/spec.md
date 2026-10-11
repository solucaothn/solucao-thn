# Spec Delta

## Purpose

Define o registro de eventos da conta sem expor dados pessoais ou segredos de autenticação nos metadados associados aos eventos.

## ADDED Requirements

### Requirement: Metadados de eventos sem dados pessoais
O sistema SHALL registrar novos eventos de conta sem incluir dados pessoais ou segredos de autenticação em seus metadados.

#### Scenario: Registro de evento de conta
- **WHEN** o sistema registra um evento de cadastro, login, consulta de sessão ou recuperação de senha
- **THEN** o evento não contém e-mail, nome, cidade, estado, senha, token ou identificador pessoal nos metadados
- **AND** a associação do ator, quando necessária, permanece no campo próprio de usuário do evento

#### Scenario: Evento sem contexto adicional seguro
- **WHEN** um fluxo registra um evento sem contexto operacional não pessoal necessário
- **THEN** o sistema grava o evento sem metadados adicionais