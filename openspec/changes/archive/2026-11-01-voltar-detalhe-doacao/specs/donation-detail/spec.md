# Spec Delta

## ADDED Requirements

### Requirement: Botão Voltar do detalhe
A página de detalhe MUST oferecer um controle acessível para voltar à home em todos os estados de exibição.

#### Scenario: Botão Voltar durante o carregamento
- **WHEN** a página de detalhe está carregando a doação
- **THEN** MUST apresentar o controle “Voltar” com seta verde abaixo do cabeçalho
- **AND** MUST disponibilizar o rótulo acessível “Voltar”

#### Scenario: Botão Voltar com a doação carregada
- **WHEN** a página apresenta os dados de uma doação disponível
- **THEN** MUST apresentar o controle “Voltar” com seta verde abaixo do cabeçalho
- **AND** MUST disponibilizar o rótulo acessível “Voltar”

#### Scenario: Botão Voltar quando a doação não é encontrada
- **WHEN** a página apresenta “Doação não encontrada”, inclusive para um ID inválido
- **THEN** MUST apresentar o controle “Voltar” com seta verde abaixo do cabeçalho
- **AND** MUST disponibilizar o rótulo acessível “Voltar”

#### Scenario: Botão Voltar em caso de erro
- **WHEN** a página apresenta uma mensagem de erro de rede ou de resposta inválida
- **THEN** MUST apresentar o controle “Voltar” com seta verde abaixo do cabeçalho
- **AND** MUST disponibilizar o rótulo acessível “Voltar”

#### Scenario: Retornar para a home
- **WHEN** uma pessoa ativa o controle “Voltar” em qualquer estado da página de detalhe
- **THEN** o sistema MUST navegar para `/`
