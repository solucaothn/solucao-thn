## MODIFIED Requirements

### Requirement: Resposta do perfil sem dados privados
A resposta do perfil MUST conter somente o primeiro nome, a cidade, a UF, o mês e o ano de cadastro e o texto de Sobre de quem doa e a página pedida das doações disponíveis. Ela MUST NOT expor dados privados nem identificadores de usuário.

#### Scenario: Dados de identificação retornados
- **WHEN** a consulta do perfil é respondida com sucesso
- **THEN** a resposta MUST incluir o primeiro nome, a cidade, a UF, o mês e o ano de cadastro e o texto de Sobre de quem doa
- **AND** o primeiro nome MUST ser o único dado nominal
- **AND** a data de cadastro MUST ser reduzida a mês e ano, sem dia nem horário
- **AND** um Sobre não preenchido MUST vir vazio ou nulo

#### Scenario: Campos privados excluídos
- **WHEN** a resposta do perfil é construída
- **THEN** ela MUST NOT conter e-mail, sobrenome, `owner_id`, id de usuário, endereço, bairro, CEP, papel da conta ou dados de recuperação de senha

### Requirement: Página do perfil de quem doa
A página `/doacao/<id>/quem-doa` MUST apresentar a identificação de quem doa e as suas doações disponíveis, seguindo os frames `perfil-doador-01` e `perfil-doador-02` do Figma, com as diferenças registradas em `docs/design/README.md`.

#### Scenario: Identificação de quem doa
- **WHEN** o perfil carrega com sucesso
- **THEN** a página MUST mostrar, num cartão, um círculo com a inicial do primeiro nome, o primeiro nome, “Cidade, UF” e “No DoaFácil desde <mês> de <ano>”, com o mês por extenso em português

#### Scenario: Sobre de quem doa
- **WHEN** o perfil carrega com sucesso e quem doa preencheu o Sobre
- **THEN** o cartão de identificação MUST mostrar o texto de Sobre abaixo de “No DoaFácil desde …”, como texto simples, preservando as quebras de linha e sem interpretar HTML
- **AND** com o Sobre vazio, o cartão MUST NOT mostrar título, espaço reservado nem texto no lugar dele

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
