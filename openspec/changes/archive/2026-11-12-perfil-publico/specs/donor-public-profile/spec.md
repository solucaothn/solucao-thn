## Purpose

Permite conhecer publicamente quem doa a partir de uma doação disponível: identificação mínima, tempo de cadastro e as outras doações disponíveis da mesma pessoa, sem expor dados privados nem identificadores de usuário.

## ADDED Requirements

### Requirement: Consulta pública do perfil a partir de uma doação
O sistema MUST permitir consultar, sem autenticação, o perfil público de quem doa a partir do identificador de uma doação disponível. Doação inexistente ou indisponível MUST receber o mesmo erro 404 genérico do detalhe da doação.

#### Scenario: Consultar perfil por doação disponível
- **WHEN** uma pessoa sem sessão consulta o perfil pelo identificador de uma doação disponível
- **THEN** o sistema MUST responder com os dados públicos de quem cadastrou essa doação

#### Scenario: Doação inexistente ou indisponível
- **WHEN** o identificador não corresponde a uma doação ou a doação não está disponível
- **THEN** o sistema MUST responder com HTTP 404 e a mesma mensagem genérica de doação não encontrada
- **AND** MUST NOT revelar se a doação existe, qual é o seu status ou quem a cadastrou

#### Scenario: Uma requisição por página
- **WHEN** a página do perfil carrega ou troca de página da lista
- **THEN** o frontend MUST fazer uma única requisição ao endpoint do perfil, que traz a identificação e a página pedida da lista

### Requirement: Resposta do perfil sem dados privados
A resposta do perfil MUST conter somente o primeiro nome, a cidade, a UF, o mês e o ano de cadastro de quem doa e a página pedida das doações disponíveis. Ela MUST NOT expor dados privados nem identificadores de usuário.

#### Scenario: Dados de identificação retornados
- **WHEN** a consulta do perfil é respondida com sucesso
- **THEN** a resposta MUST incluir o primeiro nome, a cidade, a UF e o mês e o ano de cadastro de quem doa
- **AND** o primeiro nome MUST ser o único dado nominal
- **AND** a data de cadastro MUST ser reduzida a mês e ano, sem dia nem horário

#### Scenario: Campos privados excluídos
- **WHEN** a resposta do perfil é construída
- **THEN** ela MUST NOT conter e-mail, sobrenome, `owner_id`, id de usuário, endereço, bairro, CEP, papel da conta ou dados de recuperação de senha

### Requirement: Doações disponíveis de quem doa
A resposta MUST trazer as doações com status “disponível” de quem doa, da mais recente para a mais antiga, em páginas de 12, com os dados dos cartões da home e o total de itens.

#### Scenario: Lista paginada
- **WHEN** a pessoa pede uma página do perfil
- **THEN** a resposta MUST trazer até 12 doações disponíveis de quem doa, ordenadas por criação decrescente
- **AND** cada item MUST conter identificador, data de criação, título, foto como URL pública ou nula e condição
- **AND** a resposta MUST informar o número da página, o total de itens e o total de páginas

#### Scenario: Somente doações disponíveis
- **WHEN** quem doa tem doações disponíveis, reservadas e concluídas
- **THEN** a lista e o total MUST considerar somente as disponíveis

#### Scenario: Página inválida ou fora do intervalo
- **WHEN** a página pedida é menor que 1 ou maior que o total de páginas
- **THEN** o sistema MUST tratar uma página menor que 1 como a página 1
- **AND** para uma página além da última, MUST devolver a lista vazia com o total correto, sem erro

### Requirement: Página do perfil de quem doa
A página `/doacao/<id>/quem-doa` MUST apresentar a identificação de quem doa e as suas doações disponíveis, seguindo os frames `perfil-doador-01` e `perfil-doador-02` do Figma, com as diferenças registradas em `docs/design/README.md`.

#### Scenario: Identificação de quem doa
- **WHEN** o perfil carrega com sucesso
- **THEN** a página MUST mostrar, num cartão, um círculo com a inicial do primeiro nome, o primeiro nome, “Cidade, UF” e “No DoaFácil desde <mês> de <ano>”, com o mês por extenso em português

#### Scenario: Itens fora do escopo
- **WHEN** a página do perfil é exibida
- **THEN** MUST NOT apresentar foto de perfil, selo de e-mail verificado, botão de chat, avaliações, sobrenome ou e-mail
- **AND** MUST NOT apresentar esses itens como “Em breve”

#### Scenario: Lista de doações e contador
- **WHEN** quem doa tem doações disponíveis
- **THEN** a página MUST mostrar o título “Doações disponíveis”, o contador “1 item” ou “N itens” com o total, e os cartões no mesmo formato da home: foto, título, condição, NOVO para doações de até 7 dias e “Acessar”, que leva a `/doacao/<id>` do item

#### Scenario: Paginação
- **WHEN** o total passa de 12 itens
- **THEN** a página MUST mostrar controles “Anterior” e “Próxima” e a indicação “Página N de M”
- **AND** “Anterior” MUST ficar desativado na primeira página e “Próxima” na última
- **AND** trocar de página MUST fazer uma nova requisição só para a página pedida
- **AND** com até 12 itens, MUST NOT mostrar os controles

#### Scenario: Sem doações disponíveis
- **WHEN** a lista vem vazia
- **THEN** a página MUST mostrar “Nenhuma doação disponível no momento”, uma frase de apoio com o primeiro nome e o link “Explorar outras doações”, que leva à home
- **AND** MUST NOT mostrar o contador nem a paginação

#### Scenario: Voltar à doação
- **WHEN** a página do perfil é exibida, em qualquer estado
- **THEN** a linha do logotipo MUST mostrar, à esquerda, o controle “Voltar à doação” em `#007A42`, com rótulo acessível, que leva a `/doacao/<id>` da doação de origem
- **AND** em tela estreita o controle MAY mostrar só a seta, mantendo o rótulo acessível e uma área de toque de pelo menos 44 px

#### Scenario: Layout, contraste e movimento
- **WHEN** a página é exibida numa largura de 360 px
- **THEN** o cartão de identificação e os cartões de doação MUST aparecer em uma coluna, sem rolagem horizontal
- **AND** todos os textos e controles MUST ter contraste mínimo AA sobre o fundo
- **AND** o conteúdo principal MUST usar `page-fade-enter`, desativada com `prefers-reduced-motion`, sem animar o cabeçalho nem os dados carregados do Xano

### Requirement: Estados da página do perfil
A página MUST validar o identificador da rota antes de consultar o Xano e apresentar estados de carregamento, de não encontrado e de erro, no estilo visual do site.

#### Scenario: Identificador de rota inválido
- **WHEN** o segmento `<id>` não é um número inteiro positivo, como em `/doacao/abc/quem-doa`
- **THEN** a página MUST mostrar “Doação não encontrada”
- **AND** MUST NOT chamar o Xano

#### Scenario: Carregamento
- **WHEN** a página inicia a consulta
- **THEN** ela MUST mostrar um estado de carregamento sem conteúdo fictício

#### Scenario: Doação não encontrada
- **WHEN** o endpoint responde HTTP 404
- **THEN** a página MUST mostrar “Doação não encontrada”

#### Scenario: Falha de rede, limite ou resposta inválida
- **WHEN** a consulta falha, responde HTTP 429 ou devolve dados inválidos
- **THEN** a página MUST mostrar uma mensagem de erro simples, sem dados parciais de outra pessoa
- **AND** numa troca de página com falha, MUST manter a página anterior visível e mostrar a mensagem junto da paginação
