# donation-detail Specification

## Purpose
Permite consultar publicamente uma doação disponível e conhecer seus detalhes, suas fotos e a identificação pública mínima de quem doa.

## Requirements

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
- **THEN** a resposta MUST incluir identificador, título, descrição, condição, nome da categoria, modalidade de entrega, preferência de contato, cidade e UF, fotos ordenadas, primeiro nome de quem doa e a URL pública da foto de perfil de quem doa, nula quando não há foto
- **AND** MUST incluir, de quem doa, o contador de doações ativas, que soma as disponíveis e as reservadas, o contador de doações concluídas, considerando todas as doações dessa pessoa, e se o e-mail está verificado, como verdadeiro ou falso
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
A página de detalhe MUST apresentar os dados existentes e aprovados da doação em uma única página, sem exibir campos ou ações fora do escopo. A disposição MUST seguir o layout aprovado no Figma (frames `detalhes-doacao-inteira` e `detalhes-doacao-1`), com as diferenças registradas em `docs/design/README.md`.

#### Scenario: Exibir detalhes disponíveis
- **WHEN** uma pessoa abre uma doação disponível
- **THEN** a página MUST apresentar a galeria, o título, a condição com o rótulo “Condição”, a descrição, o nome da categoria, a cidade/UF, a modalidade de entrega, a preferência de contato como texto e o cartão de quem doa com a foto de perfil de quem doa, redonda, com `object-fit: cover` e texto alternativo com o primeiro nome, ou, sem foto, um círculo com a inicial do primeiro nome, o primeiro nome e cidade/UF
- **AND** o cartão de quem doa MUST mostrar, na seção “Doações”, “Doações” com o contador de ativas e “Doações realizadas” com o contador de concluídas, no singular quando o número é 1 (“Doação” e “Doação realizada”), como no perfil público e em Minhas doações, e, na seção “Informações verificadas”, “E-mail” somente quando o e-mail de quem doa está verificado, sem outros dados de quem doa
- **AND** MUST apresentar no topo do cartão os botões “Outros meios de comunicação” e “Chat” em conformidade com o layout aprovado no Figma
- **AND** o acesso ao perfil de quem doa MUST ser feito somente pelo botão “Ver perfil de quem doa” do cartão “Quem doa”, sem outros botões de perfil

#### Scenario: Não apresentar dados ou recursos indisponíveis
- **WHEN** a página exibe os detalhes da doação
- **THEN** MUST permanecerem ocultos Cor, Material, Tipo, bairro, CEP, avaliações ou estrelas, presença online, doações canceladas, CPF e o e-mail de quem doa
- **AND** as outras doações de quem doa MUST aparecer somente no perfil público, não no detalhe
- **AND** MUST NOT apresentar esses itens como “Em breve”

#### Scenario: Cartão “Quem doa” leva ao perfil
- **WHEN** a pessoa clica ou aciona pelo teclado o botão “Ver perfil de quem doa” do cartão “Quem doa”
- **THEN** a página MUST navegar para `/doacao/<id>/quem-doa`, com o identificador da doação aberta
- **AND** o botão MUST ser contornado, ocupar a largura toda do cartão, ter área de toque de pelo menos 44 px, foco visível e rótulo acessível que comece pelo texto visível e indique o primeiro nome, como “Ver perfil de quem doa, <primeiro nome>”
- **AND** o restante do cartão MUST NOT ser um link
- **AND** o frontend MUST NOT receber nem usar o identificador de usuário de quem doa

#### Scenario: Seções do cartão “Quem doa”
- **WHEN** a página exibe o cartão “Quem doa”
- **THEN** o topo MUST mostrar a foto de perfil (ou a inicial) e o primeiro nome e, abaixo, “No DoaFácil desde <mês> de <ano>” com ícone de calendário e “Cidade, UF” com ícone de local
- **AND** abaixo do botão “Ver perfil de quem doa”, uma linha divisória MUST separar a seção “Doações”, com os números “Doações” e “Doações realizadas”, cada um com ícone decorativo
- **AND** os ícones MUST ser decorativos, ocultos dos leitores de tela

#### Scenario: Informações verificadas só com e-mail verificado
- **WHEN** o e-mail de quem doa está verificado
- **THEN** uma linha divisória MUST separar a seção “Informações verificadas”, com “E-mail” e um ícone de check verde
- **AND** quando o e-mail não está verificado, a seção e a linha divisória dela MUST NOT aparecer

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

### Requirement: Fluxo de contato do doador
O sistema MUST permitir iniciar contato com quem doa somente de acordo com a preferência de contato e a autenticação da pessoa interessada, sem expor o e-mail na página. O botão “Chat” MUST iniciar ou reabrir a conversa pelo endpoint do chat e levar a pessoa a `/chat`, sem revelar por que uma doação não aceita conversa.

