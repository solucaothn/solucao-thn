# Proposal

## Why

Os quatro cartões institucionais da home (“Doar no DoaFácil é simples e seguro.”) ainda mostram um degradê provisório. O grupo produziu vídeos curtos próprios para eles, sem marca d'água e sem som, e eles já estão no projeto.

## What Changes

- **Vídeos nos cartões:** cada cartão passa a mostrar o seu vídeo de `assets/landing/` no lugar do degradê.

  | Arquivo | Cartão |
  |---|---|
  | `solidariedade.mp4` | Solidariedade / Histórias que continuam |
  | `seguranca.mp4` | Segurança / Você no controle |
  | `missao.mp4` | Nossa missão / Nada se perde |
  | `passo-a-passo.mp4` | Passo a passo / Doar leva minutos |

- **Como cada vídeo toca:** com `autoplay`, `muted`, `loop`, `playsinline` e `preload="metadata"`, a capa `.jpg` correspondente como `poster` e `object-fit: cover`.
- **Cartão:** continua igual ao Figma (245 × 245, cantos arredondados, ícone em círculo verde, rótulo e título por cima). O gradiente escuro embaixo fica sobre o vídeo e mantém o texto legível.
- **Movimento reduzido:** com `prefers-reduced-motion`, nenhum vídeo toca e só a capa aparece.
- **Acessibilidade:** o vídeo é decorativo (`aria-hidden`, sem controles e fora da ordem do Tab). O texto acessível do cartão continua sendo o rótulo e o título.
- **Sem rolagem horizontal** em 360 px.
- **Fora do escopo:**
  - o resto da home;
  - as outras páginas;
  - a change `navegacao-celular`, que continua aberta e separada;
  - qualquer mudança no Xano.

## Capabilities

### New Capabilities

Nenhuma.

### Modified Capabilities

- `public-home-content`: o requisito “Conteúdo institucional da home” troca o cenário “Imagem dos cartões”, que pedia o degradê provisório, por vídeos próprios com capa, movimento reduzido e texto legível.

## Impact

- **Código:** `doafacil/doafacil.py` (`INSTITUTIONAL_CARDS` e `institutional_card`) e `assets/chat.css` ou uma folha nova para a regra de movimento reduzido.
- **Arquivos novos versionados:** os 8 de `assets/landing/`, cerca de 950 KB no total.
- **Testes:** `tests/test_public_home.py`, que hoje confere o degradê.
- **Documentação:** `docs/design/README.md`, nas diferenças da home em relação ao Figma.
- **Sem mudanças** no Xano, nas APIs e nas dependências.
