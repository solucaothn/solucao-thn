## ADDED Requirements

### Requirement: Confirmação de leitura nas próprias mensagens
Nas mensagens enviadas pela própria pessoa, a conversa MUST mostrar embaixo da bolha, junto do horário, um ✓ cinza quando a outra pessoa ainda não leu e um ✓✓ verde quando ela já leu. Nas mensagens da outra pessoa MUST NOT aparecer indicação de leitura.

#### Scenario: Mensagem enviada e ainda não lida
- **WHEN** uma mensagem da própria pessoa tem identificador maior que a última lida pela outra pessoa
- **THEN** a página MUST mostrar um ✓ cinza ao lado do horário, com o rótulo acessível “Enviada”

#### Scenario: Mensagem lida pela outra pessoa
- **WHEN** uma mensagem da própria pessoa tem identificador menor ou igual ao da última lida pela outra pessoa
- **THEN** a página MUST mostrar um ✓✓ verde ao lado do horário, com o rótulo acessível “Lida”

#### Scenario: Mensagem da outra pessoa
- **WHEN** a mensagem foi enviada pela outra pessoa
- **THEN** a página MUST NOT mostrar ✓ nem ✓✓ nela

#### Scenario: Leitura confirmada durante a conversa
- **WHEN** a conversa está aberta e a outra pessoa lê as mensagens
- **THEN** o ✓ das mensagens lidas MUST passar a ✓✓ na próxima atualização automática da conversa, sem requisição a mais

### Requirement: Edição de mensagem
Nas próprias mensagens enviadas há até 15 minutos, fora de conversa somente leitura, a página MUST oferecer um lápis para editar: no computador ao passar o mouse sobre a bolha, no celular ao tocar nela. A edição MUST usar o campo de mensagem com “Salvar” e “Cancelar”, com as mesmas regras de tamanho e textos de erro do envio.

#### Scenario: Lápis no computador
- **WHEN** a pessoa passa o mouse sobre uma mensagem própria editável
- **THEN** a página MUST mostrar o lápis com o rótulo acessível “Editar mensagem”
- **AND** o lápis MUST continuar alcançável pelo teclado

#### Scenario: Lápis no celular
- **WHEN** a pessoa toca numa mensagem própria editável num aparelho sem mouse
- **THEN** a página MUST mostrar o lápis dessa mensagem

#### Scenario: Mensagem não editável
- **WHEN** a mensagem é da outra pessoa, foi enviada há mais de 15 minutos ou a conversa está somente leitura
- **THEN** a página MUST NOT mostrar o lápis nessa mensagem

#### Scenario: Começar a editar
- **WHEN** a pessoa aciona o lápis
- **THEN** o campo de mensagem MUST receber o texto atual da mensagem, com o aviso “Editando mensagem” e os botões “Salvar” e “Cancelar” no lugar de “Enviar”

#### Scenario: Salvar a edição
- **WHEN** a pessoa aciona “Salvar” ou Enter com um texto válido
- **THEN** a página MUST enviar a edição, trocar o texto da bolha pelo novo, mostrar “(editada)” e voltar o campo ao modo de envio, vazio

#### Scenario: Cancelar a edição
- **WHEN** a pessoa aciona “Cancelar”
- **THEN** a página MUST voltar o campo ao modo de envio, vazio, sem chamar o backend e sem alterar a mensagem

#### Scenario: Edição recusada fora do prazo
- **WHEN** o backend responde HTTP 400 a uma edição de texto válido
- **THEN** a página MUST mostrar “Não foi possível editar. O prazo de 15 minutos terminou.” e esconder o lápis dessa mensagem
- **AND** MUST manter o texto digitado no campo

#### Scenario: Edição recusada com 404
- **WHEN** o backend responde HTTP 404 a uma edição
- **THEN** a página MUST mostrar “Não foi possível editar esta mensagem.” sem revelar o motivo e voltar o campo ao modo de envio

#### Scenario: Erros comuns ao envio
- **WHEN** a edição tem texto vazio, acima de 1000 caracteres ou recebe HTTP 429
- **THEN** a página MUST aplicar as mesmas regras e textos do envio, mantendo o texto no campo

#### Scenario: Edição em andamento
- **WHEN** uma edição está em andamento
- **THEN** “Salvar” MUST ficar desativado até a resposta

### Requirement: Indicação de mensagem editada
Toda mensagem editada MUST mostrar “(editada)” ao lado do horário de envio, para as duas pessoas, com o texto sempre como texto simples.

#### Scenario: Mensagem editada pela própria pessoa
- **WHEN** a edição é salva
- **THEN** a bolha MUST mostrar o texto novo e “(editada)” ao lado do horário

#### Scenario: Edição feita pela outra pessoa
- **WHEN** a outra pessoa edita uma mensagem já exibida e a conversa está aberta
- **THEN** a próxima atualização automática MUST trocar o texto da bolha e mostrar “(editada)”, sem requisição a mais

## MODIFIED Requirements

### Requirement: Atualização automática limitada
Com uma conversa aberta e a aba visível, a página MUST buscar mensagens novas em intervalos de no mínimo 15 segundos, pedindo só as posteriores à última recebida. A mesma consulta MUST trazer também a confirmação de leitura e as mensagens editadas desde a anterior. Com a aba visível, a lista de conversas MUST ser atualizada em intervalos de no mínimo 30 segundos, com ou sem conversa aberta. Com a aba oculta, MUST NOT fazer consultas automáticas. Não há atualização em tempo real.

#### Scenario: Conversa aberta e aba visível
- **WHEN** a conversa está aberta e a aba está visível
- **THEN** a página MUST consultar mensagens novas no máximo uma vez a cada 15 segundos e acrescentá-las sem duplicar as existentes

#### Scenario: Leitura e edições na mesma consulta
- **WHEN** a consulta automática da conversa responde
- **THEN** a página MUST atualizar o ✓✓ das próprias mensagens e o texto das mensagens editadas com os dados dessa resposta
- **AND** MUST NOT fazer requisição a mais para isso

#### Scenario: Atualização da lista
- **WHEN** a pessoa está em `/chat` com a aba visível
- **THEN** a página MUST consultar a primeira página da lista no máximo uma vez a cada 30 segundos, atualizando contadores, ordem e conversas novas
- **AND** MUST manter as conversas de páginas já carregadas com “Carregar mais conversas”, sem duplicá-las

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
