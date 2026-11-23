## MODIFIED Requirements

### Requirement: Página do perfil de quem doa
A página `/doacao/<id>/quem-doa` MUST apresentar a identificação de quem doa e as suas doações disponíveis, seguindo os frames `perfil-doador-01` e `perfil-doador-02` do Figma, com as diferenças registradas em `docs/design/README.md`.

#### Scenario: Identificação de quem doa
- **WHEN** o perfil carrega com sucesso
- **THEN** a página MUST mostrar, num cartão, a foto de perfil de quem doa, redonda, com `object-fit: cover` e texto alternativo com o primeiro nome, ou, sem foto, um círculo com a inicial do primeiro nome, no mesmo tamanho do círculo, o primeiro nome, “Cidade, UF” e “No DoaFácil desde <mês> de <ano>”, com o mês por extenso em português

#### Scenario: Contadores e selo de quem doa
- **WHEN** o perfil carrega com sucesso
- **THEN** o cartão de identificação MUST mostrar “Doações” com o contador de ativas e “Doações realizadas” com o contador de concluídas, no singular quando o número é 1
- **AND** MUST mostrar o selo “E-mail verificado” somente quando o e-mail de quem doa está verificado

#### Scenario: Sobre de quem doa
- **WHEN** o perfil carrega com sucesso e quem doa preencheu o Sobre
- **THEN** o cartão de identificação MUST mostrar o texto de Sobre abaixo de “No DoaFácil desde …”, como texto simples, preservando as quebras de linha e sem interpretar HTML
- **AND** com o Sobre vazio, o cartão MUST NOT mostrar título, espaço reservado nem texto no lugar dele

#### Scenario: Itens fora do escopo
- **WHEN** a página do perfil é exibida
- **THEN** MUST NOT apresentar botão de chat, avaliações, sobrenome ou e-mail
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
- **THEN** a página MUST mostrar “Nenhuma doação disponível no momento”, uma frase de apoio com o primeiro nome e o link “Explorar outras doações”, que leva a `/explorar`
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

## ADDED Requirements

### Requirement: Tentar de novo no perfil de quem doa
Quando o perfil de quem doa não puder ser carregado, a página SHALL mostrar, junto da mensagem de erro, o botão “Tentar de novo”, que busca o perfil outra vez sem sair da página.

#### Scenario: Falha ao carregar o perfil
- **WHEN** a consulta do perfil falha, responde HTTP 429 ou devolve dados inválidos
- **THEN** a página MUST mostrar a mensagem de erro e o botão “Tentar de novo”, com área de toque de pelo menos 44 px, foco visível e contraste mínimo AA

#### Scenario: Doação não encontrada não oferece nova tentativa
- **WHEN** o identificador é inválido ou o endpoint responde HTTP 404
- **THEN** a página MUST mostrar “Doação não encontrada” sem o botão “Tentar de novo”
