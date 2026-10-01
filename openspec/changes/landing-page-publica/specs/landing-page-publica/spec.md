## Purpose

Oferecer uma entrada pública institucional para o DoaFácil que explique a
proposta da plataforma, ajude a descobrir causas demonstrativas e direcione
visitantes aos fluxos existentes sem depender de uma sessão ou backend.

## ADDED Requirements

### Requirement: Landing pública na rota raiz
O sistema SHALL apresentar na rota `/` uma landing page pública com navegação institucional, hero, bloco de descoberta, seção de segurança e confiança, destaques e rodapé, e SHALL renderizar sua estrutura sem exigir chamadas ao backend.

#### Scenario: Visitante abre a raiz
- **WHEN** uma pessoa sem autenticação acessa `/`
- **THEN** o sistema apresenta as seções públicas da landing page e não exige resposta do Xano para renderizá-las

### Requirement: Navegação para fluxos existentes
O sistema SHALL manter a tela atual de autenticação, perfil e catálogo acessível em `/app`, direcionar “Entrar” a esse fluxo e oferecer destinos distintos para catálogo de itens e vaquinhas demonstrativas.

#### Scenario: Visitante acessa a aplicação existente
- **WHEN** o visitante seleciona “Entrar”
- **THEN** o sistema navega para `/app` e preserva os formulários atuais de autenticação e catálogo

#### Scenario: Visitante escolhe explorar vaquinhas
- **WHEN** o visitante seleciona um CTA para explorar campanhas
- **THEN** o sistema navega para a experiência demonstrativa de vaquinhas sem afirmar que são campanhas persistidas

### Requirement: Busca visual com filtros de demonstração
O sistema SHALL permitir filtrar os destaques demonstrativos por palavra-chave, categoria e localidade de exemplo, identificando os resultados como conteúdo ilustrativo.

#### Scenario: Visitante pesquisa destaques
- **WHEN** o visitante envia palavra-chave, categoria ou localidade
- **THEN** o sistema apresenta os exemplos locais que correspondem aos filtros sem exigir API

### Requirement: CTA de criação sem campanha financeira disponível
O sistema SHALL exibir o CTA “Criar Campanha” e SHALL informar no destino que a criação de campanhas financeiras não está disponível nesta etapa.

#### Scenario: Visitante tenta criar uma campanha
- **WHEN** o visitante seleciona “Criar Campanha”
- **THEN** o sistema direciona para `/app#login` e informa que campanhas financeiras ainda não podem ser criadas

### Requirement: Navegação responsiva e conteúdo institucional
O sistema SHALL apresentar links de navegação para Doar, Arrecadar e Sobre, conteúdo institucional de confiança, canais de contacto e políticas, adaptando o layout a telas estreitas sem perder os destinos principais.

#### Scenario: Visitante usa tela estreita
- **WHEN** a landing page é aberta em viewport móvel
- **THEN** as seções e ações permanecem legíveis, utilizáveis e sem rolagem horizontal
