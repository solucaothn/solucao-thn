## MODIFIED Requirements

### Requirement: Dados públicos guardados no servidor
A contagem e as doações recentes da home, cada página da busca (por combinação de filtros e página), o detalhe de cada doação e cada página do perfil de quem doa SHALL ser guardados no servidor do site por até 60 s e reaproveitados por todas as pessoas. Só dados públicos SHALL ser guardados, sem token, e-mail ou outro dado pessoal. Uma falha MUST NOT ficar guardada.

#### Scenario: Várias pessoas na mesma página
- **WHEN** várias pessoas abrem a home, a mesma busca, o mesmo detalhe ou a mesma página do perfil de quem doa dentro de 60 s
- **THEN** o backend MUST receber um único pedido para cada um desses dados nesse intervalo

#### Scenario: Mudança feita pela própria pessoa
- **WHEN** a pessoa publica, edita, muda o status ou apaga uma doação com sucesso, ou salva o perfil ou a foto de perfil com sucesso
- **THEN** os dados públicos guardados, inclusive os perfis de quem doa, MUST ser descartados, e a próxima página MUST mostrar a mudança na hora

#### Scenario: Falha não guardada
- **WHEN** um desses pedidos falha, inclusive com HTTP 404 ou 429 do perfil de quem doa
- **THEN** nada MUST ficar guardado, e a próxima página MUST pedir de novo
