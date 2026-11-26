## MODIFIED Requirements

### Requirement: Seção Comece por aqui
A home SHALL apresentar a seção “Comece por aqui” abaixo da ilustração, com o conteúdo aprovado no design, cartões que levam às áreas correspondentes e uma barra de busca que abre Explorar doações com os filtros escolhidos.

#### Scenario: Exibir as opções de entrada
- **WHEN** uma pessoa acessa a home pública
- **THEN** a seção apresenta a etiqueta “COMECE POR AQUI”, em verde com contraste mínimo AA sobre o fundo, o título “Quer criar uma doação?” e a frase “Leva só alguns minutos: conte o que você quer doar e a gente conecta você a quem precisa.”
- **AND** a frase de apoio aparece maior e em negrito
- **AND** a seção apresenta os cartões “Para você”, “Ajude quem precisa” e “Desapego em grupo” com seus textos de apoio
- **AND** a seção usa aproximadamente 2.5rem de padding superior e aproximadamente 5rem de padding inferior
- **AND** há aproximadamente 1rem entre etiqueta e título, 1.5rem entre título e frase, 3rem entre frase e cartões, e 3rem entre cartões e barra de busca
- **AND** o título tem line-height de aproximadamente 1.2 e a frase tem line-height de aproximadamente 1.4
- **AND** os cartões usam gap aproximado de 1.5rem e padding interno aproximado de 2rem, com conteúdo superior alinhado e seta ou “Em breve” no rodapé

#### Scenario: Cartões que navegam
- **WHEN** uma pessoa aciona o cartão “Para você”, pelo mouse ou pelo teclado
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
