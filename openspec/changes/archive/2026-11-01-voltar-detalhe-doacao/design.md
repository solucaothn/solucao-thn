# Design

## Context

Veja [proposal.md](./proposal.md) para a motivação e [specs/donation-detail/spec.md](./specs/donation-detail/spec.md) para o comportamento esperado. A página Reflex de detalhe já exibe um cabeçalho comum e alterna o conteúdo entre carregamento, não encontrada, erro e doação carregada. As telas de login e cadastro da doação já têm links acessíveis que retornam à home.

## Goals / Non-Goals

**Goals:**
- Usar o padrão visual já adotado para retorno: seta verde no canto superior esquerdo, logo abaixo do cabeçalho.
- Garantir que o controle seja apresentado em todos os estados e leve para `/`.
- Dar ao controle iconográfico o rótulo acessível “Voltar”.

**Non-Goals:**
- Alterar a navegação, o conteúdo ou os estados da home, login ou Xano.
- Modificar os dados, ações de contato ou regras de privacidade do detalhe.

## Decisions

### Manter o controle fora da renderização condicional dos estados

Adicionar o link de retorno como elemento comum logo após o cabeçalho e antes da condição que alterna o conteúdo da página. Assim, a transição entre carregamento, detalhe carregado, não encontrada e erro não remove o controle. O link aponta diretamente para `/` e usa a seta verde já adotada no cadastro de doação, com rótulo acessível exatamente “Voltar”.

Uma alternativa seria incluir o link separadamente em cada estado. Ela foi descartada porque duplica o componente e pode deixar algum estado sem a ação.

### Alinhar e posicionar como os retornos existentes

Usar a mesma faixa abaixo do cabeçalho e o alinhamento à esquerda dos links de retorno existentes, preservando margens responsivas para celular e computador. O controle é um acréscimo fora do Figma; sua inclusão também será anotada na seção “Detalhe da doação” de `docs/design/README.md`.

## Risks / Trade-offs

- **O controle pode desaparecer em uma condição de estado:** mantê-lo como irmão comum do seletor de conteúdo e cobrir cada estado com testes.
- **A seta pode não ter nome acessível:** definir o rótulo acessível “Voltar” e verificar isso no teste do componente.
- **A posição pode não se adaptar bem a telas estreitas:** manter o limite de largura e o padding responsivo já utilizados pela página e conferir celular e computador no navegador.

## Migration Plan

1. Implementar o link no layout compartilhado do detalhe e acrescentar testes unitários de presença nos estados e de destino `/`.
2. Atualizar a documentação visual em `docs/design/README.md`.
3. Executar a suíte `unittest` completa e verificar os estados e o posicionamento no navegador.

Não há migração de dados nem mudança de API.

## Open Questions

Nenhuma.
