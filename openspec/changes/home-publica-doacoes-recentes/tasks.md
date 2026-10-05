# Tasks

## 1. Contratos públicos do Xano

- [x] 1.1 Executar `xano workspace pull -d ./xano`, revisar diferenças compartilhadas e reconciliar os arquivos do escopo sem descartar alterações locais preexistentes; verificar o estado final com `git diff`.
- [x] 1.2 Consultar a documentação Xano e definir com o Developer MCP a representação opcional da foto e sua URL pública; adicionar à doação foto opcional e condição opcional restrita a Ótimo, Bom ou Regular; validar que registros existentes sem esses campos continuam íntegros.
- [ ] 1.3 Criar endpoint público de doações recentes com até quatro registros disponíveis, ordenados por data de criação decrescente e somente com campos dos cartões; verificar chamada sem autenticação, filtro de status, ordenação, limite, campos retornados e valores ausentes.
- [ ] 1.4 Criar endpoint público de contagem de doações disponíveis; verificar chamada sem autenticação, contagem de todos os registros disponíveis e resposta zero sem registros disponíveis.
- [x] 1.5 Validar com o Xano Developer MCP todos os arquivos XanoScript alterados e executar `xano workspace push -d ./xano --dry-run`; revisar que o plano contém apenas o escopo desta change e não executar push como parte dessas tasks.

## 2. Home pública no Reflex

- [x] 2.1 Usar `assets/logo.svg` e `assets/doacao-generica.svg`, conferir a paleta disponível nos recursos e nas referências PNG e não reproduzir a captura inteira; como a ilustração de pessoas não chegou, omiti-la sem substituto e deixar TODO no código. Registrar que o Figma respondeu 403 e que a escolha exata de fontes fica pendente de acesso.
- [x] 2.2 Integrar a página Reflex aos endpoints públicos de recentes e contagem; verificar estados de carregamento e falha independentes, sem converter falhas em zero ou lista vazia.
- [x] 2.3 Implementar cabeçalho, frase de destaque, contagem e seção de cartões conforme o README de design; verificar presença dos elementos, ausência de “Pessoas alcançadas” e ausência da seção institucional/rodapé escuro.
- [x] 2.4 Implementar cartões com etiqueta “NOVO” baseada em `created_at` nos últimos sete dias, fallback de imagem, texto “Condição não informada” e botão “Acessar” sem navegação; adicionar verificações para itens com e sem dados opcionais e para os limites temporais da etiqueta.
- [x] 2.5 Implementar e verificar o estado vazio da seção quando não há doações recentes, mantendo visíveis os demais elementos da home.

## 3. Verificação integrada

- [ ] 3.1 Executar as verificações automatizadas relevantes do Reflex e percorrer manualmente a home com respostas reais ou controladas dos endpoints; confirmar visualmente o layout contra as referências aprovadas e registrar os comandos/resultados usados para validar a change.
