# Design

## Context

O estado `LoginState` mantém `auth_token` transitório e é reutilizado pelo login e cadastro. A home registra `HomeState.load_home_data` no carregamento e usa `HomeState` para contagem e doações públicas. O endpoint existente `GET auth/me` exige autenticação e retorna um objeto de usuário com `name`, além de outros dados que não devem ser mantidos no estado de exibição. Ver `proposal.md` para a motivação e `specs/user-account/spec.md` para o contrato.

O teste manual observou que o estado do Reflex continua disponível ao recarregar a mesma aba, mas não em uma aba nova nem após reiniciar o servidor. Isso não é persistência própria do site em armazenamento do navegador; a change não deve tentar limpar o estado por causa de um recarregamento.

## Goals / Non-Goals

**Goals:**

- Reaproveitar a sessão existente e carregar apenas o primeiro nome necessário ao cabeçalho.
- Isolar a consulta de conta do carregamento do conteúdo público da home.
- Manter os controles responsivos e o estilo atual do cabeçalho.

**Non-Goals:**

- Criar outro estado de autenticação, adicionar persistência própria em armazenamento do navegador ou alterar o backend.
- Reter e-mail, papel, identificador ou a resposta completa de `auth/me` no estado da interface.

## Decisions

- **Manter o comportamento de conta em `LoginState`.** O login e o cadastro já escrevem `auth_token` nesse estado compartilhado. A home pode referenciar suas Vars diretamente no cabeçalho, e um handler de carregamento definido nesse mesmo estado pode consultar a conta sem copiar o token para `HomeState`. Uma sessão/estado novo duplicaria credenciais e exigiria sincronização adicional.
- **Executar a consulta da conta como handler de carregamento independente.** Registrar `LoginState.load_account` junto de `HomeState.load_home_data` no `on_load` da home. O Reflex aceita uma lista de handlers; assim uma falha de `auth/me` não interrompe nem condiciona os pedidos independentes de contagem e doações recentes. Sem token, o handler mantém o estado de visitante e não chama o endpoint.
- **Usar `GET auth/me` com Bearer e reter somente o primeiro nome.** O cliente chama o endpoint do grupo Authentication por `XANO_AUTH_API_URL`, enviando `Authorization: Bearer <token>`. Extrai o primeiro segmento não vazio de `name`; resposta sem nome útil usa “Minha conta”. Não registrar token, resposta nem dados pessoais.
- **Distinguir token rejeitado de falha transitória.** Respostas HTTP 401/403 limpam token e nome, fazendo o cabeçalho voltar a “Entrar”. Falha de rede, configuração, outra resposta de erro ou resposta inválida mantém a home e usa “Minha conta”, sem limpar automaticamente um token que não foi rejeitado.
- **Limpar a sessão no próprio estado ao sair.** O handler de logout apaga `auth_token` e o nome de exibição; não navega porque o controle está na home.
- **Documentar a extensão visual sem alterar o Figma.** Acrescentar ao `docs/design/README.md` uma nota de que o nome e “Sair” no cabeçalho autenticado são um acréscimo ausente do Figma.

## Risks / Trade-offs

- [A resposta de `auth/me` contém mais dados pessoais do que o cabeçalho precisa] → Validar e extrair somente o primeiro nome, sem armazenar a resposta completa nem registrar conteúdo da requisição.
- [Uma falha transitória pode deixar uma sessão sem nome reconhecível] → Exibir “Minha conta” e preservar o acesso à home pública; somente rejeição explícita limpa o token.
- [Handlers simultâneos podem terminar em tempos diferentes] → Manter estados e tratamento de falha independentes; os pedidos públicos não aguardam o resultado do perfil.
- [O estado da sessão pode continuar disponível após recarga na mesma aba] → Preservar o comportamento observado, sem adicionar armazenamento próprio do site no navegador; uma aba nova ou reinício do servidor começa sem sessão.

## Migration Plan

Não há migração de dados nem alteração de configuração de ambiente: `XANO_AUTH_API_URL` já é usada pelo login e cadastro. Para reverter, retirar a consulta de conta e o cabeçalho condicional, preservando os handlers e a apresentação pública atuais.
