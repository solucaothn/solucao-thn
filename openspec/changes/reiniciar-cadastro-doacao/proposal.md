# Proposal

## Why

Após publicar uma doação, o estado de `DonationCreateState` permanece preenchido e com `published=True`. Ao retornar a `/cadastro-doacao`, o formulário reaparece com os dados anteriores e os controles de navegação/publicação ficam bloqueados, impedindo iniciar outra doação na mesma aba, inclusive após trocar de conta.

## What Changes

- Reiniciar os campos, mensagens, flags e etapa do formulário a cada entrada em `/cadastro-doacao`, inclusive em recarregamentos.
- Limpar também os arquivos selecionados no componente de upload.
- Preservar o aviso de sucesso e a proteção contra duplicação durante a visita em que a publicação foi concluída; a limpeza acontece somente na próxima entrada.
- Manter as regras existentes de fotos obrigatórias, categorias exibidas, entrega e preferência de contato.

## Capabilities

### New Capabilities

Nenhuma.

### Modified Capabilities

- `donation-creation`: definir que cada nova entrada no formulário começa um cadastro vazio e habilitado, sem perder o resultado da publicação durante a visita atual.

## Impact

- Frontend Reflex: estado `DonationCreateState`, carregamento inicial da página e controle de arquivos selecionados no upload.
- Testes `unittest` do cadastro de doação.
- Nenhuma alteração no Xano, no estado de login ou na página de detalhe.
