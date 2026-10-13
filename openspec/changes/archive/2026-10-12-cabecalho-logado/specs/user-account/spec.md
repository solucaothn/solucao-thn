# Spec Delta

## ADDED Requirements

### Requirement: Identidade da sessão no cabeçalho da home
A home SHALL representar a sessão autenticada com o primeiro nome da pessoa e permitir que ela encerre a sessão sem adicionar persistência própria em armazenamento do navegador.

#### Scenario: Exibir pessoa autenticada
- **WHEN** a consulta autenticada da conta retorna um nome válido
- **THEN** o cabeçalho exibe “Olá, <primeiro nome>” e o botão “Sair” no lugar de “Entrar”
- **AND** mantém o botão “Quero Doar”

#### Scenario: Consulta da conta falha sem rejeitar o token
- **WHEN** a consulta falha por rede, configuração ou erro do serviço que não indique token inválido
- **THEN** a home permanece disponível e o cabeçalho exibe “Minha conta”
- **AND** o carregamento da contagem e das doações recentes continua independente

#### Scenario: Token rejeitado
- **WHEN** a consulta da conta indica que o token está ausente, inválido ou expirado
- **THEN** a aplicação limpa os dados transitórios da sessão e exibe o cabeçalho de visitante com “Entrar”
- **AND** mantém a home pública disponível

#### Scenario: Encerrar sessão
- **WHEN** a pessoa aciona “Sair”
- **THEN** a aplicação limpa o token e o nome do estado transitório
- **AND** permanece na home com o cabeçalho de visitante

#### Scenario: Manter sessão ao recarregar a mesma aba
- **WHEN** uma pessoa recarrega a home na mesma aba
- **THEN** o estado da sessão permanece disponível nessa aba e o cabeçalho continua autenticado
- **AND** o site não grava o token em armazenamento do navegador

#### Scenario: Não compartilhar sessão com outra aba ou reinício do servidor
- **WHEN** a pessoa abre uma aba nova ou o servidor Reflex é reiniciado
- **THEN** a sessão não está disponível nessa nova aba ou após o reinício e o cabeçalho apresenta “Entrar”
- **AND** o site não restaura a sessão por persistência própria em armazenamento do navegador

#### Scenario: Minimizar dados mantidos para exibição
- **WHEN** a consulta autenticada retorna os dados da conta
- **THEN** o estado de exibição mantém somente o primeiro nome
- **AND** o token e os demais dados da conta não são registrados em logs
