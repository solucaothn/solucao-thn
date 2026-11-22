## ADDED Requirements

### Requirement: Caminhos a partir de uma doação indisponível
Quando a doação não está disponível (reservada, concluída, apagada ou com identificador inválido), a página de detalhe SHALL manter o aviso “Doação não encontrada” e acrescentar uma explicação e dois caminhos, sem revelar qual é o status da doação.

#### Scenario: Doação indisponível
- **WHEN** a página de detalhe mostra “Doação não encontrada”
- **THEN** ela MUST explicar que a doação pode ter sido reservada, concluída ou removida por quem doou
- **AND** MUST oferecer os links “Ver outras doações” (`/explorar`) e “Voltar ao início” (`/`), com foco visível e pelo menos 44 px de área de toque
- **AND** MUST NOT dizer qual desses casos aconteceu
