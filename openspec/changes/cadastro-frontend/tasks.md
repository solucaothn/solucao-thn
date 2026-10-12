# Tasks

## 1. Cliente de cadastro e validação

- [x] 1.1 Reutilizar a validação de `XANO_AUTH_API_URL` e implementar `POST /auth/signup` com somente `name`, `email`, `password`, `city` e `state`; validar `authToken` e `user_id`, classificar a mensagem documentada de e-mail duplicado e sanitizar demais falhas. Cobrir URL, payload, sucesso, duplicidade, rejeição genérica e rede com `httpx.MockTransport` em `unittest`.
- [x] 1.2 Implementar validações puras para campos obrigatórios, e-mail, senha mínima de oito caracteres com letra e dígito e confirmação igual; acrescentar testes `unittest` para valores válidos e inválidos de cada regra.

## 2. Estado Reflex e formulário

- [x] 2.1 Acrescentar o fluxo de signup ao mesmo estado Reflex que guarda o token do login, com carregamento, bloqueio de envio duplo, mensagens localizadas, tratamento de duplicidade e redirecionamento no sucesso; testar transições de estado, token compartilhado e ausência de senha nos campos persistentes do estado/logs.
- [x] 2.2 Criar a rota `/cadastro` com campos na ordem especificada, seletor com as 27 UFs, cartão e cabeçalho responsivos, validação e dois controles independentes de mostrar/ocultar senha; acrescentar testes estruturais de textos, ordem dos campos, opções de UF, tipos de botão, ícones e rótulos acessíveis.

## 3. Navegação e documentação de design

- [x] 3.1 Ligar “Criar conta” no login a `/cadastro` e adicionar “← Voltar” com os destinos `/` no login e `/login` no cadastro; testar as rotas e garantir que os demais controles mantêm seus comportamentos.
- [x] 3.2 Atualizar somente as seções 04 e 05 de `docs/design/README.md` com os destinos, campos reais, ausência de Telefone, fundo creme/logo e acréscimos que não constam no Figma; revisar o diff para confirmar que nenhum outro trecho do README mudou.

## 4. Verificação integrada

- [ ] 4.1 Executar `python -m unittest discover -s tests -v` e `.venv\Scripts\reflex.exe compile --dry`; conferir no navegador a responsividade e o fluxo de cadastro, erros de validação, duplicidade, rede e sucesso, sem persistência de sessão após recarregar.
