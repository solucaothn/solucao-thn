## ADDED Requirements

### Requirement: Legibilidade das perguntas e da tabela de dados
As perguntas da Central de ajuda e a tabela da Política de privacidade SHALL continuar legíveis em telas estreitas.

#### Scenario: Pergunta em duas linhas
- **WHEN** uma pergunta da Central de ajuda ou de uma categoria ocupa mais de uma linha, como em 360 px
- **THEN** as linhas da pergunta MUST ter altura de linha de cerca de 1,35, sem ficarem coladas

#### Scenario: Tabela da Privacidade no celular
- **WHEN** `/privacidade` é exibida com 360 px de largura
- **THEN** a primeira coluna da tabela MUST NOT quebrar palavras no meio, como “Mensagens” ou “Registros”
- **AND** a tabela MUST continuar rolando dentro do próprio contêiner, sem rolagem horizontal da página
