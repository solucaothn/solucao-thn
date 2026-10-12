# Proposal

## Why

A home pública já oferece o botão “Entrar”, mas ainda não existe uma tela para autenticar uma pessoa usuária. Esta change acrescenta uma entrada visualmente coerente com o design e conecta o formulário ao endpoint de login já existente no Xano.

## What Changes

- Adicionar a rota Reflex `/login`, com cabeçalho branco e logotipo centralizado, fundo creme, cartão branco, campos de e-mail e senha, botão “Entrar”, link “Esqueci minha senha” e botão “Criar conta”, conforme `docs/design/README.md` e `docs/design/04-login.png`.
- Autenticar somente por e-mail e senha usando `auth/login` do grupo Authentication; não oferecer login por CPF.
- Obter a URL base do grupo Authentication da variável de ambiente `XANO_AUTH_API_URL`, lida pelo processo do Reflex e não armazenada em arquivos versionados.
- Durante o envio, indicar carregamento e apresentar mensagem genérica para credenciais inválidas; erros de rede recebem mensagem própria.
- Em caso de sucesso, manter o token somente no estado Reflex, sem persistência adicional, e redirecionar para `/`.
- Fazer o botão “Entrar” do cabeçalho da home navegar para `/login`.
- Manter “Esqueci minha senha” e “Criar conta” sem destino nesta change.
- Adicionar testes `unittest` para configuração da URL e lógica de requisição, interpretação de resposta e erros, sem depender de navegador.

## Capabilities

### New Capabilities

Nenhuma.

### Modified Capabilities

- `user-account`: acrescentar o comportamento observável da tela Reflex de login e de sua integração com o contrato de autenticação existente.

## Impact

- Reflex: rota `/login`, formulário e estado de autenticação, com navegação do cabeçalho da home.
- Integração: chamada HTTP ao endpoint `auth/login` do grupo Authentication, usando `XANO_AUTH_API_URL` configurada no ambiente do processo.
- Testes: novos casos `unittest` para a lógica de login; nenhuma alteração no Xano, na tabela `user` ou no endpoint existente.
- Visual: reutilização do logotipo, da fonte LINE Seed JP e das cores já usadas na home, com layout responsivo.
