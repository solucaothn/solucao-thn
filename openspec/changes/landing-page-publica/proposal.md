## Why

A rota raiz do DoaFácil ainda apresenta diretamente login, cadastro e catálogo,
sem explicar publicamente o propósito da plataforma ou orientar visitantes às
principais experiências. Uma landing page institucional torna a entrada mais
clara e responsiva, mantendo autenticação e catálogo disponíveis em uma rota
de aplicação separada.

## What Changes

- Substituir o conteúdo da rota `/` por uma landing page pública com navegação,
  hero, busca demonstrativa, confiança, destaques e rodapé institucional.
- Preservar a tela atual de autenticação, perfil e catálogo em `/app`.
- Direcionar os visitantes ao catálogo de itens e à experiência demonstrativa
  de vaquinhas por CTAs distintos.
- Filtrar campanhas locais demonstrativas por palavra-chave, categoria e
  localidade, sem chamadas obrigatórias ao backend.
- Informar que criar campanhas financeiras ainda não está disponível.

Fora do escopo: criar ou persistir campanhas, conectar pesquisa da landing page
a endpoints ainda inexistentes, adicionar localização real às doações, alterar
autenticação, pagamentos ou regras do Xano, e remover arquivos/rotas existentes.

## Capabilities

### New Capabilities

- `landing-page-publica`: experiência institucional pública na raiz, navegação
  aos fluxos existentes e descoberta visual com dados demonstrativos.

### Modified Capabilities

- Nenhuma.

## Impact

- Reflex: nova página pública e componentes de navegação, busca, confiança,
  destaques e rodapé; a página existente de conta/catálogo permanece em `/app`.
- Campanhas: reutilização somente das fixtures locais da experiência de
  vaquinhas, com localidades de exemplo explicitamente não reais.
- Xano e pagamentos: nenhum endpoint, schema, dado ou integração será alterado.
