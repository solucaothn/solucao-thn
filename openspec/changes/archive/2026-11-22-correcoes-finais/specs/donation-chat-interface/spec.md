## MODIFIED Requirements

### Requirement: Atualização automática limitada
Com uma conversa aberta e a aba visível, a página MUST buscar mensagens novas em intervalos de no mínimo 25 segundos, pedindo só as posteriores à última recebida. A mesma consulta MUST trazer também a confirmação de leitura e as mensagens editadas. Sem conversa aberta e com a aba visível, a lista de conversas MUST ser atualizada em intervalos de no mínimo 30 segundos. Com uma conversa aberta, a lista MUST NOT se atualizar sozinha. Com a aba oculta, MUST NOT fazer consultas automáticas. Não há tempo real.

#### Scenario: Conversa aberta e aba visível
- **WHEN** a conversa está aberta e a aba está visível
- **THEN** a página MUST consultar mensagens novas no máximo uma vez a cada 25 segundos e acrescentá-las sem duplicar as existentes
- **AND** MUST NOT consultar a lista de conversas automaticamente

#### Scenario: Leitura e edições na mesma consulta
- **WHEN** a consulta automática da conversa responde
- **THEN** a página MUST atualizar o ✓✓ das próprias mensagens e o texto das mensagens editadas com os dados dessa resposta
- **AND** MUST NOT fazer requisição a mais para isso

#### Scenario: Atualização da lista
- **WHEN** a pessoa está em `/chat`, sem conversa aberta, com a aba visível
- **THEN** a página MUST consultar a primeira página da lista no máximo uma vez a cada 30 segundos, atualizando contadores, ordem e conversas novas
- **AND** MUST manter as conversas de páginas já carregadas com “Carregar mais conversas”, sem duplicá-las

#### Scenario: Atualizar a lista com uma conversa aberta
- **WHEN** há uma conversa aberta e a pessoa aciona o botão “Atualizar conversas”
- **THEN** a página MUST consultar a lista uma vez, sem fechar a conversa

#### Scenario: Voltar para a lista em tela estreita
- **WHEN** em tela estreita a pessoa sai da conversa com o controle de voltar à lista
- **THEN** a página MUST consultar a primeira página da lista uma vez, mantendo as conversas já carregadas sem duplicá-las
- **AND** enquanto a lista estiver à mostra, a conversa MUST contar como fechada: as mensagens MUST NOT ser consultadas automaticamente, e a lista MUST voltar à atualização de 30 segundos
- **AND** abrir de novo uma conversa MUST carregar as mensagens dela na hora

#### Scenario: Aba oculta
- **WHEN** a aba fica oculta
- **THEN** a página MUST NOT fazer consultas automáticas até a aba voltar a ficar visível

#### Scenario: Consulta automática recebe 429
- **WHEN** uma consulta automática recebe HTTP 429, do chat ou da plataforma
- **THEN** a página MUST pausar as consultas automáticas por pelo menos 60 segundos, sem mostrar erro bloqueante
- **AND** a pausa MUST valer para as mensagens e para a lista

#### Scenario: Sair da página
- **WHEN** a pessoa sai de `/chat`
- **THEN** as consultas automáticas MUST parar
