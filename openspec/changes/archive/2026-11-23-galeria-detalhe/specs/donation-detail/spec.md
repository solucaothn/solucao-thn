# Delta: donation-detail

## MODIFIED Requirements

### Requirement: Conteúdo do detalhe da doação
A página de detalhe MUST apresentar os dados existentes e aprovados da doação em uma única página, sem exibir campos ou ações fora do escopo. A disposição MUST seguir o layout aprovado no Figma (frames `detalhes-doacao-inteira` e `detalhes-doacao-1`), com as diferenças registradas em `docs/design/README.md`.

#### Scenario: Exibir detalhes disponíveis
- **WHEN** uma pessoa abre uma doação disponível
- **THEN** a página MUST apresentar a galeria, o título, a condição com o rótulo “Condição”, a descrição, o nome da categoria, a cidade/UF, a modalidade de entrega, a preferência de contato como texto e o cartão de quem doa com a foto de perfil de quem doa, redonda, com `object-fit: cover` e texto alternativo com o primeiro nome, ou, sem foto, um círculo com a inicial do primeiro nome, o primeiro nome e cidade/UF
- **AND** o cartão de quem doa MUST mostrar “Doações” com o contador de ativas e “Doações realizadas” com o contador de concluídas, no singular quando o número é 1, e o selo “E-mail verificado” somente quando o e-mail de quem doa está verificado, sem outros dados de quem doa
- **AND** MUST apresentar no topo do cartão os botões “Outros meios de comunicação” e “Chat” em conformidade com o layout aprovado no Figma
- **AND** o acesso ao perfil de quem doa MUST ser feito somente pelo cartão “Quem doa”, sem outros botões de perfil

#### Scenario: Não apresentar dados ou recursos indisponíveis
- **WHEN** a página exibe os detalhes da doação
- **THEN** MUST permanecerem ocultos Cor, Material, Tipo, bairro, CEP, avaliações, presença online e o e-mail de quem doa
- **AND** as outras doações de quem doa MUST aparecer somente no perfil público, não no detalhe
- **AND** MUST NOT apresentar esses itens como “Em breve”

#### Scenario: Cartão “Quem doa” leva ao perfil
- **WHEN** a pessoa clica ou aciona pelo teclado o cartão “Quem doa”
- **THEN** a página MUST navegar para `/doacao/<id>/quem-doa`, com o identificador da doação aberta
- **AND** o cartão MUST ter rótulo acessível que indique o perfil, como “Ver perfil de <primeiro nome>”, foco visível e área de toque confortável
- **AND** o frontend MUST NOT receber nem usar o identificador de usuário de quem doa

#### Scenario: Galeria e resumo no computador
- **WHEN** a página é exibida em tela larga
- **THEN** a galeria MUST mostrar até cinco fotos, a capa primeiro, num arranjo que depende da quantidade, com todas as fotos dentro da mesma altura da capa
- **AND** todas as fotos MUST ter os mesmos cantos arredondados e o mesmo espaçamento entre si, e, com duas fotos ou mais, MUST preencher o espaço com `object-fit: cover`
- **AND** o resumo com o título, a condição e os botões de contato MUST ficar num cartão à direita da galeria

#### Scenario: Galeria com duas fotos
- **WHEN** a doação tem duas fotos e a página é exibida em tela larga
- **THEN** a galeria MUST mostrar as duas lado a lado, do mesmo tamanho

#### Scenario: Galeria com três fotos
- **WHEN** a doação tem três fotos e a página é exibida em tela larga
- **THEN** a galeria MUST mostrar a capa à esquerda, com 2/3 da largura, e as outras duas empilhadas à direita
- **AND** as duas fotos empilhadas, somadas ao espaçamento entre elas, MUST ter a mesma altura da capa

#### Scenario: Galeria com quatro fotos
- **WHEN** a doação tem quatro fotos e a página é exibida em tela larga
- **THEN** a galeria MUST mostrar as quatro numa grade 2x2 de fotos do mesmo tamanho

#### Scenario: Galeria com cinco fotos
- **WHEN** a doação tem cinco fotos e a página é exibida em tela larga
- **THEN** a galeria MUST mostrar a capa à esquerda, com metade da largura, e as outras quatro numa grade 2x2 à direita

#### Scenario: Doação com uma foto só
- **WHEN** a doação tem uma única foto (ou só a imagem genérica)
- **THEN** a galeria MUST mostrar a imagem inteira, sem corte, na largura toda da galeria, centralizada e com fundo neutro nas sobras
- **AND** MUST manter a mesma altura da capa da galeria com várias fotos

#### Scenario: Galeria em tela estreita
- **WHEN** a página é exibida numa largura de 360 px e a doação tem mais de uma foto
- **THEN** a capa MUST aparecer em cima, na largura toda da galeria
- **AND** as demais fotos MUST aparecer logo abaixo numa única fileira de miniaturas do mesmo tamanho, com o mesmo espaçamento e os mesmos cantos arredondados
- **AND** a galeria MUST NOT causar rolagem horizontal da página

#### Scenario: Toda foto da galeria abre o visualizador
- **WHEN** a pessoa clica ou aciona com Enter ou Espaço qualquer foto da galeria, em qualquer arranjo
- **THEN** o visualizador MUST abrir naquela foto, e o rótulo acessível da foto MUST indicar a posição dela e o total de fotos

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

