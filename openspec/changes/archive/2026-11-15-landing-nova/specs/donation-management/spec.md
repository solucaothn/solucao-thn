## MODIFIED Requirements

### Requirement: Link “Minhas doações” no cabeçalho da home
O cabeçalho autenticado da home MUST oferecer “Minhas doações”, que leva a `/minhas-doacoes`, como item do menu da conta. O cabeçalho de visitante MUST NOT mostrar esse link.

#### Scenario: Pessoa logada na home
- **WHEN** a home está com o cabeçalho autenticado e a pessoa abre o menu da conta
- **THEN** o menu MUST mostrar “Minhas doações”, junto de “Editar perfil” e “Sair”, levando a `/minhas-doacoes`

#### Scenario: Visitante na home
- **WHEN** a home está com o cabeçalho de visitante
- **THEN** o cabeçalho MUST NOT mostrar “Minhas doações”
