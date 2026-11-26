## ADDED Requirements

### Requirement: Carregamento visível nas ações da lista e do histórico
Ao acionar “Atualizar conversas”, “Tentar de novo” na falha da lista, “Carregar mais conversas” ou “Carregar anteriores”, a página MUST mostrar o estado de carregamento desde o acionamento, antes do pedido ao backend, e desligá-lo quando a resposta chegar, com sucesso ou falha. Cada acionamento MUST fazer um único pedido.

#### Scenario: Atualizar ou tentar de novo a lista
- **WHEN** a pessoa aciona “Atualizar conversas” ou o “Tentar de novo” da falha da lista
- **THEN** o botão de atualizar MUST aparecer desativado, com o carregamento, antes da resposta do backend
- **AND** depois da resposta, MUST voltar ao normal

#### Scenario: Carregar mais conversas ou mensagens anteriores
- **WHEN** a pessoa aciona “Carregar mais conversas” ou “Carregar anteriores”
- **THEN** o botão acionado MUST aparecer desativado antes da resposta do backend
- **AND** um segundo clique durante a espera MUST NOT buscar a mesma página de novo

### Requirement: Rótulo do botão da falha da lista
Quando a lista de conversas não puder ser carregada, o botão para buscá-la outra vez MUST ter o texto “Tentar de novo”, como nas outras páginas do site.

#### Scenario: Falha da lista
- **WHEN** a consulta de conversas falha
- **THEN** a página MUST mostrar a mensagem de erro e o botão “Tentar de novo”, que busca a lista outra vez

## MODIFIED Requirements

### Requirement: Envio de mensagem
A página MUST permitir enviar uma mensagem pelo campo “Digite aqui...”, com o botão “Enviar” ou a tecla Enter. A interface MUST impedir o envio de texto vazio e de texto acima de 1000 caracteres, e MUST traduzir as recusas do backend em mensagens amigáveis, sem apagar o texto digitado.

#### Scenario: Envio aceito
- **WHEN** a pessoa digita um texto válido e aciona “Enviar” ou Enter
- **THEN** a página MUST enviar a mensagem, mostrá-la no fim da conversa e limpar o campo

#### Scenario: Texto vazio
- **WHEN** a pessoa aciona o envio com o campo vazio ou só com espaços
- **THEN** a página MUST NOT chamar o endpoint de envio

#### Scenario: Recusa por tamanho
- **WHEN** o backend responde HTTP 400 ao envio
- **THEN** a página MUST mostrar “A mensagem precisa ter entre 1 e 1000 caracteres.” e manter o texto no campo

#### Scenario: Limite de envio do chat atingido
- **WHEN** o backend responde HTTP 429 ao envio com a mensagem do chat “Limite de mensagens atingido”
- **THEN** a página MUST mostrar “Você enviou muitas mensagens em pouco tempo. Aguarde um minuto.” e manter o texto no campo

#### Scenario: Limite da plataforma atingido no envio
- **WHEN** o backend responde HTTP 429 ao envio com o código `ERROR_CODE_TOO_MANY_REQUESTS` e outra mensagem
- **THEN** a página MUST mostrar “O site está com muitos acessos agora. Tente de novo em instantes.” e manter o texto no campo

#### Scenario: Envio recusado com 404
- **WHEN** o backend responde HTTP 404 ao envio
- **THEN** a página MUST mostrar “Não foi possível enviar. Esta conversa não está mais disponível para novas mensagens.” sem revelar o motivo

#### Scenario: Envio em andamento
- **WHEN** um envio está em andamento
- **THEN** o botão “Enviar” MUST ficar desativado desde o acionamento, antes do pedido ao backend, até a resposta
- **AND** o campo MUST continuar ativo, com o texto digitado

#### Scenario: Enter repetido durante o envio
- **WHEN** a pessoa aciona “Enviar” ou Enter e, com o envio em andamento, aperta Enter de novo
- **THEN** a mensagem MUST ser enviada ao backend uma única vez e aparecer uma única vez na conversa

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
- **WHEN** a pessoa aciona “Cancelar” ou aperta Esc no campo durante a edição
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
- **THEN** “Salvar” MUST ficar desativado desde o acionamento, antes do pedido ao backend, até a resposta
- **AND** um Enter repetido durante a edição MUST NOT enviar a edição de novo
