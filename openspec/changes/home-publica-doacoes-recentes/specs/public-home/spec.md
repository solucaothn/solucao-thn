# Spec Delta

## Purpose

Define a apresentação da página inicial pública do DoaFácil e como seus elementos exibem a contagem e as doações disponíveis obtidas do backend.

## ADDED Requirements

### Requirement: Apresentação da home pública
A home SHALL apresentar o cabeçalho, a frase de destaque, a estatística “Doações em circulação” e a seção “Doações mais recentes” conforme as referências do design, além da ilustração aprovada no rodapé quando o recurso estiver disponível.

#### Scenario: Abrir a home sem autenticação
- **WHEN** uma pessoa acessa a página inicial sem sessão
- **THEN** a página apresenta o logotipo, os links Explorar Doações, Como funciona e Categorias, os botões Entrar e Quero Doar, a frase de destaque, a estatística e a seção de doações recentes
- **AND** não exibe a estatística “Pessoas alcançadas”
- **AND** apresenta a ilustração aprovada no rodapé quando o recurso estiver disponível

#### Scenario: Ilustração do rodapé ainda indisponível
- **WHEN** o recurso aprovado da ilustração de pessoas ainda não está disponível no projeto
- **THEN** a home omite a ilustração sem criar um substituto e o código mantém um TODO para adicioná-la quando o recurso chegar

### Requirement: Exibição da contagem em circulação
A home SHALL apresentar na estatística “Doações em circulação” a quantidade retornada pelo serviço público de contagem de doações disponíveis.

#### Scenario: Contagem retornada pelo backend
- **WHEN** o serviço retorna uma quantidade de doações disponíveis
- **THEN** a home exibe esse valor junto ao rótulo “Doações em circulação”

#### Scenario: Falha ao carregar a contagem
- **WHEN** o serviço de contagem falha
- **THEN** a home informa que a contagem não pôde ser carregada e não apresenta um valor fictício como se fosse a contagem real

#### Scenario: URL base do Xano não configurada
- **WHEN** `XANO_API_URL` está ausente ou não contém uma URL HTTP(S) válida
- **THEN** a home informa que não foi possível conectar ao Xano para cada seção afetada
- **AND** não apresenta uma contagem ou uma lista de doações fictícias

### Requirement: Cartões de doações recentes
A home SHALL exibir os dados retornados para cada doação recente com título, condição, botão “Acessar” e uma imagem.

#### Scenario: Doação com foto e condição
- **WHEN** uma doação recente possui foto e condição
- **THEN** o cartão exibe a foto, o título e a condição com o rótulo “Condição”
- **AND** exibe o botão “Acessar” sem navegar para outra página quando acionado

#### Scenario: Doação sem foto
- **WHEN** uma doação recente não possui foto
- **THEN** o cartão exibe uma imagem genérica no lugar da foto

#### Scenario: Doação sem condição
- **WHEN** uma doação recente não possui condição
- **THEN** o cartão exibe “Condição não informada”

#### Scenario: Marcação de doação nova
- **WHEN** a data de criação da doação está dentro dos últimos sete dias
- **THEN** o cartão exibe a etiqueta “NOVO”

#### Scenario: Doação fora do período de novidade
- **WHEN** a data de criação da doação tem mais de sete dias
- **THEN** o cartão não exibe a etiqueta “NOVO”

#### Scenario: Nenhuma doação recente
- **WHEN** o serviço retorna uma lista vazia
- **THEN** a home mantém os demais elementos e informa que ainda não há doações disponíveis para exibição

#### Scenario: Falha ao carregar as doações recentes
- **WHEN** o serviço de listagem falha
- **THEN** a home informa que as doações recentes não puderam ser carregadas e não apresenta cartões fictícios
