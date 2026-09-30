## Purpose

Apresentar uma experiência navegável de campanhas de arrecadação financeira
para validar a interface de descoberta, detalhe e checkout antes de existir
modelo, API ou provedor de pagamento integrado.

## ADDED Requirements

### Requirement: Feed demonstrativo de campanhas
O sistema SHALL exibir campanhas de exemplo identificadas como dados demonstrativos, com categoria, valor arrecadado, meta, apoiadores e progresso visual, sem apresentá-las como dados persistidos no Xano.

#### Scenario: Visitante visualiza campanhas de exemplo
- **WHEN** o visitante abre a página inicial de vaquinhas
- **THEN** o sistema exibe cartões de campanha com valores e progresso explicitamente demonstrativos

#### Scenario: Visitante filtra campanhas demonstrativas
- **WHEN** o visitante seleciona uma categoria ou pesquisa pelo título
- **THEN** o feed apresenta somente os exemplos correspondentes ao filtro selecionado

### Requirement: Detalhe demonstrativo de campanha
O sistema SHALL apresentar uma página de detalhe com imagem, criador, selo visual, progresso, meta e abas de história, atualizações e recados, identificando o conteúdo como demonstrativo.

#### Scenario: Visitante abre campanha
- **WHEN** o visitante seleciona um cartão do feed
- **THEN** o sistema abre o detalhe da campanha selecionada com o progresso e conteúdo demonstrativos

#### Scenario: Visitante seleciona uma aba de conteúdo
- **WHEN** o visitante seleciona História, Atualizações ou Recados
- **THEN** o sistema exibe o conteúdo de exemplo correspondente à aba

### Requirement: Checkout sem processamento financeiro
O sistema SHALL permitir selecionar valor predefinido ou personalizado, opção visual de anonimato, mensagem de apoio e método visual PIX ou cartão, sem enviar cobrança, criar pagamento ou confirmar doação.

#### Scenario: Visitante prepara uma contribuição demonstrativa
- **WHEN** o visitante informa valor, opção de anonimato, mensagem e método
- **THEN** a interface mantém a seleção no estado de apresentação sem afirmar que houve pagamento

#### Scenario: Visitante escolhe PIX ou cartão
- **WHEN** o visitante seleciona um método de pagamento
- **THEN** a interface informa que o processamento ainda não está integrado e não mostra QR Code ou resultado de transação real

### Requirement: Navegação sem alterar o catálogo de itens
O sistema SHALL manter as campanhas como experiência separada do catálogo de doações de itens e o botão “Criar Doação” SHALL encaminhar ao formulário existente de doação de itens.

#### Scenario: Usuário inicia cadastro de doação de item
- **WHEN** o usuário aciona “Criar Doação” no cabeçalho
- **THEN** o sistema apresenta ou direciona ao formulário já existente para itens

### Requirement: Integração futura com Xano sem sucesso simulado
O sistema SHALL manter pontos de integração explícitos para futuras chamadas GET e POST ao Xano e SHALL distinguir dados demonstrativos de respostas reais, sem usar fixtures como confirmação de persistência ou pagamento.

#### Scenario: API de campanhas ainda não está conectada
- **WHEN** o feed usa campanhas de exemplo locais
- **THEN** a interface marca os dados como demonstrativos e não os apresenta como retorno do Xano

#### Scenario: Checkout sem provedor configurado
- **WHEN** o visitante confirma visualmente os dados de contribuição
- **THEN** nenhuma cobrança é enviada e nenhuma mensagem de sucesso de pagamento é exibida
