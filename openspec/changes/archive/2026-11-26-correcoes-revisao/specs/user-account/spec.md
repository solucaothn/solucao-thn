## ADDED Requirements

### Requirement: Carregamento visível no login e no cadastro
Ao acionar “Entrar” ou “Criar”, a interface MUST mostrar o botão como “Entrando...” ou “Criando...”, desativado, desde o acionamento até a resposta do backend, com um único pedido por acionamento.

#### Scenario: Login em andamento
- **WHEN** a pessoa aciona “Entrar” com e-mail e senha preenchidos
- **THEN** o botão MUST aparecer como “Entrando...”, desativado, antes de a resposta do backend chegar
- **AND** numa falha, MUST voltar a “Entrar” com a mensagem de erro

#### Scenario: Cadastro em andamento
- **WHEN** a pessoa aciona “Criar” com os dados válidos
- **THEN** o botão MUST aparecer como “Criando...”, desativado, antes de a resposta do backend chegar
- **AND** numa falha, MUST voltar a “Criar” com a mensagem de erro e os dados mantidos

#### Scenario: Dados recusados pela tela
- **WHEN** faltam e-mail ou senha no login, ou os dados do cadastro não passam na conferência da tela
- **THEN** a interface MUST mostrar a mensagem de erro sem mostrar o carregamento e sem chamar o backend
