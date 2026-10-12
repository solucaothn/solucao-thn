# Tasks

## 1. Cliente do endpoint de autenticação

- [x] 1.1 Implementar a resolução e validação de `XANO_AUTH_API_URL` e a chamada `POST auth/login`, enviando apenas e-mail e senha e validando `authToken` e `user_id`; verificar que URLs inválidas, respostas malformadas e falhas HTTP geram erros classificados sem incluir credenciais ou corpo bruto.
- [x] 1.2 Acrescentar testes `unittest` isolados para URL válida/ausente/inválida, payload enviado, resposta válida, rejeição de credenciais e falha de rede; verificar com `python -m unittest discover -s tests -v` que a suíte passa sem chamar o Xano real.

## 2. Estado e interface Reflex

- [x] 2.1 Implementar o estado Reflex de login com carregamento, bloqueio de envio concorrente, mensagens genéricas de credencial e conexão, token transitório somente no estado Reflex e redirecionamento para `/`; cobrir os resultados com testes `unittest` sem navegador.
- [x] 2.2 Criar a página responsiva `/login` com logo centralizado no cabeçalho branco, fundo creme, cartão e textos/campos/botões definidos no design; manter “Esqueci minha senha” e “Criar conta” sem ação, e verificar por teste estrutural do componente os textos e controles sem destino.
- [x] 2.3 Fazer o botão “Entrar” da home navegar para `/login`; verificar por teste estrutural que o destino está registrado e não altera os demais controles da home.
- [x] 2.4 Acrescentar um botão discreto no campo Senha para alternar entre senha oculta e visível, com ícone e rótulo acessível correspondentes; verificar o estado alternável e a estrutura do botão por testes `unittest`.

## 3. Verificação integrada

- [x] 3.1 Executar `python -m unittest discover -s tests -v` e `.venv\Scripts\reflex.exe compile --dry`; testar manualmente a rota `/login` em largura estreita e larga, conferindo o design, carregamento, mensagens de erro e retorno à home após sucesso com endpoint disponível no ambiente, sem persistência de token após recarregar.
