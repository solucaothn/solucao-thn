# backend-request-budget Specification

## Purpose
Define como o site economiza pedidos ao backend (o plano grátis do Xano aceita 10 pedidos a cada 20 s para o site inteiro), para várias pessoas navegarem ao mesmo tempo sem falhas: dados públicos guardados no servidor, nova tentativa no limite e cancelamento sem erro.

## Requirements

### Requirement: Dados públicos guardados no servidor
A contagem e as doações recentes da home, cada página da busca (por combinação de filtros e página) e o detalhe de cada doação SHALL ser guardados no servidor do site por até 60 s e reaproveitados por todas as pessoas. Só dados públicos SHALL ser guardados, sem token, e-mail ou outro dado pessoal. Uma falha MUST NOT ficar guardada.

#### Scenario: Várias pessoas na mesma página
- **WHEN** várias pessoas abrem a home, a mesma busca ou o mesmo detalhe dentro de 60 s
- **THEN** o backend MUST receber um único pedido para cada um desses dados nesse intervalo

#### Scenario: Mudança feita pela própria pessoa
- **WHEN** a pessoa publica, edita, muda o status ou apaga uma doação com sucesso
- **THEN** os dados públicos guardados MUST ser descartados, e a próxima página MUST mostrar a mudança na hora

#### Scenario: Falha não guardada
- **WHEN** um desses pedidos falha
- **THEN** nada MUST ficar guardado, e a próxima página MUST pedir de novo

### Requirement: Nova tentativa no limite do backend
Quando o backend responder que o limite de pedidos foi atingido (HTTP 429), o site SHALL esperar cerca de 2 s e tentar o mesmo pedido mais uma vez antes de mostrar a mensagem de falha.

#### Scenario: Limite passageiro
- **WHEN** um pedido recebe 429 e a nova tentativa, 2 s depois, dá certo
- **THEN** a página MUST mostrar os dados normalmente, sem mensagem de falha

#### Scenario: Limite persistente
- **WHEN** a nova tentativa também recebe 429
- **THEN** a página MUST mostrar a sua mensagem de falha, sem uma terceira tentativa

### Requirement: Navegação cancelada não é falha
Quando a pessoa sai da página e o pedido em andamento é cancelado, o site MUST NOT tratar isso como falha nem mostrar mensagem de erro.

#### Scenario: Sair da página durante o carregamento
- **WHEN** a pessoa navega para outra página enquanto a anterior ainda carregava dados
- **THEN** nenhuma mensagem de falha MUST aparecer por causa do pedido cancelado
