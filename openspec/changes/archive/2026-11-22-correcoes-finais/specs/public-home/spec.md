## ADDED Requirements

### Requirement: Tentar de novo nas falhas da home
Quando a contagem ou as doações recentes da home não puderem ser carregadas, a home SHALL mostrar, junto de cada mensagem de erro, o botão “Tentar de novo”, que busca outra vez os dados da home sem recarregar o site.

#### Scenario: Falha da contagem
- **WHEN** o serviço de contagem falha
- **THEN** a home MUST mostrar a mensagem de erro da contagem e o botão “Tentar de novo”, com área de toque de pelo menos 44 px, foco visível e contraste mínimo AA

#### Scenario: Falha das doações recentes
- **WHEN** o serviço de doações recentes falha
- **THEN** a home MUST mostrar a mensagem de erro das recentes e o botão “Tentar de novo”, com as mesmas regras de toque, foco e contraste

#### Scenario: Nova tentativa
- **WHEN** a pessoa aciona “Tentar de novo”
- **THEN** a home MUST mostrar o carregamento e buscar a contagem e as recentes outra vez, mostrando os dados ou a mensagem de erro conforme o resultado

#### Scenario: Lista vazia não é falha
- **WHEN** o serviço retorna uma lista vazia de recentes
- **THEN** a home MUST mostrar que ainda não há doações, sem o botão “Tentar de novo”
