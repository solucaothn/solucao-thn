# public-home-content Specification

## Purpose

Define as seções complementares da home pública do DoaFácil, apresentando caminhos de entrada, informações institucionais e links úteis sem depender de páginas que ainda não foram criadas.

## Requirements

### Requirement: Ordem do conteúdo complementar
A home SHALL preservar a ilustração em largura total, encostada à base da seção de doações recentes, e apresentar as seções complementares na ordem definida, sem faixa de fundo creme separando a ilustração de “Comece por aqui”.

#### Scenario: Percorrer as seções da home
- **WHEN** uma pessoa percorre a home pública de cima para baixo
- **THEN** a ilustração de pessoas permanece logo abaixo de “Doações mais recentes”
- **AND** a ilustração ocupa toda a largura e encosta na base da seção
- **AND** “Comece por aqui” aparece abaixo da ilustração
- **AND** não há faixa creme separando a ilustração de “Comece por aqui”
- **AND** a seção institucional aparece depois de “Comece por aqui”
- **AND** o rodapé aparece depois da seção institucional, no final da página

### Requirement: Primeira dobra da home
A primeira tela da home SHALL agrupar cabeçalho, destaque, doações recentes e ilustração em uma área com altura mínima de 100vh, posicionando a ilustração no limite inferior quando o conteúdo couber, sem cortar conteúdo quando ultrapassar a altura da janela.

#### Scenario: Exibir o início da home na altura da janela
- **WHEN** a home é exibida em uma janela com espaço vertical suficiente
- **THEN** cabeçalho, frase de destaque, doações recentes e ilustração ocupam a primeira tela
- **AND** a ilustração encosta à borda inferior da primeira tela
- **AND** nenhum elemento de “Comece por aqui”, nem sua etiqueta, aparece antes da rolagem
- **WHEN** o conteúdo inicial excede a altura da janela
- **THEN** a primeira área cresce para acomodá-lo sem cortar conteúdo

### Requirement: Seção Comece por aqui
A home SHALL apresentar a seção “Comece por aqui” abaixo da ilustração, com o conteúdo aprovado no design, cartões que levam às áreas correspondentes e uma barra de busca que abre Explorar doações com os filtros escolhidos.

#### Scenario: Exibir as opções de entrada
- **WHEN** uma pessoa acessa a home pública
- **THEN** a seção apresenta a etiqueta “COMECE POR AQUI”, em verde com contraste mínimo AA sobre o fundo, o título “Quer criar uma doação?” e a frase “Leva só alguns minutos: conte o que você quer doar e a gente conecta você a quem precisa.”
- **AND** a frase de apoio aparece maior e em negrito
- **AND** a seção apresenta os cartões “Para você mesmo”, “Ajude quem precisa” e “Desapego em grupo” com seus textos de apoio
- **AND** a seção usa aproximadamente 2.5rem de padding superior e aproximadamente 5rem de padding inferior
- **AND** há aproximadamente 1rem entre etiqueta e título, 1.5rem entre título e frase, 3rem entre frase e cartões, e 3rem entre cartões e barra de busca
- **AND** o título tem line-height de aproximadamente 1.2 e a frase tem line-height de aproximadamente 1.4
- **AND** os cartões usam gap aproximado de 1.5rem e padding interno aproximado de 2rem, com conteúdo superior alinhado e seta ou “Em breve” no rodapé

#### Scenario: Cartões que navegam
- **WHEN** uma pessoa aciona o cartão “Para você mesmo”, pelo mouse ou pelo teclado
- **THEN** a página `/explorar` MUST ser aberta
- **WHEN** uma pessoa aciona o cartão “Ajude quem precisa”
- **THEN** a página `/cadastro-doacao` MUST ser aberta
- **AND** os dois cartões MUST ser links inteiros com rótulo acessível, seta decorativa e foco visível

#### Scenario: Cartão ainda indisponível
- **WHEN** a seção é exibida
- **THEN** o cartão “Desapego em grupo” MUST exibir “Em breve”, sem seta e sem navegação

#### Scenario: Barra de busca
- **WHEN** a seção é exibida
- **THEN** a barra apresenta o campo “Buscar doações” com o placeholder “O que você está procurando?”, o seletor “Categoria” com “Todas as categorias” seguido das categorias retornadas pelo backend, o seletor “Localização” com “Todas as localizações” seguido das 27 UFs e o botão “Buscar”
- **AND** o campo e os seletores têm fundo branco, borda cinza clara e texto digitado em #333; o placeholder usa a cor #6b6b6b com opacidade 1, e os valores dos seletores usam cinza escuro legível, sem aparência desabilitada
- **AND** em telas estreitas os campos e o botão ficam em coluna

