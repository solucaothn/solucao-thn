## MODIFIED Requirements

### Requirement: Conteúdo do detalhe da doação
A página de detalhe MUST apresentar os dados existentes e aprovados da doação em uma única página, sem exibir campos ou ações fora do escopo. A disposição MUST seguir o layout aprovado no Figma (frames `detalhes-doacao-inteira` e `detalhes-doacao-1`), com as diferenças registradas em `docs/design/README.md`.

#### Scenario: Exibir detalhes disponíveis
- **WHEN** uma pessoa abre uma doação disponível
- **THEN** a página MUST apresentar a galeria, o título, a condição com o rótulo “Condição”, a descrição, o nome da categoria, a cidade/UF, a modalidade de entrega, a preferência de contato como texto e o cartão de quem doa com a foto de perfil de quem doa, redonda, com `object-fit: cover` e texto alternativo com o primeiro nome, ou, sem foto, um círculo com a inicial do primeiro nome, o primeiro nome e cidade/UF
- **AND** o cartão de quem doa MUST mostrar, na seção “Doações”, “Doações” com o contador de ativas e “Doações realizadas” com o contador de concluídas, no singular quando o número é 1 (“Doação” e “Doação realizada”), como no perfil público e em Minhas doações, e, na seção “Informações verificadas”, “E-mail” somente quando o e-mail de quem doa está verificado, sem outros dados de quem doa
- **AND** MUST apresentar no topo do cartão de resumo os botões “Outros contatos” e “Chat”
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
- **THEN** logo abaixo da galeria MUST aparecer o subtítulo “Descrição”, no mesmo estilo dos subtítulos “Detalhes” e “Localização”, seguido da descrição
- **AND** o título da doação MUST aparecer só no cartão de resumo, como título principal da página, e MUST NOT se repetir acima da descrição
- **AND** a descrição MUST preservar as quebras de linha e ser apresentada como texto simples

#### Scenario: Cartão de resumo
- **WHEN** a página exibe o cartão de resumo, em qualquer largura
- **THEN** o título da doação MUST usar peso semibold, cerca de 28 px no celular e 30 px no computador, altura de linha de cerca de 1,25 e no máximo 3 linhas, terminando em reticências quando passar
- **AND** o cartão MUST ter cerca de 28 px de respiro interno, cerca de 8 px entre o título e “Condição”, cerca de 24 px entre “Condição” e os botões e cerca de 12 px entre os dois botões
- **AND** “Outros contatos” e “Chat” MUST ter a mesma altura, de cerca de 48 px, com o texto numa linha só
- **AND** nenhum texto ou botão do cartão MUST encostar em outro ou na borda

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
- **THEN** a galeria, o resumo, a descrição, os detalhes, a localização e o cartão de quem doa MUST aparecer em uma coluna, sem rolagem horizontal
- **AND** a grade “Detalhes” MUST se reorganizar em menos colunas sem cortar textos

#### Scenario: Contraste dos textos e botões
- **WHEN** a página apresenta textos, rótulos e botões
- **THEN** todos MUST ter contraste mínimo AA sobre o fundo em que aparecem, incluindo o texto branco do botão “Outros contatos”

### Requirement: Fluxo de contato do doador
O sistema MUST permitir iniciar contato com quem doa somente de acordo com a preferência de contato e a autenticação da pessoa interessada, sem expor o e-mail na página. O botão “Chat” MUST iniciar ou reabrir a conversa pelo endpoint do chat e levar a pessoa a `/chat`, sem revelar por que uma doação não aceita conversa.

#### Scenario: Pessoa sem login solicita outros meios de comunicação
- **WHEN** uma pessoa sem sessão válida clica em “Outros contatos”
- **THEN** o sistema MUST redirecionar para `/login`
- **AND** MUST NOT chamar o endpoint autenticado de e-mail

#### Scenario: Pessoa logada solicita contato por e-mail
- **WHEN** uma pessoa autenticada clica em “Outros contatos” em uma doação disponível cuja preferência é “E-mail” e que pertence a outra pessoa
- **THEN** o sistema MUST chamar o endpoint autenticado de e-mail com o token da sessão
- **AND** MUST abrir `mailto:` com o e-mail codificado e um assunto simples que inclua o título da doação
- **AND** MUST remover o e-mail do estado após iniciar o redirecionamento

#### Scenario: Pessoa dona da doação solicita outros meios de comunicação
- **WHEN** a pessoa autenticada que cadastrou a doação clica em “Outros contatos” na própria doação
- **THEN** o frontend MUST chamar o endpoint autenticado de e-mail, pois a resposta pública do detalhe não contém `owner_id`
- **AND** quando o backend confirmar que a doação existe, está disponível e pertence à pessoa autenticada, MUST responder com HTTP 403 e uma mensagem própria, sem devolver o e-mail
- **AND** o frontend MUST traduzir essa resposta para “Esta é a sua doação.”
- **AND** o frontend MUST NOT receber nem guardar `owner_id`

#### Scenario: Preferência de contato por chat
- **WHEN** uma pessoa autenticada clica em “Outros contatos” em uma doação cuja preferência é “Chat do DoaFácil”
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
