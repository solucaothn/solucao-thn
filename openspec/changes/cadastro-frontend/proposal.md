# Proposal

## Why

A autenticação existente permite entrar, mas ainda não oferece uma experiência de cadastro coerente com os dados exigidos pelo Xano nem uma navegação clara entre as telas de entrada. Esta change acrescenta o cadastro responsivo em Reflex e conecta os controles de retorno e criação de conta às rotas existentes.

## What Changes

- Criar a rota pública `/cadastro` em Reflex com o mesmo cabeçalho, logotipo, fundo creme e cartão branco da tela de login.
- Apresentar os campos Nome, E-mail, Cidade, Estado, Senha e Confirmar senha, nessa ordem; Estado oferece as 27 siglas de UF.
- Validar campos obrigatórios, formato do e-mail, requisitos mínimos da senha e igualdade da confirmação antes de enviar; a validação do frontend não substitui a autoridade do Xano.
- Enviar ao endpoint já existente `POST auth/signup` somente `name`, `email`, `password`, `city` e `state`, usando `XANO_AUTH_API_URL`; não enviar confirmação de senha.
- Apresentar mensagens em português para validação, e-mail já cadastrado quando distinguível na resposta do endpoint, demais falhas genéricas e erro de rede; indicar carregamento e impedir envio duplo.
- No sucesso, guardar o token no mesmo estado Reflex transitório usado pelo login e redirecionar para `/`.
- Acrescentar botão de olho para mostrar/ocultar cada campo de senha, sem copiar valores de senha ao estado Reflex.
- Conectar “Criar conta” do login a `/cadastro` e adicionar “← Voltar” em ambas as telas: login retorna a `/` e cadastro retorna a `/login`.
- Atualizar somente as seções 04 e 05 do `docs/design/README.md`, consolidando as decisões visuais e de campos aprovadas.
- Excluir Telefone do formulário e da requisição: não existe campo correspondente no Xano nem necessidade funcional no escopo.

## Capabilities

### New Capabilities

Nenhuma.

### Modified Capabilities

- `user-account`: acrescentar requisitos observáveis para a interface de cadastro e a navegação entre as telas de login e cadastro, sem duplicar os requisitos de backend já existentes.

## Impact

- Frontend Reflex: nova rota `/cadastro`, estado e validação da interface, e ajustes de navegação em `doafacil/`.
- Integração: consumo do endpoint Xano existente `auth/signup` com `XANO_AUTH_API_URL`; nenhum endpoint, tabela ou dado do Xano será alterado.
- Testes: novos testes `unittest` para validação, envio, tratamento de respostas e estrutura/navegação dos componentes.
- Documentação: revisão limitada às seções 04 e 05 de `docs/design/README.md` e delta OpenSpec em `user-account`.
- Dependências: nenhuma nova dependência prevista.
