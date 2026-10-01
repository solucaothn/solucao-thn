## Context

Consulte [proposal.md](./proposal.md) para motivação e
[spec.md](./specs/landing-page-publica/spec.md) para o comportamento esperado.
O app Reflex atual tem uma página única com login, perfil e catálogo, além de
rotas demonstrativas de campanhas. As fixtures de campanha ainda não contêm
localização; esta Change adicionará apenas localidades fictícias para filtrar
na interface.

## Goals / Non-Goals

**Goals:**

- Usar a rota raiz como página pública e manter a tela existente em `/app`.
- Reutilizar fixtures demonstrativas, sem realizar chamadas de backend no
  carregamento da landing.
- Manter os destinos dos CTAs honestos sobre o que está e não está disponível.
- Construir as seções com componentes nativos Reflex e tokens compartilhados
  da paleta do produto.

**Non-Goals:**

- Alterar as APIs ou tabelas do Xano e a Change ativa de busca.
- Transformar campanhas demonstrativas em campanhas reais.
- Implementar pesquisa geográfica real ou geocodificação.
- Implementar criação de campanhas financeiras.

## Decisions

### Preservar a página de aplicação em uma nova rota

A função atual que atende `/` será preservada e registrada em `/app`, mantendo
seu `on_load` de hidratação de autenticação e catálogo. A nova landing será
registrada em `/` sem handler que consulte o Xano.

Alternativa descartada: remover ou substituir a tela de aplicação, pois isso
quebraria os fluxos existentes de autenticação, perfil e catálogo.

### Buscar somente em fixtures demonstrativas nesta entrega

A busca da landing filtrará campanhas locais por título, categoria e
localidade fictícia. O bloco informará claramente que os resultados são
exemplos e não enviará parâmetros para endpoints inexistentes.

Alternativa descartada: conectar à busca real do catálogo, pois a API atual
busca doações de itens e não campanhas financeiras.

### Rota de criação de campanha ainda indisponível

“Criar Campanha” levará a `/app#login`, e a tela `/app` explicará que campanha
financeira ainda não pode ser criada. “Arrecadar”/“Explorar campanhas” seguirá
para `/vaquinhas`.

Alternativa descartada: apresentar sucesso ou abrir um formulário sem
persistência, pois isso poderia sugerir que uma campanha foi criada.

### Estrutura em seções e componentes Reflex

A landing terá cabeçalho, hero, busca, confiança, cards e rodapé em módulo
separado, usando componentes nativos, grids responsivos e os tokens de
`theme.py`.

Alternativa descartada: ampliar ainda mais a página monolítica de autenticação,
pois isso tornaria a separação entre landing pública e aplicação interna menos
clara.

## Risks / Trade-offs

- **[Exemplos confundidos com resultados reais]** → Identificar fixtures e
  progresso como demonstrativos em banner e cards.
- **[Localidade fictícia confundida com busca real]** → Rotular o filtro como
  demonstração e não chamar APIs.
- **[Links ao formulário em tela pequena]** → Verificar navegação responsiva e
  destino/âncoras em browser.
- **[Alteração de rota impactar hidratação]** → Manter o `on_load` da tela atual
  exclusivamente em `/app`.

## Migration Plan

1. Criar o módulo da landing e componentes auxiliares.
2. Associar os campos de localidade demonstrativa às fixtures.
3. Registrar a nova raiz e mover a página existente para `/app`.
4. Compilar Reflex, validar OpenSpec e verificar as rotas visualmente.
5. Reverter removendo a rota nova e apontando `/` novamente à função legada,
   sem migração ou alteração de dados.
