## ADDED Requirements

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
