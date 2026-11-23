## MODIFIED Requirements

### Requirement: Página de edição da doação
A página `/minhas-doacoes/<id>/editar` MUST exigir login, carregar os campos da própria doação e salvar só os campos de texto, com as mesmas validações e opções do cadastro.

#### Scenario: Formulário preenchido
- **WHEN** a pessoa abre a edição de uma doação sua, disponível ou reservada
- **THEN** a página MUST mostrar título, descrição, categoria, condição, entrega e preferência de contato preenchidos com os valores atuais
- **AND** as opções MUST ser as do cadastro: todas as categorias válidas do backend, inclusive “Móveis”, “A combinar” e “E-mail” ou “Chat do DoaFácil”
- **AND** MUST NOT apresentar campo de fotos, cidade ou UF

#### Scenario: Valor atual fora das opções
- **WHEN** o valor atual da categoria, da entrega ou da preferência de contato não está entre as opções do cadastro, inclusive quando a categoria foi apagada do backend
- **THEN** o campo MUST aparecer vazio, e a pessoa MUST escolher uma opção válida para salvar

#### Scenario: Salvar com sucesso
- **WHEN** a pessoa salva valores válidos
- **THEN** a página MUST enviar a edição e voltar a `/minhas-doacoes`, com uma mensagem de sucesso

#### Scenario: Validação antes de enviar
- **WHEN** um campo obrigatório está vazio ou inválido
- **THEN** a página MUST indicar o campo a corrigir, MUST NOT enviar a requisição e MUST manter os valores digitados

#### Scenario: Falha ao salvar
- **WHEN** o Xano recusa a edição ou ocorre falha de rede ou HTTP 429
- **THEN** a página MUST mostrar uma mensagem de erro simples e manter os valores digitados

#### Scenario: Doação concluída, de outra pessoa ou inexistente
- **WHEN** o identificador da rota é inválido, a doação não é da pessoa ou não existe
- **THEN** a página MUST mostrar “Doação não encontrada” sem formulário
- **AND** para um identificador inválido, MUST NOT chamar o Xano
- **AND** para uma doação concluída da própria pessoa, MUST mostrar que ela não pode mais ser editada, sem formulário

#### Scenario: Voltar
- **WHEN** a página é exibida, em qualquer estado
- **THEN** a linha do logotipo MUST mostrar “Voltar a Minhas doações” em `#007A42`, levando a `/minhas-doacoes`
- **AND** o conteúdo MUST usar a animação de entrada `auth-card-enter` no cartão do formulário, desativada com `prefers-reduced-motion`

## ADDED Requirements

### Requirement: Tentar de novo em Minhas doações
Quando `/minhas-doacoes` não conseguir carregar a lista, a página SHALL mostrar, junto da mensagem de erro, o botão “Tentar de novo”, que busca a página outra vez sem sair dela.

#### Scenario: Falha ao carregar a lista
- **WHEN** a consulta das próprias doações falha, responde HTTP 429 ou devolve dados inválidos
- **THEN** a página MUST mostrar a mensagem de erro e o botão “Tentar de novo”, com área de toque de pelo menos 44 px, foco visível e contraste mínimo AA

#### Scenario: Tentar de novo com sucesso
- **WHEN** a pessoa aciona “Tentar de novo” e a consulta responde
- **THEN** a página MUST mostrar o estado de carregamento e, em seguida, o cartão da pessoa e a grade, sem recarregar o site
