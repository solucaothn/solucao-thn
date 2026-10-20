# Design

## Context

Consulte [proposal.md](./proposal.md) para a motivação e as [deltas de spec](./specs/password-recovery/spec.md) e [user-account](./specs/user-account/spec.md) para os contratos. O `LoginState` em `doafacil/login.py` já concentra a integração HTTP simulável, configuração de `XANO_AUTH_API_URL`, eventos assíncronos, carregamento, mensagens genéricas e dados de formulário transitórios. As três APIs Xano já existem; `confirm_password` retorna somente sucesso/falha, então a tela deve validar senha antes do envio.

O ambiente não contém `docs/guia-do-colaborador.md`; a proposta usa as instruções de `AGENTS.md`, o README de design, as specs, código, testes e endpoints disponíveis.

## Goals / Non-Goals

**Goals:**
- Ligar as três telas às APIs já publicadas, preservando o contrato neutro do backend.
- Reutilizar padrões existentes de Reflex, cliente HTTP, validação, carregamento e animação.
- Manter os dados sensíveis temporários e inacessíveis por URL ou armazenamento no navegador.
- Atualizar documentação e cobertura estrutural/unitária das rotas e interações.

**Non-Goals:**
- Alterar ou publicar arquivos no Xano.
- Alterar endpoints legados de recuperação, envio de e-mail, sessão/autenticação persistente ou fluxo de doação.
- Incluir JavaScript ou dependências de frontend adicionais.

## Decisions

### Estado e organização do fluxo

- Reutilizar `LoginState` em `doafacil/login.py` para os eventos de recuperação e o aviso transitório do login; manter os componentes das três telas em módulo Reflex próprio e registrar as rotas em `doafacil/doafacil.py`. Essa opção permite que o fluxo e o login compartilhem a confirmação sem coordenar estados irmãos.
- O estado guarda apenas o e-mail enquanto a pessoa percorre o fluxo e o `reset_token` depois da verificação; flags operacionais como carregamento, erro genérico, visibilidade das senhas e segundos restantes são estado de interface, não dados pessoais ou credenciais. Código, senha e confirmação entram somente como dados transitórios do formulário/evento, não em atributos de estado, logs, URLs, mensagens ou armazenamento do navegador.
- Ao voltar da etapa de verificação para a solicitação, preservar o e-mail para edição; o link “Usar outro e-mail” apaga o e-mail explicitamente. Saídas para login, conclusão ou abandono apagam e-mail/token.

Alternativa considerada: manter um `PasswordRecoveryState` independente. Foi evitada para não precisar expor ou sincronizar um aviso entre estados diferentes; os dados e eventos de recuperação permanecem identificados por prefixo e compartilham as validações e o cliente do `LoginState`.

### Cliente HTTP e contratos

- Construir os endpoints relativos reutilizando a validação central de `XANO_AUTH_API_URL`, sem gravar endereço ou valor de ambiente em arquivo. Usar um `httpx.AsyncClient` com timeout e injeção do cliente nas funções auxiliares para testes com `MockTransport`.
- Enviar somente `email` a `reset/request_code`, `email` e `code` a `reset/verify_code`, e `reset_token`, `password` e `password_confirmation` a `reset/confirm_password`.
- Tratar sucesso de solicitação como avanço para a verificação, sem inferir existência da conta. Tratar `success: false` da verificação como a mesma mensagem de código inválido/vencido. Tratar falhas de rede/configuração com mensagem de conexão genérica e distinta, sem expor detalhes HTTP nem corpo do serviço.
- Validar localmente senha com mínimo de oito caracteres, ao menos uma letra e um dígito, mais confirmação idêntica, antes de enviar; são as mesmas regras do cadastro.
- Mascarar o e-mail com a primeira letra do nome local, `***` e domínio. A máscara é apenas apresentação e não muda o dado enviado ao Xano.

Alternativa considerada: interpretar detalhes de erro HTTP para separar código inválido, conta inexistente ou senha fraca. Rejeitada porque a API normaliza intencionalmente os resultados e a tela não deve reintroduzir enumeração.

### Timer, rotas e aviso de sucesso

- Implementar a contagem regressiva de 30 segundos com mecanismo de evento/timer nativo suportado pela versão instalada do Reflex; nenhuma lógica de segurança depende do timer. Após reenvio aceito, reiniciar a contagem; o endpoint Xano permanece autoridade para limites.
- As rotas de verificação e de nova senha verificam a presença do e-mail/token no estado Reflex e redirecionam para `/recuperar-senha` quando acessadas diretamente sem pré-requisito. Navegação e formulários usam apenas componentes, estado e eventos Reflex.
- Após sucesso da troca, limpar os dados do fluxo, armar um indicador de mensagem pendente e redirecionar para `/login`. No carregamento do login, consumir o indicador uma única vez em uma variável de exibição. Se a rota for aberta por recarga ou histórico sem indicador pendente, ocultar o aviso; limpar também ao digitar, submeter login ou navegar para fora. A faixa usa `role="status"` para anúncio acessível.
- Preservar o cartão e identidade das telas existentes: logo em cabeçalho branco, fundo creme, cartão branco, classe `auth-card-enter` no cartão, media query existente para movimento reduzido e regras de autofill com texto escuro/fundo branco nos novos campos.

Alternativa considerada: transportar o aviso por query string ou armazenamento de navegador. Rejeitada por deixar estado de sucesso no URL/cliente e poder reaparecer depois.

### Testabilidade e documentação

- Cobrir funções HTTP e validação com clientes simulados; cobrir estados e páginas por testes estruturais no padrão de `test_login.py`/`test_signup.py`. Não fazer requisições reais ao Xano nos testes.
- Atualizar apenas a documentação diretamente relacionada ao fluxo, acrescentando as descrições das telas 11, 12 e 13 em `docs/design/README.md`.

## Risks / Trade-offs

- [O timer visual pode divergir do relógio do servidor] → Tratar apenas como indicação; exibir falha genérica quando o reenvio for recusado e manter a limitação no Xano.
- [O token permanece disponível no estado Reflex durante a etapa de nova senha] → Guardar somente o valor mínimo, limpar em conclusão, expiração/falha definitiva ou abandono e nunca expor em URL/logs/client storage.
- [O aviso transitório depende da sequência de navegação do Reflex] → Testar estruturalmente o consumo de uma única vez e confirmar recarga/histórico na conferência manual do navegador.
- [Autofill pode aplicar cores do navegador nos campos novos] → Cobrir seletores `:-webkit-autofill`, hover e focus nos testes CSS.

## Migration Plan

Não há migração de dados nem alteração no Xano. Implementar e testar a interface localmente, executar `python -m unittest discover -s tests -v` e `.venv\Scripts\reflex.exe compile --dry`; depois da implementação, o usuário fará a conferência visual/manual no navegador antes do archive. Nenhum commit ou push faz parte desta change.
