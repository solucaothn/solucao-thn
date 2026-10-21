# Spec Delta

## MODIFIED Requirements

### Requirement: Detalhamento e categoria da doação
A interface MUST permitir informar título do objeto, descrição, uma categoria disponível e uma condição física entre “Ótimo”, “Bom” e “Regular”. O título, a categoria, a descrição e a condição MUST ser validados antes da publicação; a categoria selecionada MUST existir no Xano, e a lista exibida no wizard MUST excluir “Alimentos” e “Móveis”.

#### Scenario: Seleção de categoria disponível
- **WHEN** o formulário carrega as categorias ou o doador seleciona uma categoria
- **THEN** as opções apresentadas MUST corresponder às categorias retornadas pelo serviço de catálogo, exceto “Alimentos” e “Móveis”
- **AND** o filtro MUST ocorrer somente na interface, sem apagar categorias do Xano
- **AND** uma categoria inexistente MUST ser rejeitada pelo backend

#### Scenario: Condição selecionada no detalhamento
- **WHEN** o doador informa a condição do objeto
- **THEN** essa informação MUST ser coletada na segunda etapa e persistida com um dos três valores permitidos

### Requirement: Entrega e preferência de contato
A interface MUST apresentar “A combinar” como única modalidade de entrega selecionável e MUST manter as preferências “WhatsApp”, “E-mail” e “Chat do DoaFácil”. Esta change MUST persistir somente a preferência de contato e MUST NOT solicitar nem persistir telefone, endereço específico ou outro dado pessoal de contato.

#### Scenario: Publicação com entrega e preferência escolhidas
- **WHEN** o doador seleciona uma preferência de contato válida e a modalidade de entrega “A combinar”
- **THEN** ambas as escolhas MUST ser persistidas com a doação
- **AND** o frontend MUST enviar “A combinar”, valor aceito pelo endpoint de publicação existente

#### Scenario: Dados pessoais de contato não solicitados
- **WHEN** o doador preenche o passo de contato
- **THEN** a interface MUST apresentar apenas a escolha de preferência e MUST NOT solicitar número de telefone, endereço de contato ou identificador externo

## ADDED Requirements

### Requirement: Legibilidade dos textos de exemplo e seleção
A interface MUST apresentar placeholders e textos de seleção do cadastro de doação em cor preta ou cinza bem escura, legível sobre os fundos existentes, em todas as cinco etapas.

#### Scenario: Placeholders e prompts escuros
- **WHEN** qualquer etapa do cadastro apresenta texto de exemplo em campo ou um prompt de seleção, incluindo “Selecione uma categoria” e “Selecione a condição”
- **THEN** esses textos MUST usar cor escura equivalente a `#333333` ou mais escura

#### Scenario: Preferências de contato legíveis
- **WHEN** a quinta etapa apresenta o prompt e as opções de forma de contato
- **THEN** os textos “Selecione uma forma de contato”, “WhatsApp”, “E-mail” e “Chat do DoaFácil” MUST permanecer em cor escura legível, sem aparência apagada
