# donation-creation Specification

## Purpose

Define o fluxo autenticado para cadastrar e publicar uma doação física, reunindo os dados do item, sua localização e entrega, fotos e a preferência de contato, com persistência validada pelo Xano.

## Requirements

### Requirement: Cadastro de doação em cinco etapas
O sistema MUST permitir que uma pessoa autenticada preencha um cadastro de doação dividido em cinco etapas, na ordem definida pela interface: título do objeto; descrição, categoria e condição; fotos; entrega e localização; preferência de contato e publicação. O indicador de progresso MUST mostrar a etapa atual de cinco. A localização apresentada e persistida MUST ser a cidade e a UF do perfil autenticado do doador no momento da publicação; o formulário não MUST solicitar um endereço específico.

#### Scenario: Entrada no cadastro pela página inicial
- **WHEN** uma pessoa seleciona “Quero Doar” na página inicial
- **THEN** o sistema MUST abrir `/cadastro-doacao` e direcionar pessoas sem sessão válida ao login

#### Scenario: Navegação entre etapas
- **WHEN** o doador avança ou retorna entre etapas
- **THEN** a interface MUST atualizar o indicador para “Passo X de 5” e preservar os valores já informados

#### Scenario: Avanço com dados obrigatórios ausentes
- **WHEN** o doador tenta avançar sem preencher um campo obrigatório da etapa
- **THEN** o sistema MUST indicar o campo que precisa ser corrigido e MUST permanecer na etapa atual

#### Scenario: Localização copiada do perfil
- **WHEN** a doação é publicada
- **THEN** a cidade e a UF associadas à doação MUST corresponder aos dados do perfil autenticado no momento da publicação, sem aceitar localização arbitrária enviada pelo cliente

### Requirement: Detalhamento e categoria da doação
O sistema MUST permitir informar título do objeto, descrição, uma categoria existente e uma condição física entre “Ótimo”, “Bom” e “Regular”. O campo de título MUST apresentar o exemplo “Ex.: Carrinho de brinquedo”. O título, a categoria, a descrição e a condição MUST ser validados antes da publicação; a categoria MUST existir no Xano, e a lista exibida no wizard MUST mostrar todas as categorias válidas retornadas pelo serviço de catálogo, sem exclusões por nome.

#### Scenario: Seleção de categoria disponível
- **WHEN** o formulário carrega as categorias ou o doador seleciona uma categoria
- **THEN** as opções apresentadas MUST corresponder a todas as categorias válidas retornadas pelo serviço de catálogo, inclusive “Móveis”
- **AND** uma categoria inexistente MUST ser rejeitada pelo backend

#### Scenario: Categoria que deixou de existir
- **WHEN** o serviço de catálogo não retorna mais uma categoria, como “Alimentos”
- **THEN** ela MUST NOT aparecer nas opções, e o formulário MUST continuar funcionando com as demais
- **AND** itens da resposta sem id inteiro ou sem nome MUST ser ignorados, sem quebrar a lista

#### Scenario: Exemplo do nome do item
- **WHEN** o doador visualiza o campo “Nome do item” na primeira etapa
- **THEN** o campo MUST mostrar o placeholder “Ex.: Carrinho de brinquedo”

#### Scenario: Condição selecionada no detalhamento
- **WHEN** o doador informa a condição do objeto
- **THEN** essa informação MUST ser coletada na segunda etapa e persistida com um dos três valores permitidos

### Requirement: Seleção de fotos da doação
O sistema MUST permitir selecionar de uma a cinco imagens aceitas, de até 5 MB cada, para uma doação, mostrar uma miniatura de cada uma antes da publicação e permitir remover cada foto e mudar a ordem delas. A primeira foto é a capa. Arquivos que não sejam formatos de imagem aceitos pelo armazenamento do Xano, incluindo documentos PDF, MUST ser rejeitados com mensagem compreensível. O doador MUST selecionar pelo menos uma foto para avançar da etapa 3 e publicar pelo wizard, e o backend MUST também rejeitar publicações sem fotos.

