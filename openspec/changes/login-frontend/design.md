# Design

## Context

Ver `proposal.md` e `specs/user-account/spec.md` para objetivo e comportamento contratado. A página Reflex está concentrada em `doafacil/doafacil.py`, com a home registrada em `/`, fonte LINE Seed JP carregada pela stylesheet do app, cores compartilhadas e integração Catalog baseada em `XANO_API_URL`. O endpoint existente `POST auth/login`, do grupo Authentication, recebe `email` e `password` e retorna `authToken` e `user_id`; credenciais inválidas são rejeitadas pelo Xano. A tela e as decisões visuais estão em `docs/design/README.md` e `docs/design/04-login.png`.

## Goals / Non-Goals

**Goals:**

- Manter a nova rota, o formulário e a autenticação no padrão Reflex já adotado.
- Reutilizar o logotipo, a fonte e a paleta da home, implementando as proporções e o arranjo responsivo da referência.
- Separar a interpretação da resposta HTTP do estado visual para permitir testes `unittest` sem navegador.
- Não expor detalhes do Xano em mensagens de credenciais inválidas.

**Non-Goals:**

- Alterar Xano, seus endpoints, schema ou autenticação.
- Criar cadastro, recuperação de senha, persistência de sessão ou páginas protegidas.
- Adicionar variáveis de ambiente a arquivos, exemplos versionados ou configuração de build.

## Decisions

1. **Adicionar o caminho `/auth/login` à URL base configurada pelo processo.** Uma função dedicada lerá `XANO_AUTH_API_URL`, validará esquema HTTP(S) e host como já ocorre para `XANO_API_URL`, removerá a barra final e acrescentará `/auth/login`. Não reutilizar `XANO_API_URL`, pois ela aponta para o grupo Catalog. A URL não é segredo, mas a configuração fica no ambiente de execução para permitir instâncias diferentes sem alterar código.

2. **Separar cliente HTTP de estado e componentes.** Uma função assíncrona usará o `httpx` já presente no projeto para enviar JSON com somente `email` e `password`, validar a resposta `authToken` e `user_id`, e retornar resultado tipado ou erro reconhecido. Isso permite testar payload, URL, resposta e falhas por `httpx.MockTransport`/mock sem navegador e sem chamada real ao Xano. Não registrar e-mail, senha, token ou corpo de resposta em logs.

3. **Mapear falhas sem revelar existência da conta.** Rejeições de autenticação retornadas pelo endpoint serão exibidas como “E-mail ou senha incorretos”, sem apresentar o corpo de erro do Xano. Falhas de transporte e URL ausente/inválida terão mensagem própria de conexão/configuração. Respostas malformadas ou falhas HTTP não classificadas como rejeição de credenciais usarão mensagem genérica de indisponibilidade, sem detalhes internos.

4. **Usar estado Reflex transitório para carregamento, erro e token.** O estado do login controlará o envio, impedirá eventos concorrentes, atualizará a mensagem conforme o resultado e, no sucesso, guardará `authToken` no próprio estado antes de redirecionar para `/`. Não usar localStorage, cookies, arquivo, banco ou log nesta change. A sessão não será preservada após recarregar a aplicação; isso é consistente com o escopo de não adicionar persistência.

5. **Adicionar a tela como página Reflex e reaproveitar a estrutura visual.** Registrar `login` em `/login`, mantendo `index` em `/`. O botão “Entrar” existente na home será vinculado a `/login`; o cabeçalho da nova tela usa o mesmo `/logo.svg`, centralizado em fundo branco. A área de conteúdo usa fundo creme e cartão branco centralizado, LINE Seed JP e cores já presentes na home, com largura máxima e campos em coluna para caber em telas estreitas. Os controles “Esqueci minha senha” e “Criar conta” permanecem sem link/evento.

6. **Tratar a configuração como responsabilidade do ambiente de execução.** O processo Reflex deve receber `XANO_AUTH_API_URL` definido fora do repositório. Não alterar `.env`, `rxconfig.py`, manifests, arquivos de deploy nem exemplos versionados para incluir um valor local.

## Risks / Trade-offs

- [A URL base do grupo Authentication não estar configurada no ambiente] → validar a configuração antes da chamada e apresentar orientação de conexão sem incluir valores ou credenciais na interface.
- [O endpoint mudar o formato de sucesso ou os status de erro] → validar os campos necessários e cobrir contrato e mapeamento por testes; mudanças do contrato do Xano ficam fora desta change.
- [A sessão transitória ser perdida ao recarregar a página] → documentar e manter a limitação intencional; persistência e proteção de páginas dependem de uma change futura.
- [Mensagem ou estado Reflex expor informação sensível] → nunca renderizar nem registrar o token e não incluir credenciais ou corpo bruto de erro em mensagens/logs.
- [A composição do cartão variar entre larguras] → usar limites responsivos na largura do cartão, preservar campos em coluna e validar a compilação e os testes estruturais do componente.
