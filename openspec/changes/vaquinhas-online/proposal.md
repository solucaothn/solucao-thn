## Why

O DoaFácil já oferece um catálogo público de itens para doação, mas ainda não
apresenta uma experiência para campanhas de arrecadação financeira. Uma
interface demonstrativa permite validar feed, detalhe e checkout visualmente,
mantendo as vaquinhas separadas do catálogo e sem simular transações antes da
escolha de um provedor de pagamentos.

## What Changes

- Adicionar páginas Reflex para feed, detalhe de campanha e checkout
  demonstrativos.
- Apresentar campanhas de exemplo identificadas claramente como dados
  demonstrativos.
- Preparar estado e pontos de integração para consultas e operações futuras no
  Xano, sem afirmar que houve doação, cobrança ou confirmação de pagamento.
- Usar os componentes nativos do Reflex e a paleta visual aprovada.
- Manter o botão “Criar Doação” ligado ao formulário já existente para itens.

Fora do escopo: criar modelo/tabelas ou endpoints Xano para campanhas,
integrar provedor de pagamentos, receber doações reais, criar campanhas,
webhooks, QR Codes PIX reais, autenticação nova ou alterar o catálogo de itens.

## Capabilities

### New Capabilities

- `interface-demonstrativa-vaquinhas`: feed, detalhe e checkout visual de
  campanhas de arrecadação sem persistência ou processamento financeiro real.

### Modified Capabilities

- Nenhuma.

## Impact

- Reflex: adicionar módulos de estado, cabeçalho, feed, detalhe e checkout,
  integrados à aplicação existente sem substituir a página do catálogo.
- Xano: nenhum schema ou endpoint será criado ou alterado nesta Change.
- Pagamentos: PIX e cartão serão opções visuais demonstrativas; nenhuma
  solicitação será enviada a um adquirente e nenhum QR Code será gerado.