#### Scenario: Avanço com ao menos uma foto
- **WHEN** o doador seleciona uma imagem aceita
- **AND** clica em “Continuar” na etapa 3
- **THEN** o wizard MUST avançar para a etapa 4

#### Scenario: Tentativa de avançar sem fotos
- **WHEN** o doador clica em “Continuar” na etapa 3 sem fotos escolhidas, inclusive depois de remover todas
- **THEN** o wizard MUST permanecer na etapa 3
- **AND** MUST apresentar a mensagem “Adicione pelo menos uma foto para continuar.”

#### Scenario: Seleção dentro do limite
- **WHEN** o doador seleciona até cinco imagens aceitas
- **THEN** o sistema MUST apresentar a quantidade e uma miniatura de cada foto e enviá-las, na ordem escolhida, para persistência na publicação

#### Scenario: Miniaturas logo após a escolha
- **WHEN** o doador escolhe imagens aceitas na etapa 3
- **THEN** a interface MUST mostrar, antes da publicação, uma miniatura de cada foto, na ordem atual, com a quantidade “N de 5”
- **AND** MUST indicar que as fotos estão sendo preparadas enquanto as miniaturas não ficam prontas
- **AND** cada miniatura MUST ter texto alternativo com a posição, como “Foto 2 de 3”

#### Scenario: Capa
- **WHEN** há fotos escolhidas
- **THEN** a primeira foto MUST ser a capa e MUST mostrar o selo “Capa”, com texto e não só cor
- **AND** nenhuma outra foto MUST mostrar o selo

#### Scenario: Remover uma foto
- **WHEN** o doador aciona “Remover foto N” numa miniatura
- **THEN** somente essa foto MUST sair da seleção, e as demais MUST manter a ordem relativa
- **AND** se a foto removida era a capa, a próxima MUST passar a ser a capa

#### Scenario: Reordenar sem arrastar
- **WHEN** o doador aciona “Mover para a esquerda” ou “Mover para a direita” numa foto
- **THEN** a foto MUST trocar de lugar com a vizinha daquele lado
- **AND** “Mover para a esquerda” MUST ficar indisponível na primeira foto e “Mover para a direita” na última
- **WHEN** o doador aciona “Tornar capa” numa foto que não é a primeira
- **THEN** essa foto MUST passar para a primeira posição, e as demais MUST manter a ordem relativa
- **AND** “Tornar capa” MUST ficar indisponível na foto que já é a capa

#### Scenario: Escolher mais fotos soma às já escolhidas
- **WHEN** o doador, já com fotos escolhidas, escolhe mais imagens aceitas
- **THEN** as novas MUST entrar depois das já escolhidas, sem substituí-las

#### Scenario: Tentativa de ultrapassar o limite
- **WHEN** o doador tenta manter mais de cinco imagens escolhidas, numa escolha só ou somando escolhas
- **THEN** o sistema MUST aceitar somente as imagens até completar cinco, na ordem da escolha, informar o limite e manter os arquivos já aceitos
- **AND** com cinco fotos, a área de escolha MUST indicar que o limite foi atingido

#### Scenario: Foto com mais de 5 MB
- **WHEN** o doador escolhe uma imagem com mais de 5 MB
- **THEN** a interface MUST recusá-la antes de aceitá-la, com a mensagem “A foto pode ter no máximo 5 MB.”, e MUST manter as fotos já aceitas

#### Scenario: Foto preparada antes do envio
- **WHEN** uma foto é aceita
- **THEN** o arquivo enviado na publicação MUST estar na orientação em que a foto foi tirada (orientação EXIF aplicada)
- **AND** MUST NOT conter metadados do original, como a localização (GPS), a data ou o modelo da câmera
- **AND** MUST ter no máximo 1600 px no lado maior, mantendo a proporção, sem ampliar uma imagem menor
- **AND** MUST ser PNG somente quando a imagem tem algum pixel transparente, preservando a transparência; nos outros casos, inclusive PNG, GIF (primeiro quadro) e WEBP sem transparência, MUST ser JPEG com compressão otimizada
- **AND** o nome enviado MUST ser `foto-N.<ext>`, com N igual à posição na ordem escolhida, sem o nome original do arquivo

