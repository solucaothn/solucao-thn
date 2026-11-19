## MODIFIED Requirements

### Requirement: Conteúdo institucional da home
A home SHALL apresentar o título, o texto de apoio e os cartões institucionais definidos para o DoaFácil, sem imagens de terceiros com marca d'água. Cada cartão SHALL mostrar, como fundo, um vídeo curto próprio do projeto, decorativo e sem som, com a sua capa.

#### Scenario: Exibir a seção e seus cartões
- **WHEN** uma pessoa acessa a home pública
- **THEN** a seção apresenta “Doar no DoaFácil é simples e seguro.”
- **AND** apresenta o texto “Doações já circularam por aqui, conectando quem tem com quem precisa. Transparência em cada etapa, do anúncio à entrega.”
- **AND** apresenta quatro cartões quadrados, cada um com ícone em círculo verde, categoria e título: Solidariedade — “Histórias que continuam”; Segurança — “Você no controle”; Nossa missão — “Nada se perde”; Passo a passo — “Doar leva minutos”
- **AND** os cartões não apresentam “Saiba mais” nem navegam

#### Scenario: Imagem dos cartões
- **WHEN** a home é exibida sem preferência por movimento reduzido
- **THEN** cada cartão MUST mostrar o seu vídeo próprio (`solidariedade`, `seguranca`, `missao` e `passo-a-passo`), tocando sozinho, sem som, em repetição e dentro da página no celular, preenchendo o cartão sem distorcer
- **AND** antes de o vídeo carregar, ou se ele não carregar, o cartão MUST mostrar a capa do vídeo
- **AND** o texto do cartão MUST continuar legível, sobre o gradiente escuro na parte de baixo, com contraste mínimo AA sobre a capa

#### Scenario: Movimento reduzido
- **WHEN** a pessoa prefere movimento reduzido (`prefers-reduced-motion: reduce`)
- **THEN** nenhum vídeo MUST tocar, e cada cartão MUST mostrar só a capa

#### Scenario: Vídeo decorativo
- **WHEN** um leitor de tela ou o teclado percorre a seção
- **THEN** os vídeos MUST ficar ocultos para o leitor de tela, sem controles e fora da ordem do Tab
- **AND** passar o mouse ou clicar no vídeo MUST NOT mostrar controles do navegador (picture-in-picture, “pular”, transmissão, velocidade, tela cheia ou download), e o vídeo MUST NOT receber cliques
- **AND** o texto acessível de cada cartão MUST ser o rótulo e o título

#### Scenario: Cartões em 360 px
- **WHEN** a home é exibida com 360 px de largura
- **THEN** os cartões com vídeo MUST caber sem rolagem horizontal da página
