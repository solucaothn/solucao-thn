## MODIFIED Requirements

### Requirement: Consulta e atualização do perfil
O sistema SHALL permitir que uma pessoa autenticada consulte e atualize apenas o próprio perfil, incluindo nome, cidade, estado e o texto de Sobre. O e-mail MUST NOT ser alterado por essa atualização.

#### Scenario: Consultar perfil
- **WHEN** uma pessoa autenticada solicita seu perfil
- **THEN** o sistema retorna o identificador, a data de criação, o nome, o e-mail, a cidade, o estado e o texto de Sobre da própria conta
- **AND** um Sobre nunca preenchido MUST vir vazio ou nulo

#### Scenario: Atualizar perfil
- **WHEN** uma pessoa autenticada envia nome, cidade, estado e Sobre válidos para atualização
- **THEN** o sistema atualiza esses campos da própria conta e retorna identificador, data de criação, nome, e-mail, cidade, estado e Sobre atualizados
- **AND** o e-mail, a senha e as doações já publicadas MUST permanecer iguais

#### Scenario: Perfil com campo obrigatório inválido
- **WHEN** uma pessoa autenticada envia nome, cidade ou estado vazio
- **THEN** o sistema rejeita a atualização e mantém os valores existentes

#### Scenario: Estado fora das unidades federativas
- **WHEN** uma pessoa autenticada envia um estado que não é uma das 27 siglas de unidades federativas do Brasil
- **THEN** o sistema rejeita a atualização com HTTP 400 e mantém os valores existentes

#### Scenario: Sobre opcional e limitado
- **WHEN** uma pessoa autenticada envia o Sobre vazio
- **THEN** o sistema grava o Sobre vazio, apagando o texto anterior
- **AND** um Sobre com mais de 300 caracteres, depois de tirar os espaços das pontas, MUST ser rejeitado com HTTP 400 sem alterar o perfil

#### Scenario: Atualização sem sessão válida
- **WHEN** uma pessoa sem sessão válida tenta atualizar um perfil
- **THEN** o sistema responde HTTP 401 sem alterar dados

## ADDED Requirements

### Requirement: Página de edição do perfil
A página `/perfil/editar` MUST exigir login e permitir editar nome, Sobre, cidade e estado, com o e-mail só para leitura, seguindo o frame `Group 7` do Figma com as diferenças registradas em `docs/design/README.md`.

#### Scenario: Acesso sem login
- **WHEN** uma pessoa sem sessão válida abre `/perfil/editar` ou recebe HTTP 401 durante o uso
- **THEN** a página MUST levar a `/login` sem mostrar dados

#### Scenario: Entrada pela página Minhas doações
- **WHEN** a pessoa aciona “Editar perfil” no cartão da pessoa em `/minhas-doacoes`
- **THEN** o sistema MUST abrir `/perfil/editar`

#### Scenario: Cabeçalho e título
- **WHEN** a página é exibida, em qualquer estado
- **THEN** a linha do logotipo MUST mostrar, à esquerda, “Voltar a Minhas doações” em `#007A42`, com rótulo acessível e área de toque de pelo menos 44 px, levando a `/minhas-doacoes`
- **AND** o título “Editar perfil” MUST aparecer à esquerda, em negrito e verde

#### Scenario: Formulário preenchido
- **WHEN** a página carrega o perfil com sucesso
- **THEN** MUST mostrar os campos Nome, Sobre, Cidade e Estado preenchidos com os valores atuais
- **AND** Estado MUST permitir selecionar uma das 27 siglas de unidades federativas do Brasil
- **AND** MUST mostrar o e-mail num campo só de leitura, com o texto “O e-mail é usado para entrar e não pode ser alterado.”
- **AND** MUST NOT apresentar campo ou ação de foto de perfil

#### Scenario: Contador do Sobre
- **WHEN** a pessoa digita no campo Sobre
- **THEN** a página MUST mostrar o contador “N/300”, atualizado conforme o texto
- **AND** o campo MUST impedir mais de 300 caracteres

#### Scenario: Prévia do perfil
- **WHEN** a página está com o formulário preenchido
- **THEN** MUST mostrar, à esquerda, uma prévia com o círculo da inicial, o primeiro nome, “Cidade, UF” e o texto de Sobre, acompanhando o que a pessoa digita
- **AND** a prévia MUST NOT mostrar e-mail, contadores, foto, “Editar perfil” ou “Compartilhar”
- **AND** com o Sobre vazio, a prévia MUST NOT mostrar nada no lugar dele

#### Scenario: Quem vê estas informações
- **WHEN** a página está com o formulário
- **THEN** MUST mostrar o quadro “Quem vê estas informações”, explicando que o primeiro nome, a cidade, o estado e o Sobre são públicos e em que situação o e-mail é mostrado a outras pessoas, de forma coerente com a preferência de contato “E-mail” das doações

#### Scenario: Validação antes de enviar
- **WHEN** a pessoa salva com nome ou cidade vazios, estado não selecionado ou Sobre com mais de 300 caracteres
- **THEN** a página MUST indicar o campo a corrigir, MUST NOT enviar a requisição e MUST manter os valores digitados

#### Scenario: Salvar com sucesso
- **WHEN** a pessoa salva valores válidos
- **THEN** a página MUST enviar a atualização e mostrar “Alterações salvas.”
- **AND** o cabeçalho da home MUST passar a mostrar o primeiro nome novo, sem novo login

#### Scenario: Mudar a cidade não altera doações publicadas
- **WHEN** a pessoa muda a cidade ou o estado e salva
- **THEN** as doações já publicadas MUST manter a cidade e a UF do momento da publicação
- **AND** novas doações MUST usar a cidade e a UF novas

#### Scenario: Falha ao salvar
- **WHEN** o Xano recusa a atualização ou ocorre falha de rede ou HTTP 429
- **THEN** a página MUST mostrar uma mensagem de erro simples e manter os valores digitados

#### Scenario: Cancelar
- **WHEN** a pessoa aciona “Cancelar”
- **THEN** a página MUST voltar a `/minhas-doacoes` sem enviar requisição de atualização

#### Scenario: Texto de Sobre literal
- **WHEN** o Sobre contém marcação HTML ou quebras de linha
- **THEN** a prévia, o perfil público e o cartão de Minhas doações MUST apresentá-lo como texto simples, preservando as quebras de linha, sem interpretar HTML

#### Scenario: Layout, contraste e movimento
- **WHEN** a página é exibida numa largura de 360 px
- **THEN** a prévia e o formulário MUST aparecer em uma coluna, sem rolagem horizontal, e Cidade e Estado MAY ficar um abaixo do outro
- **AND** todos os textos e controles MUST ter contraste mínimo AA, inclusive o campo de e-mail só de leitura
- **AND** o cartão do formulário MUST usar a animação de entrada `auth-card-enter`, desativada com `prefers-reduced-motion`
