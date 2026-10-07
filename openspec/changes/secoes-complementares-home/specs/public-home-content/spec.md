# Spec Delta

## Purpose

Define as seções complementares da home pública do DoaFácil, apresentando caminhos de entrada, informações institucionais e links úteis sem depender de páginas que ainda não foram criadas.

## ADDED Requirements

### Requirement: Ordem do conteúdo complementar
A home SHALL apresentar as seções complementares em uma ordem definida após as doações recentes.

#### Scenario: Percorrer as seções da home
- **WHEN** uma pessoa percorre a home pública de cima para baixo
- **THEN** “Comece por aqui” aparece abaixo de “Doações mais recentes”
- **AND** a seção institucional aparece depois de “Comece por aqui”
- **AND** o rodapé aparece depois da seção institucional, no final da página

### Requirement: Seção Comece por aqui
A home SHALL apresentar a seção “Comece por aqui” abaixo das doações recentes com o conteúdo aprovado no design.

#### Scenario: Exibir as opções de entrada
- **WHEN** uma pessoa acessa a home pública
- **THEN** a seção apresenta a etiqueta “COMECE POR AQUI”, o título “Quer criar uma doação?” e os cartões “Para você mesmo”, “Ajude quem precisa” e “Desapego em grupo” com seus textos de apoio
- **AND** os dois primeiros cartões exibem uma seta decorativa sem navegação
- **AND** o cartão “Desapego em grupo” exibe “Em breve” e não exibe seta
- **AND** a seção não apresenta barra de busca

### Requirement: Conteúdo institucional da home
A home SHALL apresentar o título, o texto de apoio e os cartões institucionais definidos para o DoaFácil.

#### Scenario: Exibir a seção e seus cartões
- **WHEN** uma pessoa acessa a home pública
- **THEN** a seção apresenta “Doar no DoaFácil é simples e seguro.”
- **AND** apresenta o texto “Doações já circularam por aqui, conectando quem tem com quem precisa. Transparência em cada etapa, do anúncio à entrega.”
- **AND** apresenta quatro cartões com ícone, categoria, título e “Saiba mais”: Solidariedade — “Conheça histórias de quem doou e quem recebeu”; Segurança — “Como funciona a autenticação e proteção dos seus dados”; Nossa missão — “Descubra por que criamos o DoaFácil”; Passo a passo — “Veja como criar sua doação em poucos minutos”
- **AND** os cartões usam degradês verde e cinza, sem fotos ou vídeos
- **AND** os controles “Saiba mais” não navegam para outra página

### Requirement: Rodapé público da home
A home SHALL apresentar um rodapé escuro com a identidade e os links rápidos aprovados.

#### Scenario: Exibir o rodapé sem elementos herdados
- **WHEN** uma pessoa acessa a home pública
- **THEN** o rodapé apresenta o logotipo, o título “Links rápidos”, os links “Quem somos”, “Doações”, “Criar doações”, “Doações mais recentes”, “Política de privacidade”, “Termos de uso”, “Dúvidas frequentes” e “Segurança e transparência”
- **AND** apresenta a linha “Projeto acadêmico DoaFácil”
- **AND** os links não navegam para outra página
- **AND** não apresenta selo de segurança, CNPJ, cidade, horário de atendimento, “Busca por recibo” ou “Verificação de links”

### Requirement: Layout responsivo das seções complementares
As seções “Comece por aqui” e institucional SHALL adaptar a disposição dos cartões à largura disponível.

#### Scenario: Visualização em tela estreita
- **WHEN** a home é exibida em uma tela estreita
- **THEN** os cartões de cada seção são dispostos em coluna e permanecem legíveis sem sobreposição
