# Spec Delta

## Purpose

Permite consultar publicamente uma doação disponível e conhecer seus detalhes, suas fotos e a identificação pública mínima de quem doa.

## ADDED Requirements

### Requirement: Consulta pública de detalhe de doação disponível
O sistema MUST permitir consultar uma doação por identificador sem autenticação e MUST expor somente doações com status “disponível”.

#### Scenario: Consultar doação disponível
- **WHEN** uma pessoa consulta o detalhe de uma doação disponível sem sessão
- **THEN** o sistema MUST retornar os dados públicos necessários para o detalhe

#### Scenario: Doação inexistente ou indisponível
- **WHEN** o identificador não corresponde a uma doação ou a doação não está disponível
- **THEN** o sistema MUST responder com o mesmo erro HTTP 404 de doação não encontrada, sem revelar se ela existe ou qual é seu status
- **AND** a página MUST apresentar “Doação não encontrada” no estilo visual do site

### Requirement: Resposta pública limitada e sem dados privados
A resposta do detalhe MUST conter somente os dados da doação aprovados para exibição e MUST NOT expor dados privados de quem doa.

#### Scenario: Dados retornados para o detalhe
- **WHEN** uma consulta pública retorna uma doação disponível
- **THEN** a resposta MUST incluir identificador, título, descrição, condição, nome da categoria, modalidade de entrega, preferência de contato, cidade e UF, fotos ordenadas e primeiro nome de quem doa
- **AND** o primeiro nome MUST ser o único dado nominal de quem doa
- **AND** cidade e UF usadas no cartão de quem doa MUST corresponder à localização da doação

#### Scenario: Campos privados excluídos
- **WHEN** a resposta do detalhe é construída
- **THEN** ela MUST NOT conter e-mail, sobrenome, `owner_id`, endereço, bairro ou CEP de quem doa
- **AND** MUST NOT incluir dados adicionais da conta que não sejam necessários à página

### Requirement: Galeria ordenada da doação
O detalhe MUST apresentar a foto de capa seguida das fotos adicionais da doação em ordem crescente de posição e MUST NOT repetir uma imagem na galeria.

#### Scenario: Doação com capa e fotos adicionais
- **WHEN** a doação possui foto de capa e registros em `donation_photo`
- **THEN** a galeria MUST apresentar a capa primeiro e as fotos adicionais na ordem de posição

#### Scenario: Capa também registrada como foto adicional
- **WHEN** a mesma imagem armazenada como capa também aparece entre os registros de `donation_photo`
- **THEN** a galeria MUST apresentar essa imagem uma única vez, na posição da capa
- **AND** MUST manter as demais fotos adicionais na ordem de posição

#### Scenario: Doação sem fotos retornadas
- **WHEN** a doação não possui foto de capa nem fotos adicionais
- **THEN** a página MUST apresentar a imagem genérica de doação já utilizada nos cartões da home

### Requirement: Conteúdo do detalhe da doação
A página de detalhe MUST apresentar os dados existentes e aprovados da doação em uma única página, sem exibir campos ou ações fora do escopo.

#### Scenario: Exibir detalhes disponíveis
- **WHEN** uma pessoa abre uma doação disponível
- **THEN** a página MUST apresentar a galeria, o título, a condição com o rótulo “Condição”, a descrição, o nome da categoria, a cidade/UF, a modalidade de entrega, a preferência de contato como texto e o cartão de quem doa com somente primeiro nome e cidade/UF
- **AND** MUST NOT apresentar botões de chat, de outros meios de comunicação ou de acesso ao perfil do doador

#### Scenario: Não apresentar dados ou recursos indisponíveis
- **WHEN** a página exibe os detalhes da doação
- **THEN** MUST permanecerem ocultos Cor, Material, Tipo, bairro, CEP, avaliações, histórico de doações, presença online, indicadores de conta ou e-mail verificados e foto de perfil
- **AND** MUST NOT apresentar esses itens como “Em breve”

### Requirement: Estados e navegação do detalhe
A página MUST carregar o detalhe pela rota `/doacao/<id>`, validar o identificador antes da consulta e apresentar estados compreensíveis de carregamento e erro, respeitando movimento reduzido.

#### Scenario: Identificador de rota inválido
- **WHEN** o segmento `<id>` não representa um número inteiro positivo, como em `/doacao/abc`, `/doacao/0` ou `/doacao/-1`
- **THEN** a página MUST apresentar “Doação não encontrada”
- **AND** MUST NOT chamar o endpoint do Xano

#### Scenario: Carregamento da doação
- **WHEN** a página inicia a consulta do detalhe
- **THEN** ela MUST apresentar um estado de carregamento sem mostrar conteúdo fictício

#### Scenario: Falha de rede ou resposta inválida
- **WHEN** a consulta falha ou retorna dados inválidos
- **THEN** a página MUST apresentar uma mensagem de erro visualmente consistente com o site
- **AND** MUST NOT apresentar sucesso ou dados de outra doação

#### Scenario: Identificador válido sem correspondência
- **WHEN** o identificador é um número inteiro positivo, mas não corresponde a uma doação disponível, como em `/doacao/999999`
- **THEN** a página MUST consultar o Xano e apresentar “Doação não encontrada” quando o endpoint responder que não há doação disponível

#### Scenario: Entrada na página e movimento reduzido
- **WHEN** a página de detalhe é exibida
- **THEN** o conteúdo principal MUST usar a animação de entrada `page-fade-enter`
- **AND** a animação MUST ser desativada quando `prefers-reduced-motion` estiver ativo
- **AND** o cabeçalho e os dados carregados do Xano MUST NOT ser animados
