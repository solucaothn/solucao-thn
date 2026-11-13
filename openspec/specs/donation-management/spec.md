# donation-management Specification

## Purpose
Permite que quem doa veja todas as próprias doações, com o status e os contadores, e as gerencie: muda o status, corrige os campos de texto e apaga. O backend garante que cada pessoa só lê e altera as doações que cadastrou.

## Requirements

### Requirement: Listagem das próprias doações
O sistema MUST oferecer uma consulta autenticada que devolve, numa só requisição, uma página das doações da pessoa autenticada, de qualquer status, os contadores dela e o primeiro nome. A pessoa é sempre derivada da sessão, nunca de um identificador enviado pelo cliente.

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

#### Scenario: Somente dados da própria pessoa
- **WHEN** a consulta é respondida
- **THEN** ela MUST NOT conter doações, nomes, e-mails ou identificadores de outras pessoas
- **AND** MUST NOT conter e-mail, sobrenome, `owner_id` nem id de usuário

#### Scenario: Página inválida ou fora do intervalo
- **WHEN** a página pedida é menor que 1 ou maior que o total de páginas
- **THEN** o sistema MUST tratar uma página menor que 1 como a página 1
- **AND** para uma página além da última, MUST devolver a lista vazia com os totais corretos, sem erro

#### Scenario: Consulta sem sessão válida
- **WHEN** uma pessoa sem sessão válida faz a consulta
- **THEN** o endpoint MUST responder HTTP 401 sem retornar dados

### Requirement: Leitura de uma doação própria para edição
O sistema MUST oferecer uma consulta autenticada que devolve os campos editáveis de uma doação da pessoa autenticada, de qualquer status. Uma doação inexistente ou de outra pessoa MUST receber o mesmo erro 404 genérico.

#### Scenario: Ler a própria doação
- **WHEN** a pessoa autenticada consulta uma doação que cadastrou
- **THEN** a resposta MUST conter identificador, título, descrição, identificador da categoria, condição, modalidade de entrega, preferência de contato e status
- **AND** MUST NOT conter e-mail, `owner_id` nem id de usuário

#### Scenario: Doação inexistente ou de outra pessoa
- **WHEN** o identificador não corresponde a uma doação da pessoa autenticada
- **THEN** o endpoint MUST responder HTTP 404 com a mesma mensagem genérica de doação não encontrada
- **AND** MUST NOT revelar se a doação existe nem quem a cadastrou

#### Scenario: Leitura sem sessão válida
- **WHEN** uma pessoa sem sessão válida faz a consulta
- **THEN** o endpoint MUST responder HTTP 401 sem retornar dados

### Requirement: Mudança de status pela pessoa dona
Somente a pessoa dona MUST poder mudar o status da doação. As transições permitidas são de disponível para reservada, de reservada para disponível, e de disponível ou reservada para concluída. Uma doação concluída MUST NOT mudar de status.

#### Scenario: Reservar uma doação disponível
- **WHEN** a pessoa dona marca uma doação disponível como reservada
- **THEN** o sistema MUST gravar o status “reservada”

#### Scenario: Voltar uma doação reservada a disponível
- **WHEN** a pessoa dona marca uma doação reservada como disponível
- **THEN** o sistema MUST gravar o status “disponível”
- **AND** a doação MUST voltar a aparecer na home, no detalhe e no perfil público

#### Scenario: Concluir uma doação
- **WHEN** a pessoa dona marca uma doação disponível ou reservada como concluída
- **THEN** o sistema MUST gravar o status “concluída”
- **AND** as conversas dessa doação MUST passar a ser somente leitura, como já define o chat

#### Scenario: Doação concluída não muda
- **WHEN** a pessoa dona tenta mudar o status de uma doação concluída
- **THEN** o endpoint MUST responder HTTP 400 sem alterar a doação

#### Scenario: Pessoa que não é dona
- **WHEN** uma pessoa autenticada tenta mudar o status de uma doação de outra pessoa
- **THEN** o endpoint MUST recusar a requisição sem alterar a doação

### Requirement: Edição dos campos de texto da doação
Somente a pessoa dona MUST poder editar título, descrição, categoria, condição, modalidade de entrega e preferência de contato de uma doação disponível ou reservada. O backend MUST aplicar as validações da publicação. Fotos, cidade, UF e status MUST NOT mudar pela edição.

#### Scenario: Edição válida
- **WHEN** a pessoa dona envia valores válidos para uma doação disponível ou reservada
- **THEN** o sistema MUST gravar os seis campos e manter as fotos, a cidade, a UF e o status
- **AND** a resposta MUST NOT conter e-mail, `owner_id` nem id de usuário

#### Scenario: Valores inválidos
- **WHEN** o título ou a descrição ficam vazios depois de tirar os espaços das pontas, o título passa de 100 caracteres, a descrição passa de 2000, a categoria não existe, a condição não é “Ótimo”, “Bom” ou “Regular”, a entrega não é “A combinar” ou a preferência não é “E-mail” ou “Chat do DoaFácil”
- **THEN** o endpoint MUST responder HTTP 400 sem alterar a doação

