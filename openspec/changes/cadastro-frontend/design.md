# Design

## Context

Ver `proposal.md` e `specs/user-account/spec.md` para motivação e comportamento contratado. A rota `/login`, a função de validação da URL do grupo Authentication e o estado `LoginState` estão em `doafacil/login.py`; a app registra as páginas em `doafacil/doafacil.py`. O cliente atual usa `httpx`; `tests/test_login.py` cobre clientes simulados e estrutura de componentes Reflex. O endpoint `POST auth/signup` recebe `name`, `email`, `password`, `city` e `state`, e retorna `{authToken, user_id}`. Para duplicidade, o Xano declara `error_type = "accessdenied"` e a mensagem `An account with this email already exists.`; o arquivo `.xs` não fixa o envelope HTTP dessa falha.

## Goals / Non-Goals

**Goals:**

- Reutilizar a configuração e o estado de sessão usados pelo login.
- Preservar os valores de senha somente no envio do formulário, mantendo no estado apenas indicadores booleanos da visibilidade.
- Distinguir a rejeição específica de e-mail duplicado somente quando a resposta estruturada identificar essa mensagem conhecida.
- Manter os requisitos de signup já consolidados em `user-account` como contrato do backend, especificando nesta change somente o comportamento da interface e a navegação.

**Non-Goals:**

- Alterar arquivos, endpoints, validações ou dados do Xano.
- Persistir token ou senha em armazenamento do cliente, arquivo, banco ou log.
- Incluir telefone, recuperação de senha, telas adicionais ou estado de usuário autenticado no cabeçalho.

## Decisions

1. **Reutilizar `LoginState` e a configuração do grupo Authentication.** Extrair a resolução/validação da base URL existente para que os caminhos `/auth/login` e `/auth/signup` compartilhem a mesma validação de `XANO_AUTH_API_URL`. O cadastro usa o mesmo `LoginState` que contém `auth_token`, evitando uma segunda sessão Reflex. Criar um estado independente exigiria transferir o token entre estados e poderia divergir da sessão atual.

2. **Separar validação de formulário e cliente HTTP.** Funções puras validarão campos obrigatórios, formato de e-mail, senha mínima de oito caracteres com letra e dígito e confirmação. O handler receberá os valores do formulário em `form_data`, sem copiá-los para variáveis de estado. A chamada HTTP envia somente os cinco campos aceitos pelo endpoint; confirmação nunca integra o payload. A validação do cliente serve à experiência e não substitui a validação do Xano.

3. **Classificar e sanitizar respostas do signup.** Validar `authToken` e `user_id` no sucesso. Para falhas, inspecionar apenas campos estruturados da resposta em busca do texto exato de duplicidade definido no Xano. Como o `.xs` não determina o envelope HTTP, qualquer status/rejeição cujo conteúdo não identifique de modo inequívoco essa mensagem recebe erro genérico. Nunca mostrar nem registrar corpo bruto, credenciais ou token.

4. **Manter controles de visibilidade independentes.** Adicionar dois booleanos ao estado Reflex, um para Senha e outro para Confirmar senha. Cada input decide entre `password` e `text` pelo booleano correspondente, e seu botão `type="button"` alterna ícone e `aria-label`. Valores de senha continuam apenas nos campos e no argumento transitório do handler.

5. **Compor a página a partir do padrão do login.** Reaproveitar o cabeçalho branco com `/logo.svg`, paleta, fonte LINE Seed JP, cartão branco e comportamento responsivo. Implementar o seletor de Estado com as 27 UFs oficiais. Colocar “← Voltar” alinhado ao início do cartão nas duas páginas e associar controles às rotas definidas; “Criar conta” deixa de ser inerte.

6. **Atualizar apenas as seções 04 e 05 do README de design.** A seção 04 registra Voltar para `/` e Criar conta para `/cadastro`; a seção 05 substitui o cadastro desatualizado pelas decisões aprovadas de campos, fundo, logo, telefone e controles adicionais. Nenhuma outra parte do README será alterada.

## Risks / Trade-offs

- [A resposta HTTP de `accessdenied` não conter o texto de duplicidade em um campo estruturado reconhecido] → apresentar mensagem genérica, sem fazer inferências pelo status isolado nem expor o corpo bruto.
- [A validação do navegador divergir das regras do Xano] → manter o Xano como autoridade e tratar qualquer rejeição não reconhecida com mensagem genérica.
- [O estado compartilhado conter muitas responsabilidades] → adicionar somente flags e eventos de cadastro necessários a `LoginState`, sem mover o token nem as regras existentes de login.

## Migration Plan

Não há migração de dados nem publicação de mudanças no Xano. A implantação limita-se ao frontend Reflex e ao README de design; rollback consiste em reverter a change do frontend e a atualização documental.
