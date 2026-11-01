# Proposal

## Why

A página `/doacao/<id>` não oferece um caminho de retorno para a home. Quem chega pelo botão “Acessar” pode ficar sem saída, especialmente quando o identificador é inválido, a doação não é encontrada ou ocorre uma falha de rede.

## What Changes

- Adicionar à página de detalhe um botão “Voltar” com seta verde, posicionado no canto superior esquerdo logo abaixo do cabeçalho, levando para `/`.
- Manter o botão visível durante o carregamento, quando a doação está carregada, quando não é encontrada (inclusive com ID inválido) e quando ocorre erro de rede.
- Disponibilizar o rótulo acessível “Voltar” para leitores de tela.
- Registrar em `docs/design/README.md`, na seção do detalhe, que o botão é um acréscimo fora do Figma.
- Adicionar testes `unittest` dos estados e do destino de navegação, preservando os testes existentes.

## Capabilities

### New Capabilities

Nenhuma.

### Modified Capabilities

- `donation-detail`: acrescentar um requisito para o botão de retorno presente em todos os estados da página e com destino à home.

## Impact

- **Frontend Reflex:** página `/doacao/<id>` e seus estados de carregamento, sucesso, não encontrada e erro.
- **Documentação visual:** seção “Detalhe da doação” em `docs/design/README.md`.
- **Testes:** cobertura `unittest` do botão nos estados e de sua navegação para `/`; a suíte existente, atualmente com 136 testes na main, deve continuar passando sem alterações.
- **Fora do escopo:** alterações no Xano, login, home, regras de privacidade, conteúdo aprovado do detalhe e implementação de outras funcionalidades.
