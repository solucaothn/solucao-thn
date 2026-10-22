# Spec Delta

## MODIFIED Requirements

### Requirement: Seleção de fotos da doação
O sistema MUST permitir selecionar de uma a cinco imagens aceitas para uma doação e MUST informar visualmente o progresso de cada arquivo enquanto ele é processado. Arquivos que não sejam formatos de imagem aceitos pelo armazenamento do Xano, incluindo documentos PDF, MUST ser rejeitados com mensagem compreensível. O doador MUST selecionar pelo menos uma foto para avançar da etapa 3 e publicar pelo wizard, ainda que o endpoint Xano aceite requisições sem fotos.

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

### Requirement: Detalhamento e categoria da doação
A interface MUST permitir informar título do objeto, descrição, uma categoria disponível e uma condição física entre “Ótimo”, “Bom” e “Regular”. O campo de título MUST apresentar o exemplo “Ex.: Carrinho de brinquedo”. O título, a categoria, a descrição e a condição MUST ser validados antes da publicação; a categoria selecionada MUST existir no Xano, e a lista exibida no wizard MUST excluir “Alimentos” e “Móveis”.

#### Scenario: Seleção de categoria disponível
- **WHEN** o formulário carrega as categorias ou o doador seleciona uma categoria
- **THEN** as opções apresentadas MUST corresponder às categorias retornadas pelo serviço de catálogo, exceto “Alimentos” e “Móveis”
- **AND** o filtro MUST ocorrer somente na interface, sem apagar categorias do Xano
- **AND** uma categoria inexistente MUST ser rejeitada pelo backend

#### Scenario: Exemplo do nome do item
- **WHEN** o doador visualiza o campo “Nome do item” na primeira etapa
- **THEN** o campo MUST mostrar o placeholder “Ex.: Carrinho de brinquedo”

#### Scenario: Condição selecionada no detalhamento
- **WHEN** o doador informa a condição do objeto
- **THEN** essa informação MUST ser coletada na segunda etapa e persistida com um dos três valores permitidos

### Requirement: Entrega e preferência de contato
A interface MUST apresentar “A combinar” como única modalidade de entrega selecionável e MUST oferecer somente as preferências “E-mail” e “Chat do DoaFácil”. Esta change MUST persistir somente a preferência de contato e MUST NOT solicitar nem persistir telefone, endereço específico ou outro dado pessoal de contato.

#### Scenario: Publicação com entrega e preferência escolhidas
- **WHEN** o doador seleciona uma preferência de contato válida e a modalidade de entrega “A combinar”
- **THEN** ambas as escolhas MUST ser persistidas com a doação
- **AND** o frontend MUST enviar “A combinar”, valor aceito pelo endpoint de publicação existente
- **AND** a preferência MUST ser “E-mail” ou “Chat do DoaFácil”, ambos aceitos pelo endpoint existente

#### Scenario: Opção de contato removida
- **WHEN** o doador escolhe uma preferência de contato
- **THEN** a interface MUST oferecer “E-mail” e “Chat do DoaFácil” e MUST NOT oferecer “WhatsApp”

#### Scenario: Dados pessoais de contato não solicitados
- **WHEN** o doador preenche o passo de contato
- **THEN** a interface MUST apresentar apenas a escolha de preferência e MUST NOT solicitar número de telefone, endereço de contato ou identificador externo

## ADDED Requirements

### Requirement: Legibilidade dos textos de exemplo e seleção
A interface MUST apresentar placeholders e textos de seleção do cadastro de doação em cor preta ou cinza bem escura, legível sobre os fundos existentes, em todas as cinco etapas.

#### Scenario: Placeholders e prompts escuros
- **WHEN** qualquer etapa do cadastro apresenta texto de exemplo em campo ou um prompt de seleção, incluindo “Selecione uma categoria” e “Selecione a condição”
- **THEN** esses textos MUST usar cor escura equivalente a `#333333` ou mais escura
- **AND** o placeholder de um Select do Radix MUST manter essa cor no elemento de conteúdo interno marcado pelo estado de placeholder, sem alterar o fundo do controle
- **AND** a regra MUST NOT alterar a aparência das opções na lista aberta

#### Scenario: Preferências de contato legíveis
- **WHEN** a quinta etapa apresenta o prompt e as opções de forma de contato
- **THEN** os textos “Selecione uma forma de contato”, “E-mail” e “Chat do DoaFácil” MUST permanecer em cor escura legível, sem aparência apagada
