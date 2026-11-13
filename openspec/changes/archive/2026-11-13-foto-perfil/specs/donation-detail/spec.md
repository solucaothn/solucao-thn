## MODIFIED Requirements

### Requirement: Resposta pública limitada e sem dados privados
A resposta do detalhe MUST conter somente os dados da doação aprovados para exibição e MUST NOT expor dados privados de quem doa.

#### Scenario: Dados retornados para o detalhe
- **WHEN** uma consulta pública retorna uma doação disponível
- **THEN** a resposta MUST incluir identificador, título, descrição, condição, nome da categoria, modalidade de entrega, preferência de contato, cidade e UF, fotos ordenadas, primeiro nome de quem doa e a URL pública da foto de perfil de quem doa, nula quando não há foto
- **AND** o primeiro nome MUST ser o único dado nominal de quem doa
- **AND** cidade e UF usadas no cartão de quem doa MUST corresponder à localização da doação

#### Scenario: Campos privados excluídos
- **WHEN** a resposta do detalhe é construída
- **THEN** ela MUST NOT conter e-mail, sobrenome, `owner_id`, endereço, bairro ou CEP de quem doa
- **AND** MUST NOT incluir dados adicionais da conta que não sejam necessários à página

### Requirement: Conteúdo do detalhe da doação
A página de detalhe MUST apresentar os dados existentes e aprovados da doação em uma única página, sem exibir campos ou ações fora do escopo. A disposição MUST seguir o layout aprovado no Figma (frames `detalhes-doacao-inteira` e `detalhes-doacao-1`), com as diferenças registradas em `docs/design/README.md`.

#### Scenario: Exibir detalhes disponíveis
- **WHEN** uma pessoa abre uma doação disponível
- **THEN** a página MUST apresentar a galeria, o título, a condição com o rótulo “Condição”, a descrição, o nome da categoria, a cidade/UF, a modalidade de entrega, a preferência de contato como texto e o cartão de quem doa com a foto de perfil de quem doa, redonda, com `object-fit: cover` e texto alternativo com o primeiro nome, ou, sem foto, um círculo com a inicial do primeiro nome, o primeiro nome e cidade/UF, sem outros dados de quem doa
- **AND** MUST apresentar no topo do cartão os botões “Outros meios de comunicação” e “Chat” em conformidade com o layout aprovado no Figma
- **AND** o acesso ao perfil de quem doa MUST ser feito somente pelo cartão “Quem doa”, sem outros botões de perfil

#### Scenario: Não apresentar dados ou recursos indisponíveis
- **WHEN** a página exibe os detalhes da doação
- **THEN** MUST permanecerem ocultos Cor, Material, Tipo, bairro, CEP, avaliações, presença online, indicadores de conta ou e-mail verificados
- **AND** as outras doações de quem doa MUST aparecer somente no perfil público, não no detalhe
- **AND** MUST NOT apresentar esses itens como “Em breve”

#### Scenario: Cartão “Quem doa” leva ao perfil
- **WHEN** a pessoa clica ou aciona pelo teclado o cartão “Quem doa”
- **THEN** a página MUST navegar para `/doacao/<id>/quem-doa`, com o identificador da doação aberta
- **AND** o cartão MUST ter rótulo acessível que indique o perfil, como “Ver perfil de <primeiro nome>”, foco visível e área de toque confortável
- **AND** o frontend MUST NOT receber nem usar o identificador de usuário de quem doa

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
