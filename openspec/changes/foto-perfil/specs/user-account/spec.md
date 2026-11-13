## MODIFIED Requirements

### Requirement: Consulta e atualização do perfil
O sistema SHALL permitir que uma pessoa autenticada consulte e atualize apenas o próprio perfil, incluindo nome, cidade, estado e o texto de Sobre. A consulta também devolve a URL pública da foto de perfil. O e-mail e a foto MUST NOT ser alterados por essa atualização.

#### Scenario: Consultar perfil
- **WHEN** uma pessoa autenticada solicita seu perfil
- **THEN** o sistema retorna o identificador, a data de criação, o nome, o e-mail, a cidade, o estado, o texto de Sobre e a URL pública da foto de perfil da própria conta
- **AND** sem foto, a URL MUST vir nula
- **AND** um Sobre nunca preenchido MUST vir vazio ou nulo

#### Scenario: Atualizar perfil
- **WHEN** uma pessoa autenticada envia nome, cidade, estado e Sobre válidos para atualização
- **THEN** o sistema atualiza esses campos da própria conta e retorna identificador, data de criação, nome, e-mail, cidade, estado e Sobre atualizados
- **AND** o e-mail, a senha, a foto de perfil e as doações já publicadas MUST permanecer iguais

#### Scenario: Perfil com campo obrigatório inválido
- **WHEN** uma pessoa autenticada envia nome, cidade ou estado vazio
- **THEN** o sistema rejeita a atualização e mantém os valores existentes

#### Scenario: Estado fora das unidades federativas
- **WHEN** uma pessoa autenticada envia um estado que não é uma das 27 siglas de unidades federativas do Brasil
- **THEN** o sistema rejeita a atualização com HTTP 400 e mantém os valores existentes

#### Scenario: Sobre sempre gravado
- **WHEN** uma pessoa autenticada envia uma atualização do perfil
- **THEN** o sistema MUST gravar o Sobre em toda atualização: com texto, grava o texto sem os espaços das pontas
- **AND** com o Sobre vazio, nulo ou omitido, MUST gravar o Sobre vazio, apagando o texto anterior
- **AND** um Sobre com mais de 300 caracteres, depois de tirar os espaços das pontas, MUST ser rejeitado com HTTP 400 sem alterar o perfil

#### Scenario: Atualização sem sessão válida
- **WHEN** uma pessoa sem sessão válida tenta atualizar um perfil
- **THEN** o sistema responde HTTP 401 sem alterar dados

### Requirement: Página de edição do perfil
A página `/perfil/editar` MUST exigir login e permitir trocar ou remover a foto de perfil e editar nome, Sobre, cidade e estado, com o e-mail só para leitura, seguindo o frame `Group 7` do Figma com as diferenças registradas em `docs/design/README.md`.

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
- **AND** o campo Nome MUST conter o nome completo da conta, com a ajuda “Só o primeiro nome aparece para outras pessoas.”
- **AND** o campo Sobre MUST aceitar quebras de linha e mostrar a dica “Não coloque telefone, endereço ou e-mail: este texto é público.”
- **AND** Estado MUST permitir selecionar uma das 27 siglas de unidades federativas do Brasil
- **AND** MUST mostrar o e-mail num campo só de leitura, com o texto “O e-mail é usado para entrar e não pode ser alterado.”
- **AND** o campo de e-mail MUST ser somente leitura e não desativado, para permitir selecionar e copiar, com texto `#1F1F1F` sobre fundo `#F1F1F1`, um ícone de cadeado `#6B6B6B` dentro do campo à direita, o rótulo acessível “E-mail (não pode ser alterado)” e cursor padrão

#### Scenario: Seção Foto
- **WHEN** a página carrega o perfil com sucesso
- **THEN** MUST mostrar, antes de “Dados públicos”, a seção “Foto” com a foto atual (ou o círculo da inicial), o botão “Alterar foto”, os formatos aceitos “JPG, PNG, GIF ou WEBP, até 5 MB” e o aviso “Sua foto aparece para outras pessoas.”
- **AND** “Remover foto” MUST aparecer somente quando a pessoa tem foto
- **AND** os controles MUST ser acessíveis pelo teclado, com área de toque de pelo menos 44 px

#### Scenario: Enviar uma foto nova
- **WHEN** a pessoa escolhe em “Alterar foto” um arquivo JPG, PNG, GIF ou WEBP com até 5 MB
- **THEN** a página MUST enviar a foto na hora, sem depender de “Salvar alterações”, e mostrar um estado de envio
- **AND** no sucesso, a seção “Foto” e a prévia MUST passar a mostrar a foto nova, com uma mensagem curta de sucesso anunciada ao leitor de tela
- **AND** os valores já digitados no formulário MUST permanecer, sem serem salvos

#### Scenario: Arquivo de formato ou tamanho inválido
- **WHEN** a pessoa escolhe um arquivo que não é JPG, PNG, GIF ou WEBP, ou que passa de 5 MB
- **THEN** a página MUST mostrar uma mensagem clara sobre o formato ou o tamanho e MUST NOT enviar a requisição
- **AND** quando o Xano recusar o arquivo com HTTP 400, a página MUST mostrar a mensagem correspondente, mantendo a foto anterior

#### Scenario: Remover a foto
- **WHEN** a pessoa aciona “Remover foto”
- **THEN** a página MUST remover a foto na hora, sem depender de “Salvar alterações”
- **AND** a seção “Foto” e a prévia MUST voltar ao círculo da inicial

