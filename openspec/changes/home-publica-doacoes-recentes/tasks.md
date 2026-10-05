# Tasks

## 1. Contratos públicos do Xano

- [ ] 1.1 Executar `xano workspace pull -d ./xano`, revisar diferenças compartilhadas e reconciliar os arquivos do escopo sem descartar alterações locais preexistentes; verificar o estado final com `git diff`.
- [ ] 1.2 Consultar a documentação Xano e definir com o Developer MCP a representação opcional da foto e sua URL pública; adicionar à doação foto opcional e condição opcional restrita a Ótimo, Bom ou Regular; validar que registros existentes sem esses campos continuam íntegros.
- [ ] 1.3 Criar endpoint público de doações recentes com até quatro registros disponíveis, ordenados por data de criação decrescente e somente com campos dos cartões; verificar chamada sem autenticação, filtro de status, ordenação, limite, campos retornados e valores ausentes.
- [ ] 1.4 Criar endpoint público de contagem de doações disponíveis; verificar chamada sem autenticação, contagem de todos os registros disponíveis e resposta zero sem registros disponíveis.
- [ ] 1.5 Validar com o Xano Developer MCP todos os arquivos XanoScript alterados e executar `xano workspace push -d ./xano --dry-run`; revisar que o plano contém apenas o escopo desta change e não executar push como parte dessas tasks.

## 2. Home pública no Reflex

- [ ] 2.1 Disponibilizar no projeto os recursos visuais aprovados necessários à home — logotipo, ilustração do rodapé e imagem genérica — e extrair cores e fontes do Figma; verificar que os arquivos locais existem e não se usa a captura de tela inteira como interface.
- [ ] 2.2 Integrar a página Reflex aos endpoints públicos de recentes e contagem; verificar estados de carregamento e falha independentes, sem converter falhas em zero ou lista vazia.
- [ ] 2.3 Implementar cabeçalho, frase de destaque, contagem, seção de cartões e ilustração no rodapé conforme o README de design; verificar presença dos elementos e ausência de “Pessoas alcançadas”.
- [ ] 2.4 Implementar cartões com etiqueta “NOVO” baseada em `created_at` nos últimos sete dias, fallback de imagem, texto “Condição não informada” e botão “Acessar” sem navegação; adicionar verificações para itens com e sem dados opcionais e para os limites temporais da etiqueta.
- [ ] 2.5 Implementar e verificar o estado vazio da seção quando não há doações recentes, mantendo visíveis os demais elementos da home.

## 3. Verificação integrada

- [ ] 3.1 Executar as verificações automatizadas relevantes do Reflex e percorrer manualmente a home com respostas reais ou controladas dos endpoints; confirmar visualmente o layout contra as referências aprovadas e registrar os comandos/resultados usados para validar a change.
