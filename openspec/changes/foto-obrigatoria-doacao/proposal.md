# Proposta

## Por quê

O wizard já exige pelo menos uma foto, mas `POST /catalog/donations/publish` aceita chamadas sem fotos e pode criar uma doação sem imagem. A validação precisa existir também no backend para garantir a regra mesmo quando o endpoint é chamado fora do site e evitar registros incompletos.

## O que muda

- **BREAKING:** `POST /catalog/donations/publish` rejeita `photos` ausente, nulo ou vazio com `inputerror` (HTTP 400) e a mensagem “Adicione pelo menos uma foto para continuar.”; a validação ocorre antes de qualquer upload ou `db.add`.
- Manter o limite de cinco fotos e o bloqueio atual da etapa 3 no site.
- Quando a resposta do Xano indicar falta de foto, o site mostra a mesma mensagem e mantém os dados do formulário.
- Tornar `donation_photo.photo` obrigatório somente se a auditoria manual confirmar que não existem linhas com valor vazio; caso contrário, manter a tabela inalterada nesta change.
- Não alterar doações antigas com `donation.photo` vazio.
- Atualizar os testes com respostas simuladas, a especificação e o guia do colaborador.
- Coordenar a mudança do contrato do endpoint compartilhado: avisar o grupo e obter seu OK antes do push real.

## Capacidades

### Novas capacidades

Nenhuma.

### Capacidades modificadas

- `donation-creation`: “Seleção de fotos da doação” e “Publicação autenticada e persistente” passam a exigir no backend pelo menos uma foto e a especificar a resposta e o comportamento da interface quando a publicação não contém fotos.

## Impacto

- Frontend Reflex: `doafacil/cadastro_doacao.py`, para tratar a rejeição específica do Xano sem perder os dados do formulário.
- Testes: `tests/test_donation_creation.py`, incluindo a substituição do teste que atualmente aceita publicação sem fotos.
- Xano: `xano/api/catalog/catalog/donations/publish_POST.xs` e, condicionada ao resultado da auditoria, `xano/table/donation_photo.xs`.
- Dados: auditoria manual de `donation_photo.photo` e `donation.photo`; registros antigos não serão alterados.
- Documentação: `docs/guia-do-colaborador.md`.
- Publicação: o endpoint foi criado por outro integrante e pode ter consumidores além do site; a mudança requer revisão e autorização do grupo antes do push real.
