# Proposal

## Why

As APIs de recuperação por código já estão publicadas no Xano, mas a aplicação Reflex ainda não oferece o fluxo correspondente e o link “Esqueci minha senha” no login não leva a lugar algum. Esta mudança conecta as telas de recuperação ao backend e fecha o retorno ao login após a troca de senha.

## What Changes

- Criar as rotas Reflex para solicitar código, verificar e-mail/código e definir nova senha, consumindo os três endpoints publicados no grupo Authentication.
- Manter e-mail e token de redefinição somente no estado Reflex durante o fluxo; códigos e senhas serão processados como dados de formulário sem persistência em estado nem registro em logs.
- Apresentar mensagens neutras para não revelar se uma conta existe, validar a senha no frontend antes da confirmação e mostrar um aviso de sucesso de uso único no login.
- Atualizar a documentação de design com as telas 11, 12 e 13 e registrar o destino do link de recuperação.
- Alterar o requisito existente `user-account` para que o link do login abra a primeira tela do fluxo.

## Capabilities

### New Capabilities

- `password-recovery`: interface Reflex do fluxo de recuperação por código e retorno ao login com confirmação transitória.

### Modified Capabilities

- `user-account`: atualizar o cenário da interface de login para que “Esqueci minha senha” navegue para `/recuperar-senha`.

## Impact

- Frontend Reflex: `doafacil/login.py`, `doafacil/cadastro.py`, `doafacil/doafacil.py` e testes unittest relacionados.
- Documentação: `docs/design/README.md`.
- APIs Xano existentes `reset/request_code`, `reset/verify_code` e `reset/confirm_password` como consumidoras; nenhuma alteração no Xano.
- Sem novas dependências, persistência de sessão ou alterações no cadastro de doação.
