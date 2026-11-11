## ADDED Requirements

### Requirement: Visualizador de fotos da doação
Clicar ou acionar pelo teclado qualquer foto da galeria MUST abrir um visualizador em tela cheia, com fundo creme semitransparente e desfocado e a foto inteira, sem corte. O visualizador MUST permitir trocar de foto, ampliar e fechar, e MUST ser acessível pelo teclado e por leitores de tela.

#### Scenario: Abrir pela capa ou por uma miniatura
- **WHEN** a pessoa clica ou aciona com Enter ou Espaço a capa ou uma miniatura
- **THEN** o visualizador MUST abrir na foto escolhida, mostrada inteira sobre o fundo creme semitransparente com desfoque
- **AND** MUST mostrar o contador “N de M”, com a posição da foto e o total de fotos

#### Scenario: Cores do visualizador
- **WHEN** o visualizador está aberto
- **THEN** o fundo MUST ser creme semitransparente (`rgba(255, 246, 232, 0.85)`) com desfoque da página atrás, sem o véu escuro padrão do diálogo
- **AND** textos e ícones MUST ser escuros (`#1F1F1F`), com contraste AA sobre o fundo
- **AND** os botões ‹, › e X MUST ter fundo branco e sombra leve

#### Scenario: Foto inteira em 1x
- **WHEN** a foto aparece em 1x, em qualquer largura e altura de tela
- **THEN** ela MUST caber inteira na área abaixo do cabeçalho do visualizador, com `object-fit: contain`
- **AND** MUST NOT passar da borda de baixo nem das laterais da tela

#### Scenario: Controles dentro da tela
- **WHEN** o visualizador está aberto, em qualquer largura de tela
- **THEN** o X e os botões ‹ e › MUST ficar inteiros dentro da área visível, a 16 px das bordas
- **AND** MUST NOT ficar cortados nem exigir rolagem para aparecer

#### Scenario: Trocar de foto
- **WHEN** o visualizador está aberto com mais de uma foto e a pessoa aciona ‹ ou ›, ou aperta as setas esquerda ou direita do teclado
- **THEN** MUST mostrar a foto anterior ou a seguinte, voltando ao início depois da última e ao fim antes da primeira
- **AND** o contador MUST acompanhar a foto mostrada

#### Scenario: Doação com uma foto
- **WHEN** o visualizador abre numa doação com uma única foto
- **THEN** MUST NOT mostrar os botões ‹ e ›
- **AND** as setas do teclado MUST NOT trocar a foto

#### Scenario: Ampliar a foto
- **WHEN** a pessoa clica ou aciona a foto aberta
- **THEN** o zoom MUST alternar entre 1x e 2x
- **AND** em 2x a foto MUST poder ser movida com a rolagem
- **AND** no celular MUST valer o gesto de pinça do navegador
- **AND** trocar de foto MUST voltar o zoom a 1x

#### Scenario: Fechar o visualizador
- **WHEN** a pessoa aciona o botão de fechar, aperta Esc ou clica no fundo fora da foto e dos botões
- **THEN** o visualizador MUST fechar e devolver o foco à página

#### Scenario: Acessibilidade do visualizador
- **WHEN** o visualizador está aberto
- **THEN** o foco MUST ficar preso dentro dele, como numa janela modal
- **AND** os botões MUST ter rótulos acessíveis (“Fechar”, “Foto anterior”, “Próxima foto”, “Ampliar foto” ou “Reduzir foto”) e área de toque de pelo menos 44 px
- **AND** a capa e as miniaturas MUST ser botões com rótulo acessível que indica qual foto abre

## MODIFIED Requirements

### Requirement: Conteúdo do detalhe da doação
A página de detalhe MUST apresentar os dados existentes e aprovados da doação em uma única página, sem exibir campos ou ações fora do escopo. A disposição MUST seguir o layout aprovado no Figma (frames `detalhes-doacao-inteira` e `detalhes-doacao-1`), com as diferenças registradas em `docs/design/README.md`.

#### Scenario: Exibir detalhes disponíveis
- **WHEN** uma pessoa abre uma doação disponível
- **THEN** a página MUST apresentar a galeria, o título, a condição com o rótulo “Condição”, a descrição, o nome da categoria, a cidade/UF, a modalidade de entrega, a preferência de contato como texto e o cartão de quem doa com somente primeiro nome e cidade/UF
- **AND** MUST apresentar no topo do cartão os botões “Outros meios de comunicação” e “Chat” em conformidade com o layout aprovado no Figma
- **AND** MUST NOT apresentar botões de acesso ao perfil do doador

