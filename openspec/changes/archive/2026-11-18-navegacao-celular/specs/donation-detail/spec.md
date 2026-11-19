## ADDED Requirements

### Requirement: Tentar de novo quando o detalhe falha
Quando o detalhe da doação não puder ser carregado, a página SHALL mostrar a mensagem de falha com o botão “Tentar novamente”, que busca a doação outra vez sem sair da página.

#### Scenario: Falha ao carregar o detalhe
- **WHEN** a busca do detalhe falha (por exemplo, pelo limite de pedidos do backend)
- **THEN** a página MUST mostrar a mensagem de falha e o botão “Tentar novamente”, com 44 px de área de toque e foco visível
- **AND** acionar o botão MUST buscar a doação de novo e, se der certo, mostrar o detalhe
