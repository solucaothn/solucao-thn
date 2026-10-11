# Proposal

## Why

A home pública atual já apresenta a contagem e as doações recentes, mas ainda não oferece as opções de entrada para quem quer doar ou receber, nem explica a missão e as informações institucionais do DoaFácil. Completar essas áreas conforme o design aprovado torna a página mais informativa sem depender de destinos que ainda não existem.

## What Changes

- Acrescentar abaixo das doações recentes a seção “Comece por aqui”, com etiqueta, título, texto de apoio e os cartões “Para você mesmo”, “Ajude quem precisa” e “Desapego em grupo”.
- Identificar “Desapego em grupo” como “Em breve” e não apresentar seta nesse cartão.
- Acrescentar a seção institucional com título e frase de apoio aprovados e quatro cartões: Solidariedade, Segurança, Nossa missão e Passo a passo, cada um com ícone, categoria, título e “Saiba mais”, em degradê verde e cinza, sem fotos ou vídeos.
- Acrescentar um rodapé escuro com o logotipo, os links rápidos aprovados e a identificação “Projeto acadêmico DoaFácil”.
- Manter botões, setas e links sem navegação, pois os destinos não existem nesta change.
- Organizar os cartões em coluna em telas estreitas e preservar a fonte LINE Seed JP, a paleta e os estilos já usados na home.
- Atualizar `docs/design/README.md` para registrar estas decisões, inclusive a remoção dos elementos de rodapé herdados do Vakinha.

## Capabilities

### New Capabilities

- `public-home-content`: apresentação das seções de entrada, conteúdo institucional e rodapé na home pública.

### Modified Capabilities

Nenhuma. O inventário atual não contém specs consolidadas; o comportamento novo será especificado nesta capability.

## Impact

- Frontend Reflex: página inicial em `doafacil/doafacil.py`, mantendo os mecanismos e estilos existentes.
- Documentação de design: `docs/design/README.md`.
- Nenhuma alteração no Xano, em APIs, dados, autenticação ou dependências.
- Fora do escopo: busca, páginas de destino, Explorar Doações, vídeos, login e cadastro, seção institucional com fotos, e qualquer navegação dos controles novos.
