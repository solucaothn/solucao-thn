## ADDED Requirements

### Requirement: Saída da lista de conversas vazia
Quando a pessoa ainda não tem conversas, a página `/chat` SHALL oferecer, junto ao aviso “Você ainda não tem conversas.”, o link “Explorar doações” para `/explorar`.

#### Scenario: Lista vazia com caminho
- **WHEN** a pessoa autenticada abre `/chat` e não participa de nenhuma conversa
- **THEN** a página MUST mostrar “Você ainda não tem conversas.” e o link “Explorar doações”, com foco visível e pelo menos 44 px de área de toque