#### Scenario: Arquivos guardados durante o cadastro
- **WHEN** fotos escolhidas ficam guardadas no servidor da aplicação até a publicação
- **THEN** o servidor MUST guardar somente a versão preparada de cada foto, nunca o arquivo como foi escolhido, e MUST NOT enviá-la ao navegador além da miniatura
- **AND** MUST apagar a foto guardada quando ela é removida, todas as fotos guardadas quando a publicação é concluída e todas quando o cadastro é reiniciado
- **AND** numa falha de publicação, MUST manter as fotos guardadas para uma nova tentativa

#### Scenario: Arquivo não aceito ou falha no upload
- **WHEN** um arquivo não é uma imagem aceita, não pode ser lido como imagem ou o upload falha
- **THEN** o sistema MUST identificar a falha com a mensagem atual, permitir correção ou nova tentativa, manter as fotos já aceitas e MUST NOT apresentar a doação como publicada

#### Scenario: A ordem escolhida é a ordem salva
- **WHEN** a doação é publicada
- **THEN** as fotos MUST ser enviadas e persistidas na ordem mostrada na etapa 3
- **AND** a capa nos cartões de listagem e a primeira foto do detalhe MUST ser a primeira dessa ordem, seguida das demais na mesma ordem

#### Scenario: Teclado e tela estreita
- **WHEN** a etapa 3 é usada pelo teclado ou numa largura de 360 px
- **THEN** escolher arquivos, remover, mover e tornar capa MUST ser acionáveis pelo teclado, com rótulos acessíveis que incluam a posição da foto (por exemplo, “Remover foto 2”) e foco visível
- **AND** os controles MUST ter área de toque de pelo menos 44 px e contraste mínimo AA
- **AND** as miniaturas e os controles MUST caber sem rolagem horizontal

#### Scenario: Publicação sem fotos pelo endpoint
- **WHEN** uma requisição autenticada ao endpoint de publicação contém `photos` ausente, nulo ou vazio
- **THEN** o backend MUST rejeitar a requisição com erro `inputerror` (HTTP 400) e a mensagem “Adicione pelo menos uma foto para continuar.”
- **AND** MUST NOT criar uma doação, linhas de fotos associadas ou arquivos de imagem sem dono

### Requirement: Entrega e preferência de contato
O sistema MUST apresentar “A combinar” como única modalidade de entrega selecionável e MUST oferecer somente as preferências “E-mail” e “Chat do DoaFácil”. Esta change MUST persistir somente a preferência de contato e MUST NOT solicitar nem persistir telefone, endereço específico ou outro dado pessoal de contato.

#### Scenario: Publicação com entrega e preferência escolhidas
- **WHEN** o doador seleciona uma preferência de contato válida e a modalidade de entrega “A combinar”
- **THEN** ambas as escolhas MUST ser persistidas com a doação
- **AND** o frontend MUST enviar “A combinar”, valor aceito pelo endpoint de publicação existente
- **AND** a preferência MUST ser “E-mail” ou “Chat do DoaFácil”, ambos aceitos pelo endpoint existente

#### Scenario: Opção de contato removida
- **WHEN** o doador escolhe uma preferência de contato
- **THEN** a interface MUST oferecer “E-mail” e “Chat do DoaFácil” e MUST NOT oferecer “WhatsApp”

#### Scenario: Dados pessoais de contato não solicitados
- **WHEN** o doador preenche o passo de contato
- **THEN** a interface MUST apresentar apenas a escolha de preferência e MUST NOT solicitar número de telefone, endereço de contato ou identificador externo