#### Scenario: Pessoa sem login solicita outros meios de comunicação
- **WHEN** uma pessoa sem sessão válida clica em “Outros meios de comunicação”
- **THEN** o sistema MUST redirecionar para `/login`
- **AND** MUST NOT chamar o endpoint autenticado de e-mail

#### Scenario: Pessoa logada solicita contato por e-mail
- **WHEN** uma pessoa autenticada clica em “Outros meios de comunicação” em uma doação disponível cuja preferência é “E-mail” e que pertence a outra pessoa
- **THEN** o sistema MUST chamar o endpoint autenticado de e-mail com o token da sessão
- **AND** MUST abrir `mailto:` com o e-mail codificado e um assunto simples que inclua o título da doação
- **AND** MUST remover o e-mail do estado após iniciar o redirecionamento

#### Scenario: Pessoa dona da doação solicita outros meios de comunicação
- **WHEN** a pessoa autenticada que cadastrou a doação clica em “Outros meios de comunicação” na própria doação
- **THEN** o frontend MUST chamar o endpoint autenticado de e-mail, pois a resposta pública do detalhe não contém `owner_id`
- **AND** quando o backend confirmar que a doação existe, está disponível e pertence à pessoa autenticada, MUST responder com HTTP 403 e uma mensagem própria, sem devolver o e-mail
- **AND** o frontend MUST traduzir essa resposta para “Esta é a sua doação.”
- **AND** o frontend MUST NOT receber nem guardar `owner_id`

#### Scenario: Preferência de contato por chat
- **WHEN** uma pessoa autenticada clica em “Outros meios de comunicação” em uma doação cuja preferência é “Chat do DoaFácil”
- **THEN** a página MUST mostrar “Quem doa prefere contato pelo chat.”
- **AND** MUST NOT chamar o endpoint autenticado de e-mail

#### Scenario: Botão Chat
- **WHEN** uma pessoa autenticada clica em “Chat” no topo do detalhe de uma doação que aceita conversa
- **THEN** a página MUST chamar o endpoint de iniciar conversa com o token da sessão e o identificador da doação
- **AND** MUST navegar para `/chat?conversa=<id>` com o identificador devolvido, abrindo essa conversa
- **AND** se a conversa já existir, MUST abrir a mesma conversa, sem criar outra

#### Scenario: Botão Chat sem login
- **WHEN** uma pessoa sem sessão válida clica em “Chat”
- **THEN** o sistema MUST redirecionar para `/login`
- **AND** MUST NOT chamar o endpoint de iniciar conversa

#### Scenario: Botão Chat em doação que não aceita conversa
- **WHEN** o endpoint de iniciar conversa responde HTTP 404, seja porque a preferência é “E-mail”, porque a doação é da própria pessoa ou porque ela não está mais disponível
- **THEN** a página MUST mostrar a mensagem neutra “Não é possível conversar sobre esta doação pelo chat.”
- **AND** MUST NOT navegar para outra rota nem revelar qual condição impediu a conversa

#### Scenario: Falha ao iniciar conversa
- **WHEN** ocorre falha de rede ou o endpoint de iniciar conversa responde com erro diferente de 401 e 404
- **THEN** a página MUST mostrar uma mensagem de erro simples e manter o restante da página funcional
- **AND** quando a resposta for HTTP 401, MUST limpar a sessão transitória e redirecionar para `/login`

#### Scenario: Endpoint sem e-mail disponível
- **WHEN** o endpoint autenticado é chamado sem sessão válida
- **THEN** MUST responder com HTTP 401

#### Scenario: Doação inexistente, indisponível ou com preferência por chat
- **WHEN** o endpoint autenticado recebe uma solicitação para uma doação inexistente, indisponível ou cuja preferência é “Chat do DoaFácil”
- **THEN** MUST responder com o mesmo erro HTTP 404 genérico

#### Scenario: Pessoa autenticada consulta a própria doação
- **WHEN** o endpoint autenticado confirma que a doação existe e está disponível, e que pertence à pessoa autenticada
- **THEN** MUST responder com HTTP 403 e uma mensagem própria
- **AND** MUST NOT devolver o e-mail do doador

#### Scenario: Pessoa autenticada consulta doação elegível de outra pessoa
- **WHEN** o endpoint autenticado confirma que a doação existe, está disponível, pertence a outra pessoa e a preferência é “E-mail”
- **THEN** MUST retornar somente o e-mail de quem doa

#### Scenario: Registro de acesso ao e-mail
- **WHEN** o endpoint autenticado de e-mail recebe uma chamada
- **THEN** o sistema MUST registrar um evento pela função de log existente usando somente `user_id`, ação e data
- **AND** MUST NOT incluir e-mail, nome, título da doação ou token no evento

