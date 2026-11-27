## ADDED Requirements

### Requirement: Espaçamento do rodapé
O rodapé SHALL separar os blocos e as colunas de links com espaço suficiente para que nenhum título ou link encoste em outro.

#### Scenario: Rodapé no celular
- **WHEN** o rodapé é exibido com 360 px de largura
- **THEN** MUST haver cerca de 16 px entre o bloco “Fale conosco” e o título “Links rápidos”
- **AND** as duas colunas de links MUST ter cerca de 12 px entre si, sem que um link encoste no da outra coluna

#### Scenario: Rodapé no computador
- **WHEN** o rodapé é exibido com 1280 px de largura
- **THEN** “Fale conosco” e “Links rápidos” MUST continuar lado a lado, com as colunas de links separadas por cerca de 12 px