#### Scenario: Aviso de visibilidade do e-mail
- **WHEN** o doador seleciona “E-mail” como preferência de contato na quinta etapa
- **THEN** a interface MUST exibir o aviso curto: “Seu e-mail ficará disponível para pessoas logadas que quiserem falar com você.”
- **AND** MUST manter a seleção da preferência e o restante do fluxo de publicação sem alterar as etapas anteriores

#### Scenario: Escolha de chat sem aviso de e-mail
- **WHEN** o doador seleciona “Chat do DoaFácil” como preferência de contato
- **THEN** a interface MUST NOT exibir o aviso de disponibilidade de e-mail
- **AND** MUST continuar seguindo o comportamento atual do wizard

### Requirement: Legibilidade dos textos de exemplo e seleção
A interface MUST apresentar os textos de exemplo dos campos de texto do cadastro de doação em cinza médio legível, equivalente a `#6B6B6B`, para que não se confundam com texto digitado. Os prompts e textos de seleção MUST usar cor preta ou cinza bem escura, em todas as cinco etapas. O texto digitado ou colado MUST aparecer em cor escura opaca, mais escura que o texto de exemplo, independentemente do tema claro ou escuro do sistema.

#### Scenario: Texto de exemplo dos campos em cinza médio
- **WHEN** o campo “Nome do item” da etapa 1 ou o campo “Descrição” da etapa 2 está vazio
- **THEN** o texto de exemplo MUST usar cor equivalente a `#6B6B6B`, com opacidade total
- **AND** MUST NOT herdar a cor do texto digitado nem aparecer semitransparente

#### Scenario: Placeholders e prompts escuros
- **WHEN** qualquer etapa do cadastro apresenta um prompt de seleção, incluindo “Selecione uma categoria” e “Selecione a condição”
- **THEN** esses prompts MUST usar cor escura equivalente a `#333333` ou mais escura
- **AND** os textos de exemplo dos campos de texto MUST seguir o cenário “Texto de exemplo dos campos em cinza médio”, e não esta regra
- **AND** o placeholder de um Select do Radix MUST manter essa cor no elemento de conteúdo interno marcado pelo estado de placeholder, sem alterar o fundo do controle
- **AND** a regra MUST NOT alterar a aparência das opções na lista aberta

#### Scenario: Preferências de contato legíveis
- **WHEN** a quinta etapa apresenta o prompt e as opções de forma de contato
- **THEN** os textos “Selecione uma forma de contato”, “E-mail” e “Chat do DoaFácil” MUST permanecer em cor escura legível, sem aparência apagada

#### Scenario: Selects com fundo branco
- **WHEN** qualquer etapa apresenta um select (Categoria, Condição do item, Forma de entrega ou Preferência de contato), com ou sem valor escolhido
- **THEN** o botão visível do select MUST ter fundo branco, borda `#C8C8C8`, texto `#1F1F1F` e foco visível em `#007A42`, como os campos de texto
- **AND** MUST NOT aparecer com fundo cinza, como se estivesse desativado

#### Scenario: Foco dos botões do cadastro
- **WHEN** a pessoa navega pelo teclado até “Voltar”, “Continuar” ou “Publicar doação”
- **THEN** o foco MUST aparecer como um anel verde `#007A42`, igual aos outros controles do site, e MUST NOT usar o anel azul do tema

#### Scenario: Texto digitado legível
- **WHEN** a pessoa digita no campo “Nome do item” da etapa 1 ou no campo “Descrição” da etapa 2
- **THEN** o texto digitado MUST usar cor escura equivalente a `#1F1F1F` ou mais escura, com opacidade total
- **AND** MUST NOT herdar cor clara do tema nem aparecer semitransparente

#### Scenario: Texto colado legível
- **WHEN** a pessoa cola um texto num desses campos
- **THEN** o texto colado MUST aparecer com a mesma cor e opacidade do texto digitado

#### Scenario: Tema escuro do sistema
- **WHEN** o sistema operacional ou o navegador está no tema escuro e a pessoa digita num desses campos
- **THEN** o texto MUST continuar escuro e legível sobre o fundo branco do campo