#### Scenario: Edição de doação concluída
- **WHEN** a pessoa dona tenta editar uma doação concluída
- **THEN** o endpoint MUST responder HTTP 400 sem alterar a doação

#### Scenario: Pessoa que não é dona
- **WHEN** uma pessoa autenticada tenta editar uma doação de outra pessoa ou inexistente
- **THEN** o endpoint MUST recusar a requisição sem alterar nenhuma doação

### Requirement: Exclusão da própria doação
Somente a pessoa dona MUST poder apagar uma doação, de qualquer status. A exclusão MUST remover junto, na mesma operação, as conversas e as mensagens da doação e os registros das fotos adicionais, sem deixar registros órfãos.

#### Scenario: Apagar a própria doação
- **WHEN** a pessoa dona apaga uma doação
- **THEN** o sistema MUST remover a doação, as conversas, as mensagens e os registros de fotos adicionais dela
- **AND** a doação MUST deixar de aparecer na listagem, na home, no detalhe e no perfil público

#### Scenario: Pessoa que não é dona
- **WHEN** uma pessoa autenticada tenta apagar uma doação de outra pessoa
- **THEN** o endpoint MUST recusar a requisição sem remover nada

### Requirement: Link “Minhas doações” no cabeçalho da home
O cabeçalho autenticado da home MUST mostrar o link “Minhas doações”, que leva a `/minhas-doacoes`. O cabeçalho de visitante MUST NOT mostrar esse link.

#### Scenario: Pessoa logada na home
- **WHEN** a home está com o cabeçalho autenticado
- **THEN** o cabeçalho MUST mostrar “Minhas doações” ao lado de “Olá, <primeiro nome>” e “Sair”, levando a `/minhas-doacoes`

#### Scenario: Visitante na home
- **WHEN** a home está com o cabeçalho de visitante
- **THEN** o cabeçalho MUST NOT mostrar “Minhas doações”

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
- **THEN** MUST mostrar um círculo com a inicial, o primeiro nome, “Doações” com o contador de ativas e “Doações realizadas” com o contador de concluídas
- **AND** MUST NOT apresentar foto de perfil, e-mail, “Sobre”, “Compartilhar”, “Editar perfil”, avaliações, selo de verificação ou botão de chat, nem como “Em breve”

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

### Requirement: Ações sobre a doação na página
Cada cartão MUST ter um menu de ações acessível pelo teclado, com só as ações válidas para o status atual. As ações que não têm volta ou que apagam dados MUST pedir confirmação antes da requisição.

#### Scenario: Ações por status
- **WHEN** a pessoa abre o menu de um cartão
- **THEN** uma doação disponível MUST oferecer “Marcar como reservada”, “Marcar como concluída”, “Editar” e “Apagar”
- **AND** uma doação reservada MUST oferecer “Marcar como disponível”, “Marcar como concluída”, “Editar” e “Apagar”
- **AND** uma doação concluída MUST oferecer só “Apagar”
- **AND** o botão do menu MUST ter um rótulo acessível com o título da doação

#### Scenario: Confirmar a conclusão
- **WHEN** a pessoa escolhe “Marcar como concluída”
- **THEN** a página MUST pedir confirmação, avisando que a doação concluída não volta a outro status e que as conversas ficam somente para leitura
- **AND** cancelar MUST NOT fazer requisição

#### Scenario: Confirmar a exclusão
- **WHEN** a pessoa escolhe “Apagar”
- **THEN** a página MUST pedir confirmação, avisando que a doação, as fotos e as conversas e mensagens dela serão apagadas e que isso não tem volta
- **AND** cancelar MUST NOT fazer requisição

#### Scenario: Ação concluída
- **WHEN** uma ação de status ou de exclusão é aceita pelo Xano
- **THEN** a página MUST atualizar a grade e os contadores e mostrar uma mensagem curta de sucesso, anunciada ao leitor de tela

#### Scenario: Ação recusada ou com falha
- **WHEN** o Xano recusa a ação ou ocorre falha de rede ou HTTP 429
- **THEN** a página MUST mostrar uma mensagem de erro simples e manter a grade como estava
- **AND** enquanto uma ação está em andamento, MUST NOT aceitar outra

### Requirement: Página de edição da doação
A página `/minhas-doacoes/<id>/editar` MUST exigir login, carregar os campos da própria doação e salvar só os campos de texto, com as mesmas validações e opções do cadastro.

#### Scenario: Formulário preenchido
- **WHEN** a pessoa abre a edição de uma doação sua, disponível ou reservada
- **THEN** a página MUST mostrar título, descrição, categoria, condição, entrega e preferência de contato preenchidos com os valores atuais
- **AND** as opções MUST ser as do cadastro: categorias sem “Alimentos” e “Móveis”, “A combinar” e “E-mail” ou “Chat do DoaFácil”
- **AND** MUST NOT apresentar campo de fotos, cidade ou UF

#### Scenario: Valor atual fora das opções
- **WHEN** o valor atual da categoria, da entrega ou da preferência de contato não está entre as opções do cadastro
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