#### Scenario: Falha ao enviar ou remover
- **WHEN** ocorre falha de rede, HTTP 429 ou outro erro ao enviar ou remover a foto
- **THEN** a página MUST mostrar uma mensagem de erro simples e manter a foto anterior
- **AND** um HTTP 401 MUST limpar a sessão e levar a `/login`

#### Scenario: Contador do Sobre
- **WHEN** a pessoa digita no campo Sobre
- **THEN** a página MUST mostrar o contador “N/300”, atualizado conforme o texto
- **AND** o campo MUST impedir mais de 300 caracteres

#### Scenario: Prévia do perfil
- **WHEN** a página está com o formulário preenchido
- **THEN** MUST mostrar, à esquerda, uma prévia com a foto de perfil (ou, sem foto, o círculo da inicial), o primeiro nome, “Cidade, UF” e o texto de Sobre, acompanhando o que a pessoa digita
- **AND** a prévia MUST NOT mostrar e-mail, contadores, “Editar perfil” ou “Compartilhar”
- **AND** com o Sobre vazio, a prévia MUST NOT mostrar nada no lugar dele

#### Scenario: Quem vê estas informações
- **WHEN** a página está com o formulário
- **THEN** MUST mostrar o quadro “Quem vê estas informações” com o texto: “Seu primeiro nome, sua foto, cidade, estado e o texto de Sobre aparecem no seu perfil público. Suas doações mostram o primeiro nome, a foto atual e a cidade e o estado do momento em que foram publicadas. Seu e-mail é usado para entrar e só é mostrado a pessoas logadas que pedirem contato numa doação sua com a preferência “E-mail”.”

#### Scenario: Validação antes de enviar
- **WHEN** a pessoa salva com nome ou cidade vazios, estado não selecionado ou Sobre com mais de 300 caracteres
- **THEN** a página MUST indicar o campo a corrigir, MUST NOT enviar a requisição e MUST manter os valores digitados

#### Scenario: Salvar com sucesso
- **WHEN** a pessoa salva valores válidos
- **THEN** a página MUST enviar o formulário inteiro (nome, cidade, estado e Sobre, mesmo vazio) e voltar a `/minhas-doacoes`, que mostra o aviso “Alterações salvas.”
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

#### Scenario: Texto digitado legível
- **WHEN** a pessoa digita ou cola um texto em Nome, Sobre ou Cidade, inclusive com o tema escuro do sistema
- **THEN** o texto MUST aparecer em `#1F1F1F`, com opacidade total
- **AND** os textos de exemplo MUST aparecer em `#6B6B6B`, com opacidade total

#### Scenario: Layout, contraste e movimento
- **WHEN** a página é exibida numa largura de 360 px
- **THEN** a prévia e o formulário MUST aparecer em uma coluna, sem rolagem horizontal, e Cidade e Estado MAY ficar um abaixo do outro
- **AND** todos os textos e controles MUST ter contraste mínimo AA, inclusive o campo de e-mail só de leitura
- **AND** o cartão do formulário MUST usar a animação de entrada `auth-card-enter`, desativada com `prefers-reduced-motion`

## ADDED Requirements

### Requirement: Foto de perfil
O sistema MUST permitir que a pessoa autenticada envie e remova somente a própria foto de perfil, por endpoints próprios. A foto MUST ser uma imagem JPG, PNG, GIF ou WEBP de até 5 MB, guardada com acesso público. A pessoa é sempre derivada da sessão.

#### Scenario: Enviar foto válida
- **WHEN** uma pessoa autenticada envia uma imagem aceita
- **THEN** o sistema MUST guardar a imagem como foto de perfil da própria conta, substituindo a anterior
- **AND** MUST responder com a URL pública da foto nova, sem e-mail nem identificadores

#### Scenario: Formato não aceito
- **WHEN** o arquivo enviado não é JPG, PNG, GIF ou WEBP
- **THEN** o endpoint MUST responder HTTP 400 com a mensagem “Envie uma imagem JPG, PNG, GIF ou WEBP.”
- **AND** MUST NOT alterar a foto atual

#### Scenario: Arquivo grande demais
- **WHEN** o arquivo enviado passa de 5 MB
- **THEN** o endpoint MUST responder HTTP 400 com a mensagem “A foto pode ter no máximo 5 MB.”
- **AND** MUST NOT alterar a foto atual

#### Scenario: Envio sem arquivo
- **WHEN** a requisição de envio não traz arquivo
- **THEN** o endpoint MUST responder HTTP 400 sem alterar a foto atual
- **AND** a mensagem MAY ser a da própria plataforma, que recusa a requisição antes de executar o endpoint; a página só envia com um arquivo escolhido

#### Scenario: Remover a foto
- **WHEN** uma pessoa autenticada remove a foto de perfil
- **THEN** o sistema MUST deixar a conta sem foto, e as respostas que trazem a foto MUST passar a trazê-la nula
- **AND** remover quando já não há foto MUST responder com sucesso, sem erro

#### Scenario: Envio ou remoção sem sessão válida
- **WHEN** uma pessoa sem sessão válida tenta enviar ou remover uma foto
- **THEN** o endpoint MUST responder HTTP 401 sem alterar dados

#### Scenario: Foto de outra pessoa
- **WHEN** qualquer requisição de envio ou remoção é feita
- **THEN** ela MUST alterar somente a conta da sessão, sem aceitar identificador de usuário enviado pelo cliente
