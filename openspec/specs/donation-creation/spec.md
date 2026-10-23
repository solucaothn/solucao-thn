# donation-creation Specification

## Purpose

Define o fluxo autenticado para cadastrar e publicar uma doação física, reunindo os dados do item, sua localização e entrega, fotos e a preferência de contato, com persistência validada pelo Xano.

## Requirements

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
O sistema MUST permitir informar título do objeto, descrição, uma categoria existente e uma condição física entre “Ótimo”, “Bom” e “Regular”. O campo de título MUST apresentar o exemplo “Ex.: Carrinho de brinquedo”. O título, a categoria, a descrição e a condição MUST ser validados antes da publicação; a categoria MUST existir no Xano, e a lista exibida no wizard MUST excluir “Alimentos” e “Móveis”.

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
- **THEN** o sistema MUST identificar a falha, permitir correção ou nova tentativa e MUST não apresentar a doação como publicada

### Requirement: Entrega e preferência de contato
O sistema MUST apresentar “A combinar” como única modalidade de entrega selecionável e MUST oferecer somente as preferências “E-mail” e “Chat do DoaFácil”. Esta change MUST persistir somente a preferência de contato e MUST NOT solicitar nem persistir telefone, endereço específico ou outro dado pessoal de contato.

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

### Requirement: Reinício do formulário a cada nova entrada
Cada nova entrada em `/cadastro-doacao` MUST iniciar um novo cadastro vazio e habilitado, limpando os dados e estados temporários da visita anterior antes de carregar as categorias e a localização do perfil.

#### Scenario: Nova entrada após publicar uma doação
- **WHEN** a pessoa publica uma doação com sucesso e depois entra novamente em `/cadastro-doacao`
- **THEN** o formulário MUST voltar ao passo 1 com título, descrição, categoria, condição, forma de entrega e preferência de contato vazios
- **AND** MUST limpar mensagens de erro e sucesso, estado de publicação e progresso de upload
- **AND** MUST limpar os arquivos selecionados no componente de upload

#### Scenario: Troca de conta na mesma aba
- **WHEN** a pessoa publica uma doação, sai da conta, entra com outra conta na mesma aba e abre `/cadastro-doacao`
- **THEN** o formulário MUST iniciar vazio no passo 1, sem dados ou estado de publicação da conta anterior
- **AND** MUST carregar categorias e cidade/UF do perfil da conta atualmente autenticada

#### Scenario: Recarregar a página de cadastro
- **WHEN** a pessoa recarrega `/cadastro-doacao`
- **THEN** o formulário MUST iniciar vazio no passo 1, limpando também os arquivos selecionados
- **AND** MUST carregar categorias e cidade/UF do perfil autenticado

#### Scenario: Publicação concluída na visita atual
- **WHEN** a publicação é concluída com sucesso e a pessoa permanece na mesma visita de `/cadastro-doacao`
- **THEN** o formulário MUST manter o aviso de sucesso e o estado que impede uma segunda publicação
- **AND** a reinicialização MUST ocorrer somente na próxima entrada na página

#### Scenario: Navegação entre os passos preserva os dados
- **WHEN** a pessoa usa “Continuar” e “Voltar” para navegar entre os passos dentro de `/cadastro-doacao`
- **THEN** o sistema MUST NOT reiniciar o formulário durante essa navegação
- **AND** os dados preenchidos nos passos anteriores MUST permanecer preenchidos ao retornar a eles
- **AND** o reinício MUST ocorrer somente na entrada da página, inclusive ao recarregá-la
