# Tasks

## 1. Cliente Xano e estado do fluxo

- [x] 1.1 Adicionar helpers testáveis para `reset/request_code`, `reset/verify_code` e `reset/confirm_password`, reutilizando `XANO_AUTH_API_URL` e o padrão `httpx.AsyncClient`; cobrir URLs, payloads, formatos de resposta e erros de rede/configuração com `httpx.MockTransport`, sem chamar o Xano real.
- [x] 1.2 Implementar no `LoginState` os eventos de solicitar, reenviar, verificar e confirmar, validação local de senha, máscara de e-mail, carregamento e bloqueio de envios concorrentes; adicionar testes unittest para sucesso/falha neutra e garantir que código e senhas não virem atributos de estado ou dados de log.
- [x] 1.3 Implementar o estado do timer de reenvio com eventos Reflex nativos compatíveis com a versão instalada; testar início em 30 segundos, contagem até zero e reinício após reenvio, deixando explícito no teste que a proteção real continua no servidor.

## 2. Telas, navegação e acessibilidade

- [x] 2.1 Criar as páginas Reflex `/recuperar-senha`, `/verificar-email` e `/nova-senha`, com estados de navegação e pré-requisitos; registrar as rotas, ligar o link do login e cobrir estrutura, rotas, mensagens neutras, voltar/usar outro e-mail e estado de carregamento em testes unittest.
- [x] 2.2 Implementar o aviso verde transitório no login, anunciado como `role="status"`, consumido uma única vez após a redefinição e limpo ao digitar, entrar, sair, recarregar ou voltar pelo histórico; adicionar testes estruturais e de estado para confirmar que não reaparece.
- [x] 2.3 Aplicar `auth-card-enter` aos cartões, preservar cabeçalho estático e movimento reduzido, e adicionar regras `:-webkit-autofill` para os campos novos; verificar as classes e regras CSS com testes estruturais/unitários.

## 3. Documentação e integração

- [x] 3.1 Acrescentar no `docs/design/README.md` as seções das telas 11, 12 e 13 e identificar os acréscimos que não estão no Figma (olhos, texto neutro, links “← Voltar”, animação e aviso verde); verificar que as descrições correspondem às telas implementadas e às decisões da change.
- [x] 3.2 Rodar `python -m unittest discover -s tests -v` e `.venv\Scripts\reflex.exe compile --dry`; corrigir falhas relacionadas à change e confirmar que os testes preexistentes de login, cadastro e home continuam passando.

## 4. Conferência manual

- [ ] 4.1 Conferir no navegador o fluxo de ponta a ponta: login para solicitação; texto neutro e e-mail mascarado; código correto/incorreto; contagem e reenvio; “Usar outro e-mail”; validação das senhas e confirmação; retorno com aviso verde; limpeza ao digitar, recarregar ou voltar; responsividade, autofill e movimento reduzido.
