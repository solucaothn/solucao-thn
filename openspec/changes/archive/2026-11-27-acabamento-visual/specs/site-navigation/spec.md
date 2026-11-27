## ADDED Requirements

### Requirement: “Entrar” e “Quero Doar” com o mesmo formato
Nos cabeçalhos que mostram “Entrar” e “Quero Doar”, os dois botões SHALL ter a mesma altura e os mesmos cantos arredondados.

#### Scenario: Cabeçalho sem sessão no computador
- **WHEN** uma página com “Entrar” e “Quero Doar” é exibida com 1280 px, sem sessão
- **THEN** os dois botões MUST ter cerca de 44 px de altura e cantos de 6 px

#### Scenario: Cabeçalho no celular
- **WHEN** a página é exibida com 360 px
- **THEN** “Entrar” MUST manter cerca de 44 px de altura e cantos de 6 px, com área de toque de pelo menos 44 px
