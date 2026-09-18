## Context

A base de identidade e autorização deve ser implementada antes dos fluxos principais do produto. O backend em Xano será responsável por persistir usuários, validar credenciais, manter a sessão ou token e aplicar regras de posse e autorização em cada operação sensível. O frontend em Reflex consumirá esses serviços e apresentará a experiência de cadastro, login e perfil, sem assumir decisões de segurança.

## Goals / Non-Goals

**Goals:**
- Permitir cadastro e autenticação básica de usuários.
- Garantir acesso e edição limitados ao próprio perfil.
- Centralizar permissões no backend.
- Preparar a base para o ciclo completo de doações e relacionamento entre usuários.

**Non-Goals:**
- Não incluir regras de recuperação de senha em escopo inicial.
- Não incluir autorização complexa por papéis ou permissões granulares além do proprietário do recurso.
- Não tratar avaliações, mensagens ou doações nesta mudança.

## Decisions

### 0. Xano como único backend de identidade
O workspace Xano contém a tabela `user` e os endpoints `auth/signup`, `auth/login`,
`auth/profile` (GET/PATCH). O Reflex usa somente um cliente HTTP para chamar essas
APIs e não mantém repositório, hash de senha, validação de credenciais ou checagem
de posse local. Os endpoints de perfil usam o usuário do token (`$auth.id`) como
fonte do registro, portanto não aceitam um identificador de usuário fornecido pelo
cliente para decidir autorização.

### 0. Persistência de conveniência do token no navegador
O token retornado pelo Xano é mantido em `AuthState.auth_token` usando `rx.Cookie`,
com nome próprio, caminho global, validade de 24 horas, `Secure` e `SameSite=Lax`.
Esse é o único dado persistido no navegador. No carregamento da página, o Reflex
usa o token para chamar `GET /auth/profile`; o Xano continua validando o token em
cada leitura e edição. Tokens expirados ou inválidos são descartados do cookie e
o estado volta à tela de login. Senhas, perfil e identificadores não são
persistidos no navegador.

### 1. Backend como fonte de verdade para autenticação e autorização
A autenticação e a autorização serão validadas no Xano, inclusive para ações sobre o próprio perfil. Essa decisão é necessária para respeitar o princípio de segurança estabelecido no projeto e evitar que a interface seja usada como mecanismo de segurança.

Alternativas consideradas:
- Validar permissões apenas no frontend: descartado porque não garante segurança real.
- Centralizar permissões em uma camada de frontend e backend: descartado porque duplicaria regras e aumentar o risco de inconsistência.

### 2. Usuário com dados mínimos e localização obrigatória
O cadastro inicial usará os atributos essenciais de identidade e localização para permitir que a plataforma conheça a pessoa e a aproxime de oportunidades relevantes. A localização será tratada como dado de acesso do usuário, não como uma informação pública irrestrita.

Alternativas consideradas:
- Cadastro sem localização: descartado porque a localização é fundamental para o domínio e cenários de recomendação geográfica.
- Localização opcional em primeiro momento: descartado porque o produto depende dessa informação para o uso futuro do catálogo e da busca.

### 3. Perfil e autorização orientados ao proprietário do recurso
O acesso ao perfil será baseado na propriedade do usuário autenticado. Qualquer operação sobre o recurso de perfil ou dados pessoais deve comparar o identificador da sessão com o identificador do dono do registro.

Alternativas consideradas:
- Permitir acesso genérico por “administrador”: descartado porque não faz parte do escopo inicial e cria autoridade adicional desnecessária.
- Permitir edição por qualquer usuário autenticado: descartado porque viola o requisito de posse e segurança.

### 4. Auth básica no início, sem camada de terceiros
A primeira iteração usará autenticação básica via e-mail e senha, com validação no backend. Essa escolha reduz a complexidade inicial e mantém o escopo alinhado ao produto. Não há necessidade de OAuth ou SSO nesta mudança.

Alternativas consideradas:
- OAuth/social login: descartado como excesso inicial para uma mudança de fundação.
- Tokens JWT sem mecanismo de sessão: descartado como um passo demasiado técnico para o primeiro ciclo do produto.

## Risks / Trade-offs

- [Segurança] → Mitigação: todas as verificações de posse e autorização devem ocorrer no backend e não depender do estado do cliente.
- [Complexidade de sessão] → Mitigação: manter o fluxo simples com autenticação por credenciais e sessão ou token mínimo, sem aumentar a superfície de risco.
- [Dados pessoais sensíveis] → Mitigação: expor somente dados do usuário autenticado e impedir vazamento de informações de terceiros.
- [Validação do e-mail] → Mitigação: aplicar regras de unicidade e sanitização antes da persistência para evitar duplicidade e inconsistência.

## Migration Plan

Não se aplica migração de dados complexa nesta mudança, mas é importante criar a estrutura inicial de autenticação e usuários de forma compatível com as futuras funcionalidades. A implementação deve seguir uma ordem de implantação:

1. Criar tabela/entidade de usuário com localização e metadados mínimos.
2. Implementar endpoints de cadastro e login no backend.
3. Implementar validação de autorização para leitura/edição do perfil próprio.
4. Expôr APIs consumíveis pelo frontend em Reflex.
5. Validar fluxos com usuário autenticado e usuário sem permissão.

Em caso de falha, a reversão deve consistir em manter a base sem expor qualquer endpoint novo em produção até que os testes de autorização e login confirmem a estabilidade.

## Open Questions

- A plataforma usará sessão server-side simples ou token de acesso no padrão do Xano? Isso deve ser decidido no momento da implementação, mas não altera o escopo funcional da mudança.
- A localização será tratada como campo obrigatório em todas as contas ou haverá fluxo de complementação posterior? O escopo atual assume obrigatoriedade para garantir consistência do domínio.
