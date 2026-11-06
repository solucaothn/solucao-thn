# Delta da especificação

## MODIFIED Requirements

### Requirement: Seleção de fotos da doação
O sistema MUST permitir selecionar de uma a cinco imagens aceitas para uma doação e MUST informar visualmente o progresso de cada arquivo enquanto ele é processado. Arquivos que não sejam formatos de imagem aceitos pelo armazenamento do Xano, incluindo documentos PDF, MUST ser rejeitados com mensagem compreensível. O doador MUST selecionar pelo menos uma foto para avançar da etapa 3 e publicar pelo wizard, e o backend MUST também rejeitar publicações sem fotos.

#### Scenario: Avanço com ao menos uma foto
- **WHEN** o doador seleciona uma imagem aceita
- **AND** clica em “Continuar” na etapa 3
- **THEN** o wizard MUST avançar para a etapa 4

#### Scenario: Tentativa de avançar sem fotos
- **WHEN** o doador clica em “Continuar” na etapa 3 sem selecionar arquivos
- **THEN** o wizard MUST permanecer na etapa 3
- **AND** MUST apresentar a mensagem “Adicione pelo menos uma foto para continuar.”

#### Scenario: Seleção dentro do limite
- **WHEN** o doador seleciona até cinco imagens aceitas
- **THEN** o sistema MUST apresentar a quantidade e o progresso dos arquivos e enviar suas referências para persistência na publicação

#### Scenario: Tentativa de ultrapassar o limite
- **WHEN** o doador tenta manter mais de cinco imagens selecionadas
- **THEN** o sistema MUST impedir a seleção excedente, informar o limite e manter os arquivos já aceitos

#### Scenario: Arquivo não aceito ou falha no upload
- **WHEN** um arquivo não é uma imagem aceita ou o upload falha
- **THEN** o sistema MUST identificar a falha, permitir correção ou nova tentativa e MUST NOT apresentar a doação como publicada

#### Scenario: Publicação sem fotos pelo endpoint
- **WHEN** uma requisição autenticada ao endpoint de publicação contém `photos` ausente, nulo ou vazio
- **THEN** o backend MUST rejeitar a requisição com erro `inputerror` (HTTP 400) e a mensagem “Adicione pelo menos uma foto para continuar.”
- **AND** MUST NOT criar uma doação, linhas de fotos associadas ou arquivos de imagem sem dono

### Requirement: Publicação autenticada e persistente
O sistema MUST publicar a doação por meio de uma operação autenticada no Xano. O backend MUST derivar o responsável da sessão autenticada, validar a categoria, a condição, a modalidade de entrega, a preferência de contato e o limite de uma a cinco fotos, e persistir os dados completos. Uma publicação aceita MUST iniciar com status “disponível”. Falhas de validação, autenticação, rede ou persistência MUST ser informadas sem apagar os dados ainda não publicados nem exibir uma confirmação de sucesso.

#### Scenario: Publicação aceita
- **WHEN** uma pessoa autenticada envia dados válidos e o Xano conclui a persistência
- **THEN** a resposta MUST identificar a doação criada, associada ao usuário autenticado, com status “disponível” e com os dados submetidos

#### Scenario: Requisição sem sessão válida
- **WHEN** uma pessoa não autenticada tenta publicar uma doação
- **THEN** o backend MUST rejeitar a requisição sem criar uma doação nem aceitar um responsável informado pelo cliente

#### Scenario: Falha durante a publicação
- **WHEN** o Xano rejeita a requisição ou ocorre uma falha de rede/persistência
- **THEN** a interface MUST apresentar uma mensagem de erro, manter os valores do wizard e MUST NOT mostrar a doação como publicada

#### Scenario: Xano rejeita publicação sem fotos
- **WHEN** o backend rejeita a publicação por não receber fotos
- **THEN** a interface MUST apresentar “Adicione pelo menos uma foto para continuar.” e manter os valores do wizard
- **AND** MUST NOT mostrar a doação como publicada
