## MODIFIED Requirements

### Requirement: Listagem das próprias doações
O sistema MUST oferecer uma consulta autenticada que devolve, numa só requisição, uma página das doações da pessoa autenticada, de qualquer status, os contadores dela, o primeiro nome, o e-mail, se o e-mail está verificado, o texto de Sobre e a URL pública da foto de perfil. A pessoa é sempre derivada da sessão, nunca de um identificador enviado pelo cliente.

#### Scenario: Página das próprias doações
- **WHEN** uma pessoa autenticada pede uma página das suas doações
- **THEN** a resposta MUST trazer até 6 doações cadastradas por ela, de qualquer status, ordenadas por criação decrescente
- **AND** cada item MUST conter identificador, data de criação, título, foto como URL pública ou nula, condição e status
- **AND** a resposta MUST informar o número da página, o total de itens e o total de páginas

#### Scenario: Contadores na mesma resposta
- **WHEN** a consulta é respondida com sucesso
- **THEN** a resposta MUST incluir o contador de doações ativas, que soma as disponíveis e as reservadas, e o contador de doações concluídas
- **AND** os contadores MUST considerar todas as doações da pessoa, não só as da página pedida
- **AND** a resposta MUST incluir o primeiro nome da pessoa autenticada como único dado nominal
- **AND** a resposta MUST incluir o texto de Sobre da pessoa autenticada, vazio ou nulo quando não preenchido
- **AND** a resposta MUST incluir a URL pública da foto de perfil da pessoa autenticada, nula quando não há foto
- **AND** a resposta MUST incluir o e-mail da pessoa autenticada e se ele está verificado, como verdadeiro ou falso

#### Scenario: Somente dados da própria pessoa
- **WHEN** a consulta é respondida
- **THEN** ela MUST NOT conter doações, nomes, e-mails ou identificadores de outras pessoas
- **AND** o único e-mail da resposta MUST ser o da própria pessoa autenticada
- **AND** MUST NOT conter sobrenome, `owner_id` nem id de usuário

#### Scenario: Página inválida ou fora do intervalo
- **WHEN** a página pedida é menor que 1 ou maior que o total de páginas
- **THEN** o sistema MUST tratar uma página menor que 1 como a página 1
- **AND** para uma página além da última, MUST devolver a lista vazia com os totais corretos, sem erro

#### Scenario: Consulta sem sessão válida
- **WHEN** uma pessoa sem sessão válida faz a consulta
- **THEN** o endpoint MUST responder HTTP 401 sem retornar dados

### Requirement: Página Minhas doações
A página `/minhas-doacoes` MUST exigir login e apresentar o cartão da pessoa e a grade das suas doações, seguindo o frame `Group 6` do Figma com as diferenças registradas em `docs/design/README.md`.

#### Scenario: Acesso sem login
- **WHEN** uma pessoa sem sessão válida abre `/minhas-doacoes` ou recebe HTTP 401 durante o uso
- **THEN** a página MUST levar a `/login` sem mostrar dados

#### Scenario: Cabeçalho e título
- **WHEN** a página é exibida, em qualquer estado
- **THEN** a linha do logotipo MUST mostrar, à esquerda, “Voltar ao início” em `#007A42`, com rótulo acessível e área de toque de pelo menos 44 px, levando a `/`
- **AND** o título “Minhas doações” MUST aparecer à esquerda, em negrito e verde

#### Scenario: Cartão da pessoa
- **WHEN** a página carrega com sucesso
- **THEN** MUST mostrar a foto de perfil da pessoa, redonda, com `object-fit: cover` e texto alternativo com o primeiro nome, ou, sem foto, um círculo com a inicial, no mesmo tamanho; o primeiro nome, “Doações” com o contador de ativas e “Doações realizadas” com o contador de concluídas
- **AND** MUST mostrar o e-mail da pessoa abaixo do primeiro nome, inteiro, quebrando a linha quando não couber, sem rolagem horizontal
- **AND** MUST mostrar o selo “E-mail verificado” somente quando o e-mail da pessoa está verificado
- **AND** MUST mostrar o botão “Editar perfil”, que leva a `/perfil/editar`, com área de toque de pelo menos 44 px
- **AND** quando a pessoa preencheu o Sobre, MUST mostrá-lo como texto simples, preservando as quebras de linha; com o Sobre vazio, MUST NOT mostrar nada no lugar dele
- **AND** MUST NOT apresentar “Compartilhar”, avaliações ou botão de chat, nem como “Em breve”

#### Scenario: Grade das doações
- **WHEN** a pessoa tem doações
- **THEN** a página MUST mostrar até 6 cartões por página, das mais novas para as mais antigas, cada um com foto (ou a imagem genérica), título, a linha “Condição: …”, selo de status e menu de ações
- **AND** o selo MUST dizer “Disponível”, “Reservada” ou “Concluída”, com cores de contraste AA e o texto como informação principal, não só a cor
- **AND** só os cartões de doações disponíveis MUST ter o link “Ver anúncio”, que leva a `/doacao/<id>`
- **AND** os cartões MUST NOT mostrar o selo NOVO

#### Scenario: Paginação
- **WHEN** a pessoa tem mais de 6 doações
- **THEN** a página MUST mostrar “Anterior”, “Próxima” e “Página N de M”, com “Anterior” desativado na primeira página e “Próxima” na última
- **AND** trocar de página MUST fazer uma requisição só para a página pedida
- **AND** com até 6 doações, MUST NOT mostrar os controles

#### Scenario: Sem doações
- **WHEN** a pessoa não tem nenhuma doação
- **THEN** a página MUST mostrar “Você ainda não tem doações” e o botão “Quero Doar”, que leva a `/cadastro-doacao`
- **AND** MUST NOT mostrar a paginação

#### Scenario: Carregamento e erro
- **WHEN** a página consulta o Xano
- **THEN** MUST mostrar um estado de carregamento sem conteúdo fictício
- **AND** numa falha de rede, resposta inválida ou HTTP 429, MUST mostrar uma mensagem de erro simples, sem dados parciais

#### Scenario: Layout, contraste e movimento
- **WHEN** a página é exibida numa largura de 360 px
- **THEN** o cartão da pessoa e os cartões de doação MUST aparecer em uma coluna, sem rolagem horizontal
- **AND** todos os textos, selos e controles MUST ter contraste mínimo AA
- **AND** o conteúdo principal MUST usar `page-fade-enter`, desativada com `prefers-reduced-motion`, sem animar o cabeçalho nem os dados carregados do Xano