#### Scenario: Placeholder volta ao apagar o texto
- **WHEN** a pessoa digita ou cola um texto em “Nome do item” ou “Descrição” e depois apaga todo o conteúdo
- **THEN** o campo MUST voltar a mostrar o texto de exemplo, em cor equivalente a `#6B6B6B`
- **AND** o valor do campo guardado pelo formulário MUST ficar vazio

### Requirement: Publicação autenticada e persistente
O sistema MUST publicar a doação por meio de uma operação autenticada no Xano. O backend MUST derivar o responsável da sessão autenticada, validar a categoria, a condição, a modalidade de entrega, a preferência de contato e o limite de uma a cinco fotos, e persistir os dados completos. Uma publicação aceita MUST iniciar com status “disponível”, e a interface MUST levar ao detalhe da doação criada. Falhas de validação, autenticação, rede ou persistência MUST ser informadas sem apagar os dados ainda não publicados nem exibir uma confirmação de sucesso.

#### Scenario: Publicação aceita
- **WHEN** uma pessoa autenticada envia dados válidos e o Xano conclui a persistência
- **THEN** a resposta MUST identificar a doação criada, associada ao usuário autenticado, com status “disponível” e com os dados submetidos
- **AND** a interface MUST levar a `/doacao/<id>` da doação criada, que mostra o aviso de publicação (veja “Aviso de doação recém-publicada” em `donation-detail`)
- **AND** um segundo clique em “Publicar doação” durante ou depois do envio MUST NOT criar outra doação

#### Scenario: Requisição sem sessão válida
- **WHEN** uma pessoa não autenticada tenta publicar uma doação
- **THEN** o backend MUST rejeitar a requisição sem criar uma doação nem aceitar um responsável informado pelo cliente

#### Scenario: Falha durante a publicação
- **WHEN** o Xano rejeita a requisição ou ocorre uma falha de rede/persistência
- **THEN** a interface MUST apresentar uma mensagem de erro, manter os valores do wizard, inclusive as fotos e a ordem delas, e MUST NOT mostrar a doação como publicada nem sair do cadastro

#### Scenario: Xano rejeita publicação sem fotos
- **WHEN** o backend rejeita a publicação por não receber fotos
- **THEN** a interface MUST apresentar “Adicione pelo menos uma foto para continuar.” e manter os valores do wizard
- **AND** MUST NOT mostrar a doação como publicada

### Requirement: Reinício do formulário a cada nova entrada
Cada nova entrada em `/cadastro-doacao` MUST iniciar um novo cadastro vazio e habilitado, limpando os dados e estados temporários da visita anterior antes de carregar as categorias e a localização do perfil.

#### Scenario: Nova entrada após publicar uma doação
- **WHEN** a pessoa publica uma doação com sucesso e depois entra novamente em `/cadastro-doacao`
- **THEN** o formulário MUST voltar ao passo 1 com título, descrição, categoria, condição, forma de entrega e preferência de contato vazios
- **AND** MUST limpar mensagens de erro e sucesso, estado de publicação e progresso de upload
- **AND** MUST limpar as fotos escolhidas e as miniaturas

#### Scenario: Troca de conta na mesma aba
- **WHEN** a pessoa publica uma doação, sai da conta, entra com outra conta na mesma aba e abre `/cadastro-doacao`
- **THEN** o formulário MUST iniciar vazio no passo 1, sem dados, fotos ou estado de publicação da conta anterior
- **AND** MUST carregar categorias e cidade/UF do perfil da conta atualmente autenticada

#### Scenario: Recarregar a página de cadastro
- **WHEN** a pessoa recarrega `/cadastro-doacao`
- **THEN** o formulário MUST iniciar vazio no passo 1, limpando também as fotos escolhidas
- **AND** MUST carregar categorias e cidade/UF do perfil autenticado