#### Scenario: Não apresentar dados ou recursos indisponíveis
- **WHEN** a página exibe os detalhes da doação
- **THEN** MUST permanecerem ocultos Cor, Material, Tipo, bairro, CEP, avaliações, histórico de doações, presença online, indicadores de conta ou e-mail verificados, foto de perfil e qualquer botão ou link para o perfil do doador
- **AND** MUST NOT apresentar esses itens como “Em breve”

#### Scenario: Galeria e resumo no computador
- **WHEN** a página é exibida em tela larga
- **THEN** a galeria MUST mostrar a capa grande e, ao lado dela, as demais fotos (até quatro) numa grade de duas colunas
- **AND** o resumo com o título, a condição e os botões de contato MUST ficar num cartão à direita da galeria

#### Scenario: Doação com uma foto só
- **WHEN** a doação tem uma única foto (ou só a imagem genérica)
- **THEN** a galeria MUST mostrar a imagem inteira, sem corte, centralizada e com fundo neutro nas sobras
- **AND** MUST manter a mesma altura da capa da galeria com várias fotos

#### Scenario: Título e descrição abaixo da galeria
- **WHEN** a página exibe uma doação
- **THEN** o título da doação MUST aparecer em destaque logo abaixo da galeria, seguido da descrição
- **AND** a descrição MUST preservar as quebras de linha e ser apresentada como texto simples

#### Scenario: Seção Detalhes em grade
- **WHEN** a página exibe uma doação
- **THEN** a seção “Detalhes” MUST apresentar, em grade, Categoria, Condição, Forma de entrega e Preferência de contato
- **AND** cada item MUST ter um ícone verde decorativo, um rótulo pequeno e o valor logo abaixo do rótulo
- **AND** MUST NOT apresentar outros atributos

#### Scenario: Localização somente com cidade e UF
- **WHEN** a página exibe uma doação
- **THEN** a seção “Localização” MUST apresentar, num cartão com ícone decorativo, somente a cidade e a UF no formato “Cidade, UF”
- **AND** MUST NOT apresentar bairro, zona, CEP, endereço ou mapa

#### Scenario: Layout em tela estreita
- **WHEN** a página é exibida numa largura de 360 px
- **THEN** a galeria, o resumo, o título com a descrição, os detalhes, a localização e o cartão de quem doa MUST aparecer em uma coluna, sem rolagem horizontal
- **AND** a grade “Detalhes” MUST se reorganizar em menos colunas sem cortar textos

#### Scenario: Contraste dos textos e botões
- **WHEN** a página apresenta textos, rótulos e botões
- **THEN** todos MUST ter contraste mínimo AA sobre o fundo em que aparecem, incluindo o texto branco do botão “Outros meios de comunicação”

### Requirement: Botão Voltar do detalhe
A página de detalhe MUST oferecer um controle acessível para voltar à home em todos os estados de exibição. O controle MUST ficar na linha do logotipo, à esquerda, como “Voltar ao início”, igual ao cabeçalho do chat e ao Figma.

#### Scenario: Botão Voltar durante o carregamento
- **WHEN** a página de detalhe está carregando a doação
- **THEN** MUST apresentar o controle “Voltar ao início” com seta verde na linha do logotipo
- **AND** MUST disponibilizar o rótulo acessível “Voltar ao início”

#### Scenario: Botão Voltar com a doação carregada
- **WHEN** a página apresenta os dados de uma doação disponível
- **THEN** MUST apresentar o controle “Voltar ao início” com seta verde na linha do logotipo
- **AND** MUST disponibilizar o rótulo acessível “Voltar ao início”

#### Scenario: Botão Voltar quando a doação não é encontrada
- **WHEN** a página apresenta “Doação não encontrada”, inclusive para um ID inválido
- **THEN** MUST apresentar o controle “Voltar ao início” com seta verde na linha do logotipo
- **AND** MUST disponibilizar o rótulo acessível “Voltar ao início”

#### Scenario: Botão Voltar em caso de erro
- **WHEN** a página apresenta uma mensagem de erro de rede ou de resposta inválida
- **THEN** MUST apresentar o controle “Voltar ao início” com seta verde na linha do logotipo
- **AND** MUST disponibilizar o rótulo acessível “Voltar ao início”

#### Scenario: Retornar para a home
- **WHEN** uma pessoa ativa o controle “Voltar ao início” em qualquer estado da página de detalhe
- **THEN** o sistema MUST navegar para `/`

#### Scenario: Texto do controle em tela estreita
- **WHEN** a página é exibida em tela estreita
- **THEN** o controle MAY mostrar só a seta, mantendo o rótulo acessível “Voltar ao início” e uma área de toque confortável
