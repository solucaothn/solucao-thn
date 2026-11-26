## MODIFIED Requirements

### Requirement: Lista de categorias
O site SHALL apresentar todas as categorias válidas retornadas pelo backend, sem exclusões por nome, cada uma com ícone e nome, levando a `/explorar?categoria=<id>`. As categorias SHALL ser buscadas no backend uma vez e reaproveitadas pela gaveta, pela página `/categorias`, pela busca da home, pela Explorar, pelo cadastro de doação e pela edição de doação; uma nova busca SHALL acontecer só depois de uma falha ou quando a cópia guardada expirar.

#### Scenario: Categorias do backend
- **WHEN** o backend retorna as categorias
- **THEN** a lista MUST mostrar cada categoria válida, inclusive “Móveis”, com um ícone correspondente ao nome (ou um ícone genérico) e uma seta decorativa
- **AND** acionar uma categoria, pelo mouse ou pelo teclado, MUST abrir `/explorar?categoria=<id>` daquela categoria

#### Scenario: Ícone de Móveis
- **WHEN** a lista mostra a categoria “Móveis”
- **THEN** o ícone MUST ser o de sofá, decorativo, sem rótulo próprio

#### Scenario: Categoria que deixou de existir
- **WHEN** o backend não retorna mais uma categoria, como “Alimentos”
- **THEN** ela MUST NOT aparecer na lista, e um link antigo `/explorar?categoria=<id>` dela MUST abrir a Explorar sem quebrar, mostrando o estado vazio

#### Scenario: Falha ao carregar
- **WHEN** o backend não retorna as categorias
- **THEN** a lista MUST informar que as categorias não puderam ser carregadas e oferecer o link “Explorar doações” para `/explorar`, sem categorias fictícias
- **AND** a lista MUST oferecer o botão “Tentar de novo”, que busca as categorias outra vez
- **AND** acionar “Tentar de novo”, na página `/categorias` ou na gaveta, MUST mostrar “Carregando categorias...” na hora, até a resposta

#### Scenario: Navegar entre páginas que usam categorias
- **WHEN** a pessoa abre, uma depois da outra, a home, a gaveta, `/categorias`, a Explorar filtrada e o cadastro de doação
- **THEN** as categorias MUST ser buscadas no backend uma única vez, e as outras páginas MUST reaproveitar a mesma lista

#### Scenario: Falha não fica guardada
- **WHEN** uma busca de categorias falha
- **THEN** nada MUST ficar guardado, e a próxima página ou o “Tentar de novo” MUST buscar de novo
