## Why

O DoaFácil precisa de uma base sólida de identidade e autorização para que usuários possam criar contas, autenticar-se e acessar somente seus próprios dados e recursos. Sem esse alicerce, não é possível garantir a integridade das doações, a privacidade dos dados e a confiabilidade do fluxo de relacionamento entre doador e interessado.

A mudança é necessária agora porque as próximas funcionalidades dependem diretamente de quem é o usuário autenticado e de quais ações ele pode realizar. Isso inclui cadastro de doações, manifestação de interesse, comunicação entre partes e avaliações, todas sensíveis a regras de posse e autorização.

## What Changes

- Criação de cadastro de usuário com dados mínimos e localização associada.
- Autenticação básica por credenciais do usuário, com validação no backend.
- Perfil do usuário com leitura e edição restrita ao próprio dono.
- Regras de autorização no backend para garantir que cada usuário acesse apenas seus próprios recursos e dados.
- Estabelecimento da base para futuras mudanças de doações, interesses, mensagens e avaliações.

## Capabilities

### New Capabilities
- `identidade-autorizacao`: base de identidade, autenticação básica, perfil do usuário e políticas de autorização no backend.

### Modified Capabilities
- Nenhuma. Esta mudança cria a fundação de identidade e autorização sem alterar uma capability existente.

## Impact

- Backend em Xano: novos endpoints e regras de autenticação/autorização; validação de dados e permissões em todas as operações sensíveis.
- Frontend em Reflex: telas de cadastro, login e edição de perfil, com o backend como fonte de verdade para segurança.
- Dados de usuário e localização: modelagem inicial para persistência, consistência e uso em filtros geográficos.
- Dependências futuras: a base criada aqui habilita a implementação de doações, interesses, mensagens e avaliações sem duplicação de regras de identidade e permissão.
