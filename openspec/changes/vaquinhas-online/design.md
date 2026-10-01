## Context

Ver [proposal.md](./proposal.md) para motivação e escopo e
[spec.md](./specs/interface-demonstrativa-vaquinhas/spec.md) para o contrato de
comportamento. O Reflex atual usa uma aplicação principal em
`solucao_thn/solucao_thn.py` e um cliente Xano em `solucao_thn/xano_api.py`.
O catálogo existente representa itens físicos, não campanhas financeiras.

## Goals / Non-Goals

**Goals:**

- Adicionar páginas modulares Reflex sem substituir a página atual do catálogo.
- Tornar dados de exemplo e estado de checkout claramente não transacionais.
- Deixar pontos de integração para GET/POST futuros, sem chamar endpoints
  inexistentes nem armazenar uma alegada confirmação.
- Usar componentes nativos Reflex e a paleta visual definida pelo produto.

**Non-Goals:**

- Definir tabelas, regras financeiras, endpoints Xano ou autorização de
  campanhas.
- Integrar PIX, cartão, QR Code, adquirente, webhook ou qualquer fluxo real de
  pagamento.
- Criar ou persistir campanha, apoiador ou contribuição.

## Decisions

### Páginas separadas em módulos Reflex

O estado da interface de campanhas ficará em `solucao_thn/state.py`, com
componentes comuns em `solucao_thn/components/` e páginas em
`solucao_thn/pages/`. A aplicação atual registrará as rotas mantendo o
catálogo existente.

Alternativa descartada: substituir a página atual ou adicionar toda a UI ao
módulo monolítico, pois isso misturaria campanhas financeiras com o catálogo
de itens e dificultaria a evolução modular solicitada.

### Fixtures explícitas e não persistentes

O feed usará uma coleção local pequena de exemplos com marcador demonstrativo.
As ações GET/POST futuras serão indicadas nos pontos de integração, mas a UI não
fará chamadas a endpoints de campanhas ainda inexistentes.

Alternativa descartada: retornar listas vazias ou fingir uma resposta de API,
pois isso prejudicaria a avaliação visual e poderia ser confundido com estado
persistido.

### Checkout somente de apresentação

Valor, anonimato, mensagem e método serão mantidos como estado de interface.
O PIX não exibirá QR Code real; cartão não coletará dados de cartão; confirmar
não produzirá sucesso financeiro nem chamará um serviço externo.

Alternativa descartada: simular pagamento aprovado, pois criaria uma falsa
representação de uma operação financeira.

### Separação do CTA de doação existente

O botão “Criar Doação” levará ao formulário atual de itens no catálogo. Nesta
Change não haverá criação de campanha de arrecadação.

Alternativa descartada: reutilizar o botão para uma rota de campanha inexistente
ou mudar o significado do cadastro atual sem contrato de produto.

## Risks / Trade-offs

- **[Fixtures confundidas com campanhas reais]** → Exibir aviso “dados
  demonstrativos” nas páginas e nos cartões.
- **[Checkout interpretado como pagamento]** → Não gerar QR, cobrar cartão ou
  mostrar confirmação de transação.
- **[Rotas alterarem a navegação atual]** → Manter a rota do catálogo e
  acrescentar rotas nomeadas para feed, campanha e checkout.
- **[Incompatibilidade de componentes com Reflex instalado]** → Validar com
  `reflex compile --dry` usando a versão já instalada, sem adicionar
  dependências.

## Migration Plan

1. Criar módulos Reflex para estado, cabeçalho e páginas demonstrativas.
2. Registrar rotas sem remover a página atual do catálogo.
3. Executar compilação Reflex e corrigir incompatibilidades.
4. Não há migração, publicação Xano ou rollback de dados. Se necessário,
   remover as novas rotas e módulos sem alterar o catálogo ou seu backend.

## Open Questions

Nenhuma decisão necessária para o escopo demonstrativo permanece em aberto.
