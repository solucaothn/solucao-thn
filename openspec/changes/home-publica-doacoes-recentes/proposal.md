# Proposal

## Why

A home pública do DoaFácil ainda não existe no frontend, e os contratos locais do Xano não fornecem os dados necessários para os cartões de doações recentes nem para a contagem de doações em circulação. Esta change entrega a primeira fatia pública do produto, conectando a home Reflex a endpoints públicos e preservando compatibilidade com doações existentes sem foto ou condição.

## What Changes

- Adicionar à doação os campos opcionais de foto e condição, com os valores Ótimo, Bom e Regular.
- Disponibilizar um endpoint público para listar as quatro doações disponíveis mais recentes, com os dados necessários aos cartões da home, e um endpoint público para contar todas as doações disponíveis.
- Implementar a home no Reflex com cabeçalho, frase de destaque, contagem, cartões recentes com etiqueta NOVO para doações criadas nos últimos sete dias e ilustração no rodapé.
- Exibir imagem genérica quando a doação não tiver foto e “Condição não informada” quando não houver condição.
- Manter o botão “Acessar” visível, sem navegação nesta change.
- Excluir do MVP “Pessoas alcançadas”; a busca, Explorar Doações, detalhe, formulário, “Comece por aqui”, login/cadastro no frontend e administração permanecem fora do escopo.

## Capabilities

### New Capabilities

- `public-donation-discovery`: consulta pública de doações disponíveis recentes e sua contagem, incluindo os dados opcionais usados pela home.
- `public-home`: apresentação da home pública com a contagem e os cartões de doações recentes.

### Modified Capabilities

Nenhuma. O projeto ainda não possui specs consolidadas.

## Impact

- Xano: tabela `donation` e endpoints do catálogo para foto, condição, listagem pública limitada às quatro doações disponíveis mais recentes e contagem de doações disponíveis.
- Reflex: página inicial e recursos visuais locais para logotipo, imagem genérica e ilustração do rodapé, conforme referências de `docs/design/`.
- Compatibilidade: foto e condição permanecem opcionais; doações existentes sem esses dados continuam listáveis.