#### Scenario: Publicação concluída na visita atual
- **WHEN** a publicação é concluída com sucesso
- **THEN** a interface MUST sair do cadastro e abrir o detalhe da doação criada
- **AND** voltar a `/cadastro-doacao` depois disso MUST iniciar um cadastro novo, sem permitir publicar de novo a mesma doação

#### Scenario: Navegação entre os passos preserva os dados
- **WHEN** a pessoa usa “Continuar” e “Voltar” para navegar entre os passos dentro de `/cadastro-doacao`
- **THEN** o sistema MUST NOT reiniciar o formulário durante essa navegação
- **AND** os dados preenchidos nos passos anteriores, inclusive as fotos e a ordem delas, MUST permanecer ao retornar a eles
- **AND** o reinício MUST ocorrer somente na entrada da página, inclusive ao recarregá-la

### Requirement: Posição da seta de retorno do cadastro de doação
A página `/cadastro-doacao` MUST apresentar a seta de retorno na linha do logotipo, à esquerda, no mesmo cabeçalho das outras páginas com “Voltar” (spec `site-navigation`), e não numa faixa própria abaixo do cabeçalho. A posição MUST ser a mesma nas cinco etapas. A seta MUST continuar levando à home (`/`) com o rótulo acessível “Voltar ao início”.

#### Scenario: Seta no canto em tela larga
- **WHEN** a pessoa abre `/cadastro-doacao` numa janela de 1440 px de largura
- **THEN** a seta MUST aparecer na linha do logotipo, à esquerda, alinhada à margem do cabeçalho
- **AND** MUST NOT ficar alinhada à coluna centralizada do formulário nem numa faixa solta abaixo do cabeçalho

#### Scenario: Mesma posição em todas as etapas
- **WHEN** a pessoa navega da etapa 1 à etapa 5 com “Continuar” e volta com “Voltar”
- **THEN** a seta MUST permanecer na mesma posição, sem deslocamento entre etapas

#### Scenario: Seta em tela estreita
- **WHEN** a pessoa abre `/cadastro-doacao` numa largura de celular (360 px)
- **THEN** a seta MUST continuar à esquerda na linha do logotipo, com 44 px de área de toque, sem sobrepor o logotipo, a barra de progresso ou os campos e sem causar rolagem horizontal

#### Scenario: Destino e rótulo preservados
- **WHEN** a pessoa ativa a seta pelo mouse ou pelo teclado
- **THEN** o sistema MUST levar à home (`/`)
- **AND** a seta MUST manter o rótulo acessível “Voltar ao início”

### Requirement: Criação de doação só pela publicação
O backend MUST criar doações somente pela operação de publicação descrita em “Publicação autenticada e persistente”, com as validações dela: de uma a cinco fotos, cidade e UF do perfil, categoria, condição, modalidade de entrega e preferência de contato. Nenhum outro endpoint pode criar uma doação.

#### Scenario: Criação antiga sem as regras da publicação
- **WHEN** qualquer cliente chama `POST catalog/donations`, com ou sem sessão e com qualquer corpo
- **THEN** o backend MUST responder “não encontrado”
- **AND** MUST NOT criar doação

#### Scenario: Publicação preservada
- **WHEN** uma pessoa autenticada publica uma doação pelo cadastro em cinco etapas
- **THEN** a publicação MUST funcionar como antes, com as mesmas validações e respostas

### Requirement: Limites e valores aceitos pelo endpoint de publicação
O endpoint de publicação MUST recusar, com HTTP 400 e sem criar doação, fotos ou arquivos: título com mais de 100 caracteres ou descrição com mais de 2000, depois de tirar os espaços das pontas; entrega diferente de “A combinar”; e preferência de contato diferente de “E-mail” e “Chat do DoaFácil”. São os mesmos limites e valores aceitos pela edição de doação.

#### Scenario: Título longo demais
- **WHEN** uma requisição autenticada envia um título com 101 caracteres
- **THEN** o backend MUST responder HTTP 400 por causa do título, antes de validar as fotos
- **AND** MUST NOT criar doação, linhas de fotos ou arquivos de imagem

