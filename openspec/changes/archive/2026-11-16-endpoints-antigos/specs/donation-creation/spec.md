## ADDED Requirements

### Requirement: Criação de doação só pela publicação
O backend MUST criar doações somente pela operação de publicação descrita em “Publicação autenticada e persistente”, com as validações dela: de uma a cinco fotos, cidade e UF do perfil, categoria, condição, modalidade de entrega e preferência de contato. Nenhum outro endpoint pode criar uma doação.

#### Scenario: Criação antiga sem as regras da publicação
- **WHEN** qualquer cliente chama `POST catalog/donations`, com ou sem sessão e com qualquer corpo
- **THEN** o backend MUST responder “não encontrado”
- **AND** MUST NOT criar doação

#### Scenario: Publicação preservada
- **WHEN** uma pessoa autenticada publica uma doação pelo cadastro em cinco etapas
- **THEN** a publicação MUST funcionar como antes, com as mesmas validações e respostas
