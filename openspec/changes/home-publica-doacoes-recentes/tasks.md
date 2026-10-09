# Tasks

## 1. Contratos públicos do Xano

- [x] 1.1 Executar `xano workspace pull -d ./xano`, revisar diferenças compartilhadas e reconciliar os arquivos do escopo sem descartar alterações locais preexistentes; verificar o estado final com `git diff`.
- [x] 1.2 Consultar a documentação Xano e definir com o Developer MCP a representação opcional da foto e sua URL pública; adicionar à doação foto opcional e condição opcional restrita a Ótimo, Bom ou Regular; validar que registros existentes sem esses campos continuam íntegros.
- [ ] 1.3 Criar endpoint público de doações recentes com até quatro registros disponíveis, ordenados por data de criação decrescente e somente com campos dos cartões; verificar chamada sem autenticação, filtro de status, ordenação, limite, campos retornados e valores ausentes.
- [ ] 1.4 Criar endpoint público de contagem de doações disponíveis; verificar chamada sem autenticação, contagem de todos os registros disponíveis e resposta zero sem registros disponíveis.
- [x] 1.5 Validar com o Xano Developer MCP todos os arquivos XanoScript alterados e executar `xano workspace push -d ./xano --dry-run`; revisar que o plano contém apenas o escopo desta change e não executar push como parte dessas tasks.

## 2. Home pública no Reflex

- [x] 2.1 Usar `assets/logo.svg`, `assets/doacao-generica.svg` e `assets/ilustracao-rodape.png`; aplicar a fonte LINE Seed JP por stylesheet do app com alternativas de sistema, conferir a paleta disponível nos recursos e nas referências PNG e não reproduzir a captura inteira.
- [x] 2.2 Integrar a página Reflex aos endpoints públicos de recentes e contagem; verificar estados de carregamento e falha independentes, sem converter falhas em zero ou lista vazia.
- [x] 2.3 Implementar cabeçalho, frase de destaque, contagem e seção de cartões conforme o README de design; verificar presença dos elementos, ausência de “Pessoas alcançadas” e ausência da seção institucional/rodapé escuro.
- [x] 2.4 Implementar cartões com etiqueta “NOVO” baseada em `created_at` nos últimos sete dias, fallback de imagem, texto “Condição não informada” e botão “Acessar” sem navegação; adicionar verificações para itens com e sem dados opcionais e para os limites temporais da etiqueta.
- [x] 2.5 Implementar e verificar o estado vazio da seção quando não há doações recentes, mantendo visíveis os demais elementos da home.

## 3. Verificação integrada

- [ ] 3.1 Executar as verificações automatizadas relevantes do Reflex e percorrer manualmente a home com respostas reais ou controladas dos endpoints; confirmar visualmente o layout contra as referências aprovadas e registrar os comandos/resultados usados para validar a change.
- [x] 3.2 Atualizar spec e design para registrar o carrossel horizontal de uma linha, o descarte isolado de itens inválidos e o layout sem sobreposição no estado de erro; implementar e cobrir esses comportamentos com testes, sem alterar Xano, endpoints ou a primeira tela fora da seção de doações recentes.
- [x] 3.3 Executar `python -m unittest discover -s tests -v` e verificar no navegador, inclusive em viewport de 390px, que o carrossel permanece em uma linha com rolagem horizontal e que a contagem/erro não se sobrepõem.
- [x] 3.4 Reservar 14rem para a contagem em telas largas, permitir quebra do rótulo, manter o carrossel no espaço restante e confirmar a ausência de sobreposição ou rolagem horizontal da página em 1440px, 1024px e 390px.
