# Proposal

## Why

No cadastro de doação, placeholders e textos de seleção aparecem apagados, dificultando a leitura; algumas categorias e modalidades também precisam ser retiradas das escolhas disponíveis nesta etapa. Os ajustes devem permanecer no frontend Reflex, sem alterar o catálogo nem os contratos do Xano.

## What Changes

- Aumentar o contraste dos placeholders dos campos, dos textos de placeholder e das opções dos selects, incluindo as formas de contato do quinto passo, para uma cor preta ou cinza bem escura.
- Filtrar somente no frontend as categorias “Alimentos” e “Móveis”, sem apagar categorias nem alterar a API ou os dados do Xano.
- Apresentar apenas “A combinar” como modalidade de entrega e validar/publicar esse valor conforme o contrato existente.
- Aplicar a cor escura diretamente ao conteúdo interno de placeholder do Select do Radix, sem alterar o fundo nem o estilo das listas abertas; permitir avançar no passo de fotos sem selecionar arquivos; manter apenas “E-mail” e “Chat do DoaFácil” como preferências de contato.
- Alterar o exemplo do campo “Nome do item” para “Ex.: Carrinho de brinquedo” e exigir pelo menos uma foto antes de avançar do passo 3, mantendo o limite de cinco.
- Acrescentar testes unittest para o filtro, as opções de entrega, o contraste nas telas/controles e o payload de publicação.

## Capabilities

### New Capabilities

### Modified Capabilities

- `donation-creation`: atualizar os requisitos de apresentação e seleção de categorias e forma de entrega no wizard.

## Impact

- Frontend Reflex: `doafacil/cadastro_doacao.py` e estilos compartilhados de componentes.
- Testes: `tests/test_donation_creation.py`.
- Documentação de design: `docs/design/README.md`.
- Spec existente: `openspec/specs/donation-creation/spec.md`.
- Xano: nenhuma mudança. O endpoint `catalog/donations/publish` aceita “A combinar”, “E-mail” e “Chat do DoaFácil” e declara `photos` opcional, incluindo o fluxo sem arquivos.
- Sem novas dependências, rotas ou mudanças no processo de publicação.