#### Scenario: Buscar com filtros
- **WHEN** uma pessoa preenche ou escolhe qualquer combinação de texto, categoria e UF e aciona “Buscar”, pelo botão ou com Enter no campo
- **THEN** a página `/explorar` MUST ser aberta com os parâmetros `q` (texto sem espaços nas pontas), `categoria` (id da categoria) e `uf` (sigla), somente para os filtros escolhidos
- **AND** sem nenhum filtro, MUST abrir `/explorar` sem parâmetros

#### Scenario: Categorias indisponíveis
- **WHEN** o backend não retorna as categorias
- **THEN** o seletor “Categoria” MUST oferecer só “Todas as categorias”, e a busca MUST continuar funcionando com texto e UF

### Requirement: Conteúdo institucional da home
A home SHALL apresentar o título, o texto de apoio e os cartões institucionais definidos para o DoaFácil, sem imagens de terceiros com marca d'água.

#### Scenario: Exibir a seção e seus cartões
- **WHEN** uma pessoa acessa a home pública
- **THEN** a seção apresenta “Doar no DoaFácil é simples e seguro.”
- **AND** apresenta o texto “Doações já circularam por aqui, conectando quem tem com quem precisa. Transparência em cada etapa, do anúncio à entrega.”
- **AND** apresenta quatro cartões quadrados, cada um com ícone em círculo verde, categoria e título: Solidariedade — “Histórias que continuam”; Segurança — “Você no controle”; Nossa missão — “Nada se perde”; Passo a passo — “Doar leva minutos”
- **AND** os cartões não apresentam “Saiba mais” nem navegam

#### Scenario: Imagem dos cartões
- **WHEN** ainda não há fotos próprias aprovadas para os cartões
- **THEN** cada cartão MUST usar um placeholder próprio do projeto (fundo em degradê verde e cinza), sem foto de banco de imagens nem marca d'água
- **AND** o texto do cartão MUST manter contraste mínimo AA sobre o fundo

### Requirement: Rodapé público da home
A home SHALL apresentar um rodapé escuro com a identidade e os links rápidos aprovados, com cada link levando à sua rota.

#### Scenario: Exibir o rodapé sem elementos herdados
- **WHEN** uma pessoa acessa a home pública
- **THEN** o rodapé apresenta o logotipo e, abaixo dele, as colunas “Fale conosco” e “Links rápidos”
- **AND** o logotipo do rodapé usa o arquivo colorido sem filtros ou recoloração
- **AND** “Links rápidos” apresenta os links “Quem somos”, “Doações”, “Criar doações”, “Doações mais recentes”, “Política de privacidade”, “Termos de uso”, “Dúvidas frequentes” e “Segurança e transparência” em tamanho reduzido e com pouco espaço entre linhas
- **AND** os títulos do rodapé usam 15px, os links e “Clique aqui para falar conosco” usam 13px com espaço de 6px entre as linhas, e “Projeto acadêmico DoaFácil” usa 12px
- **AND** “Clique aqui para falar conosco” não é sublinhado
- **AND** as colunas ficam lado a lado em telas largas e em coluna em telas estreitas
- **AND** apresenta a linha “Projeto acadêmico DoaFácil”
- **AND** não apresenta selo de segurança, CNPJ, cidade, horário de atendimento, “Busca por recibo” ou “Verificação de links”

#### Scenario: Destinos dos links
- **WHEN** uma pessoa aciona um link do rodapé
- **THEN** “Clique aqui para falar conosco” MUST levar a `/contato`, “Quem somos” a `/quem-somos`, “Doações” a `/explorar`, “Criar doações” a `/cadastro-doacao`, “Doações mais recentes” a `/#doacoes-recentes`, “Política de privacidade” a `/privacidade`, “Termos de uso” a `/termos`, “Dúvidas frequentes” a `/duvidas` e “Segurança e transparência” a `/seguranca`
- **AND** os links MUST ter foco visível e contraste mínimo AA sobre o fundo escuro

### Requirement: Layout responsivo das seções complementares
As seções “Comece por aqui” e institucional SHALL adaptar a disposição dos cartões à largura disponível, sem rolagem horizontal da página.

#### Scenario: Visualização em tela estreita
- **WHEN** a home é exibida em uma tela estreita
- **THEN** os cartões de cada seção são dispostos em coluna e permanecem legíveis sem sobreposição

#### Scenario: Visualização em 360 px
- **WHEN** a home inteira é exibida com 360 px de largura
- **THEN** nenhuma seção, do cabeçalho ao rodapé, MUST causar rolagem horizontal da página
- **AND** só o carrossel de doações recentes MAY rolar horizontalmente, dentro dele
