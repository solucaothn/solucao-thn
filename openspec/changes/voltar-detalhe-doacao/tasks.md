# Tasks

## 1. Botão Voltar do detalhe

- [ ] 1.1 Adicionar o link compartilhado “Voltar” logo abaixo do cabeçalho e fora da condição dos estados, usando seta verde, destino `/` e rótulo acessível “Voltar”; verificar na renderização da página que o controle permanece fora dos ramos de carregamento, sucesso, não encontrada e erro.
- [ ] 1.2 Acrescentar testes `unittest` que verifiquem a presença do controle e seu rótulo acessível durante carregamento, com doação carregada, com ID inválido/não encontrada e em erro de rede/resposta inválida, além do destino `/`; executar os testes focados e manter os testes existentes passando sem alteração.
- [ ] 1.3 Atualizar `docs/design/README.md`, na seção “Detalhe da doação”, registrando o botão Voltar e sua seta como acréscimo que não está no Figma; conferir que a nota fica junto aos outros acréscimos documentados.

## 2. Verificação manual

- [ ] 2.1 (manual) Conferir no navegador, em celular e computador, que o controle aparece durante carregamento, com a doação carregada, em “Doação não encontrada” (inclusive ID inválido) e em erro de rede; confirmar o rótulo acessível “Voltar”, a posição abaixo do cabeçalho e à esquerda, e que o clique navega para `/`. O Copilot não marca esta tarefa como concluída.