#### Scenario: Título no limite
- **WHEN** uma requisição autenticada envia um título com exatamente 100 caracteres e os demais campos válidos
- **THEN** o título MUST ser aceito

#### Scenario: Descrição longa demais
- **WHEN** uma requisição autenticada envia uma descrição com 2001 caracteres
- **THEN** o backend MUST responder HTTP 400 sem criar doação

#### Scenario: Entrega ou contato fora das opções do site
- **WHEN** uma requisição autenticada envia a entrega “Retirada” ou “Entrega”, ou a preferência “WhatsApp”
- **THEN** o backend MUST responder HTTP 400 sem criar doação

#### Scenario: Publicação pelo site continua igual
- **WHEN** uma pessoa publica pelo cadastro em cinco etapas, com título de até 100 caracteres, descrição de até 2000, “A combinar” e “E-mail” ou “Chat do DoaFácil”
- **THEN** a publicação MUST ser aceita como antes

### Requirement: Andamento visível da publicação
Ao acionar “Publicar doação”, a interface MUST mostrar o andamento desde o clique, antes do envio ao backend: o botão com o texto “Publicando...”, desativado, e o aviso “Enviando sua doação...”. O andamento MUST sumir quando a resposta chegar.

#### Scenario: Publicação em andamento
- **WHEN** a pessoa aciona “Publicar doação” com todos os dados válidos
- **THEN** o botão MUST aparecer como “Publicando...”, desativado, e o aviso “Enviando sua doação...” MUST aparecer antes de a resposta do backend chegar
- **AND** a publicação MUST fazer um único pedido ao backend

#### Scenario: Falha depois do andamento
- **WHEN** o backend recusa a publicação ou ocorre uma falha de rede
- **THEN** o aviso “Enviando sua doação...” MUST sumir e o botão MUST voltar a “Publicar doação”, habilitado, com a mensagem de erro e os dados mantidos

#### Scenario: Dados recusados pela tela
- **WHEN** a pessoa aciona “Publicar doação” e algum dado não passa na conferência da tela
- **THEN** a interface MUST mostrar a mensagem de erro sem mostrar o andamento e sem chamar o backend

### Requirement: Tentar de novo no carregamento do cadastro
Quando as categorias ou a localização do perfil não puderem ser carregadas ao abrir o cadastro, a interface MUST oferecer o botão “Tentar de novo”. Acioná-lo MUST mostrar “Preparando seu cadastro...” na hora e buscar os dados outra vez, com os mesmos pedidos da abertura.

#### Scenario: Tentar de novo depois da falha
- **WHEN** o carregamento do cadastro falha e a pessoa aciona “Tentar de novo”
- **THEN** a interface MUST mostrar “Preparando seu cadastro...” antes da resposta do backend
- **AND** com a resposta aceita, MUST mostrar o cadastro pronto para preencher

### Requirement: Aviso legal do cadastro
Acima dos botões de navegação, o cadastro MUST mostrar o aviso “Ao clicar no botão abaixo, você declara que é maior de 18 anos e que leu e concorda com os Termos de uso.”, com “Termos de uso” como link para `/termos`. O aviso MUST NOT citar documentos que o site não tem.

#### Scenario: Ler os Termos durante o cadastro
- **WHEN** a pessoa aciona o link “Termos de uso” do aviso
- **THEN** a página `/termos` MUST abrir em outra aba
- **AND** o cadastro em andamento MUST continuar na aba original, com os dados e as fotos preenchidos

#### Scenario: Texto do aviso
- **WHEN** o cadastro é exibido
- **THEN** o aviso MUST NOT mencionar taxas, prazos ou regulamentos

### Requirement: Título neutro da etapa de contato
A quinta etapa do cadastro MUST ter o título “Como prefere que entrem em contato?”.

#### Scenario: Abrir a etapa de contato
- **WHEN** a pessoa chega à quinta etapa do cadastro
- **THEN** o título MUST ser “Como prefere que entrem em contato?”
