## Purpose

Define o fluxo autenticado para cadastrar e publicar uma doação física, reunindo os dados do item, sua localização e entrega, fotos e a preferência de contato, com persistência validada pelo Xano.

## ADDED Requirements

### Requirement: Cadastro de doação em cinco etapas
O sistema MUST permitir que uma pessoa autenticada preencha um cadastro de doação dividido em cinco etapas, na ordem definida pela interface: título do objeto; descrição, categoria e condição; fotos; entrega e localização; preferência de contato e publicação. O indicador de progresso MUST mostrar a etapa atual de cinco. A localização apresentada e persistida MUST ser a cidade e a UF do perfil autenticado do doador no momento da publicação; o formulário não MUST solicitar um endereço específico.

#### Scenario: Entrada no cadastro pela página inicial
- **WHEN** uma pessoa seleciona “Quero Doar” na página inicial
- **THEN** o sistema MUST abrir `/cadastro-doacao` e direcionar pessoas sem sessão válida ao login

#### Scenario: Navegação entre etapas
- **WHEN** o doador avança ou retorna entre etapas
- **THEN** a interface MUST atualizar o indicador para “Passo X de 5” e preservar os valores já informados

#### Scenario: Avanço com dados obrigatórios ausentes
- **WHEN** o doador tenta avançar sem preencher um campo obrigatório da etapa
- **THEN** o sistema MUST indicar o campo que precisa ser corrigido e MUST permanecer na etapa atual

#### Scenario: Localização copiada do perfil
- **WHEN** a doação é publicada
- **THEN** a cidade e a UF associadas à doação MUST corresponder aos dados do perfil autenticado no momento da publicação, sem aceitar localização arbitrária enviada pelo cliente

### Requirement: Detalhamento e categoria da doação
O sistema MUST permitir informar título do objeto, descrição, uma categoria existente e uma condição física entre “Ótimo”, “Bom” e “Regular”. O título, a categoria, a descrição e a condição MUST ser validados antes da publicação; a categoria MUST existir no Xano.

#### Scenario: Seleção de categoria disponível
- **WHEN** o formulário carrega as categorias ou o doador seleciona uma categoria
- **THEN** as opções MUST corresponder às categorias retornadas pelo serviço de catálogo e uma categoria inexistente MUST ser rejeitada pelo backend

#### Scenario: Condição selecionada no detalhamento
- **WHEN** o doador informa a condição do objeto
- **THEN** essa informação MUST ser coletada na segunda etapa e persistida com um dos três valores permitidos

### Requirement: Seleção de fotos da doação
O sistema MUST permitir selecionar até cinco arquivos de imagem para uma doação e MUST informar visualmente o progresso de cada arquivo enquanto ele é processado. Arquivos que não sejam formatos de imagem aceitos pelo armazenamento do Xano, incluindo documentos PDF, MUST ser rejeitados com mensagem compreensível. A ausência de fotos MUST não impedir a publicação.

#### Scenario: Seleção dentro do limite
- **WHEN** o doador seleciona até cinco imagens aceitas
- **THEN** o sistema MUST apresentar a quantidade e o progresso dos arquivos e enviar suas referências para persistência na publicação

#### Scenario: Tentativa de ultrapassar o limite
- **WHEN** o doador tenta manter mais de cinco imagens selecionadas
- **THEN** o sistema MUST impedir a seleção excedente, informar o limite e manter os arquivos já aceitos

#### Scenario: Arquivo não aceito ou falha no upload
- **WHEN** um arquivo não é uma imagem aceita ou o upload falha
- **THEN** o sistema MUST identificar a falha, permitir correção ou nova tentativa e MUST não apresentar a doação como publicada

### Requirement: Entrega e preferência de contato
O sistema MUST permitir escolher uma modalidade de entrega entre “Retirada”, “Entrega” e “A combinar”, além de uma preferência entre “WhatsApp”, “E-mail” e “Chat do DoaFácil”. Esta change MUST persistir somente a preferência de contato e MUST NOT solicitar nem persistir telefone, endereço específico ou outro dado pessoal de contato.

#### Scenario: Publicação com entrega e preferência escolhidas
- **WHEN** o doador seleciona uma modalidade de entrega e uma preferência de contato válidas
- **THEN** ambas as escolhas MUST ser persistidas com a doação

#### Scenario: Dados pessoais de contato não solicitados
- **WHEN** o doador preenche o passo de contato
- **THEN** a interface MUST apresentar apenas a escolha de preferência e MUST NOT solicitar número de telefone, endereço de contato ou identificador externo

### Requirement: Publicação autenticada e persistente
O sistema MUST publicar a doação por meio de uma operação autenticada no Xano. O backend MUST derivar o responsável da sessão autenticada, validar a categoria, a condição, a modalidade de entrega, a preferência de contato e o limite de fotos, e persistir os dados completos. Uma publicação aceita MUST iniciar com status “disponível”. Falhas de validação, autenticação, rede ou persistência MUST ser informadas sem apagar os dados ainda não publicados nem exibir uma confirmação de sucesso.

#### Scenario: Publicação aceita
- **WHEN** uma pessoa autenticada envia dados válidos e o Xano conclui a persistência
- **THEN** a resposta MUST identificar a doação criada, associada ao usuário autenticado, com status “disponível” e com os dados submetidos

#### Scenario: Requisição sem sessão válida
- **WHEN** uma pessoa não autenticada tenta publicar uma doação
- **THEN** o backend MUST rejeitar a requisição sem criar uma doação nem aceitar um responsável informado pelo cliente

#### Scenario: Falha durante a publicação
- **WHEN** o Xano rejeita a requisição ou ocorre uma falha de rede/persistência
- **THEN** a interface MUST apresentar uma mensagem de erro, manter os valores do wizard e MUST NOT mostrar a doação como publicada
