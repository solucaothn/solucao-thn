## ADDED Requirements

### Requirement: Campos do cadastro com a mesma altura
Na página `/cadastro`, o seletor “Estado” MUST ter a mesma altura dos outros campos do formulário, cerca de 48 px, em qualquer largura.

#### Scenario: Ver o formulário de cadastro
- **WHEN** uma pessoa abre `/cadastro` em 1280 ou 360 px
- **THEN** o seletor “Estado” MUST ter a mesma altura dos campos Nome, E-mail, Cidade, Senha e Confirmar senha

## MODIFIED Requirements

### Requirement: Interface pública de login
A aplicação SHALL oferecer uma página pública de login responsiva, coerente com a identidade visual da home e com autenticação somente por e-mail.

#### Scenario: Acessar a página de login
- **WHEN** uma pessoa acessa `/login` ou aciona “Entrar” no cabeçalho da home
- **THEN** a aplicação apresenta cabeçalho branco com logotipo colorido centralizado, fundo creme e cartão branco centralizado
- **AND** o cartão apresenta “Boas-vindas”, “Entre com seu e-mail e senha”, os campos “E-mail” e “Senha”, o link “Esqueci minha senha” alinhado à direita abaixo da senha e o botão verde “Entrar”
- **AND** a página apresenta abaixo do cartão o botão em forma de pílula “Criar conta”
- **AND** não solicita CPF
- **AND** “Esqueci minha senha” leva para `/recuperar-senha`, enquanto “Criar conta” leva para `/cadastro`

#### Scenario: Alternar a visibilidade da senha
- **WHEN** a pessoa aciona o botão de olho no campo “Senha”
- **THEN** a senha alterna entre oculta e visível, iniciando oculta
- **AND** o ícone e o rótulo acessível alternam entre olho / “Mostrar senha” e olho riscado / “Ocultar senha”
- **AND** o controle é do tipo botão e não envia o formulário
