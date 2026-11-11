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