#### Scenario: Erro ao solicitar contato
- **WHEN** ocorre falha de rede ou o endpoint responde com erro HTTP 401 ou 404
- **THEN** a interface MUST apresentar uma mensagem de erro simples no mesmo estilo visual do site
- **AND** MUST manter o restante da página funcional

#### Scenario: Resposta 403 para doação própria
- **WHEN** o endpoint responde com HTTP 403 porque a doação pertence à pessoa autenticada
- **THEN** a interface MUST mostrar “Esta é a sua doação.”
- **AND** MUST NOT exibir o e-mail

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

### Requirement: Aviso de doação recém-publicada
Logo depois de publicar uma doação pelo cadastro, a página de detalhe dessa doação MUST mostrar o aviso “Doação publicada!” com um link para “Minhas doações”. O aviso MUST aparecer somente nessa chegada, e não em outras visitas ao detalhe.

#### Scenario: Chegada depois de publicar
- **WHEN** o cadastro conclui a publicação e abre `/doacao/<id>` da doação criada
- **THEN** a página MUST mostrar, acima do conteúdo da doação, o aviso “Doação publicada!”, anunciado ao leitor de tela, com o link “Minhas doações”, que leva a `/minhas-doacoes`
- **AND** o aviso e o link MUST ter contraste mínimo AA e o link MUST ter área de toque de pelo menos 44 px
- **AND** o aviso MUST caber em 360 px sem rolagem horizontal

#### Scenario: Outras visitas ao detalhe
- **WHEN** qualquer pessoa abre o detalhe de uma doação sem ter acabado de publicá-la, inclusive ao recarregar a página depois da chegada
- **THEN** a página MUST NOT mostrar o aviso de publicação

#### Scenario: Aviso só para a doação publicada
- **WHEN** a pessoa, depois de chegar ao detalhe com o aviso, abre o detalhe de outra doação
- **THEN** o aviso MUST NOT aparecer nessa outra doação

### Requirement: Tentar de novo quando o detalhe falha
Quando o detalhe da doação não puder ser carregado, a página SHALL mostrar a mensagem de falha com o botão “Tentar de novo”, que busca a doação outra vez sem sair da página.

#### Scenario: Falha ao carregar o detalhe
- **WHEN** a busca do detalhe falha (por exemplo, pelo limite de pedidos do backend)
- **THEN** a página MUST mostrar a mensagem de falha e o botão “Tentar de novo”, com 44 px de área de toque e foco visível
- **AND** acionar o botão MUST mostrar “Carregando doação...” na hora, buscar a doação de novo e, se der certo, mostrar o detalhe
- **AND** a nova tentativa MUST fazer um único pedido do detalhe ao backend

### Requirement: Caminhos a partir de uma doação indisponível
Quando a doação não está disponível (reservada, concluída, apagada ou com identificador inválido), a página de detalhe SHALL manter o aviso “Doação não encontrada” e acrescentar uma explicação e dois caminhos, sem revelar qual é o status da doação.

#### Scenario: Doação indisponível
- **WHEN** a página de detalhe mostra “Doação não encontrada”
- **THEN** ela MUST explicar que a doação pode ter sido reservada, concluída ou removida por quem doou
- **AND** MUST oferecer os links “Ver outras doações” (`/explorar`) e “Voltar ao início” (`/`), com foco visível e pelo menos 44 px de área de toque
- **AND** MUST NOT dizer qual desses casos aconteceu

### Requirement: Data de cadastro de quem doa no cartão
O cartão “Quem doa” do detalhe MUST mostrar o mês e o ano de cadastro de quem doa, lidos do perfil público de quem doa da mesma doação, sem atrasar o restante da página e sem mudar a resposta do detalhe.

#### Scenario: Perfil público disponível
- **WHEN** a página exibe uma doação e o perfil público de quem doa responde com o mês e o ano de cadastro
- **THEN** o cartão MUST mostrar “No DoaFácil desde <mês> de <ano>”, com o mês por extenso em minúsculas, como “No DoaFácil desde outubro de 2020”

#### Scenario: Perfil público indisponível
- **WHEN** o pedido ao perfil público falha, inclusive com HTTP 404 ou 429, ou responde com dados inválidos
- **THEN** a linha “No DoaFácil desde …” MUST NOT aparecer
- **AND** o restante do detalhe e do cartão MUST aparecer normalmente, sem mensagem de erro

#### Scenario: Perfil público reaproveitado do cache
- **WHEN** o detalhe e o perfil público da mesma doação são abertos dentro de 60 s
- **THEN** a leitura do perfil MUST reaproveitar o cache público do perfil de quem doa, sem novo pedido ao backend

#### Scenario: Doação trocada antes da resposta
- **WHEN** a pessoa abre outra doação antes de o perfil da anterior responder
- **THEN** o cartão MUST NOT mostrar a data de cadastro de quem doa a doação anterior
