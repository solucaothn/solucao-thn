## ADDED Requirements

### Requirement: Enquadramento da foto de perfil
Antes do envio, a página `/perfil/editar` MUST deixar a pessoa enquadrar a foto escolhida num modal com moldura circular. Só a área enquadrada MUST ser enviada, como imagem quadrada de 512 × 512 px, pelo mesmo endpoint de envio da foto de perfil.

#### Scenario: Abrir o modal ao escolher uma foto válida
- **WHEN** a pessoa escolhe em “Alterar foto” um arquivo JPG, PNG, GIF ou WEBP com até 5 MB
- **THEN** a página MUST abrir um modal com a imagem escolhida, já na orientação correta, sob uma moldura circular
- **AND** MUST NOT enviar nenhuma requisição ao Xano antes de “Usar foto”

#### Scenario: Posicionar e dar zoom
- **WHEN** o modal está aberto
- **THEN** a pessoa MUST poder mover a imagem arrastando com o mouse ou o dedo e pelas setas do teclado
- **AND** MUST poder mudar o zoom por um controle deslizante com o rótulo “Zoom”, pela roda do mouse, por pinça no celular e pelas teclas `+` e `-`
- **AND** a imagem MUST cobrir sempre toda a moldura, sem área vazia dentro dela

#### Scenario: Cancelar
- **WHEN** a pessoa aciona “Cancelar” ou pressiona `Esc`
- **THEN** o modal MUST fechar sem enviar requisição, mantendo a foto atual e os valores já digitados no formulário

#### Scenario: Usar foto
- **WHEN** a pessoa aciona “Usar foto”
- **THEN** a página MUST enviar uma imagem quadrada de 512 × 512 px com exatamente a área que estava dentro da moldura, mostrando um estado de envio
- **AND** no sucesso, a seção “Foto” e a prévia MUST passar a mostrar a foto nova, com a mensagem curta de sucesso anunciada ao leitor de tela
- **AND** os valores já digitados no formulário MUST permanecer, sem serem salvos

#### Scenario: Formato do resultado
- **WHEN** a foto enquadrada é enviada
- **THEN** o resultado MUST manter o formato do original quando ele é JPG ou PNG
- **AND** um WEBP MUST virar PNG quando tiver algum pixel transparente, preservando a transparência, e JPEG quando não tiver
- **AND** um GIF MUST virar uma imagem PNG estática, com o primeiro quadro
- **AND** o resultado enviado MUST ser sempre JPEG ou PNG
- **AND** o resultado MUST NOT conter metadados do arquivo original, como a localização ou o modelo da câmera

#### Scenario: Orientação da câmera
- **WHEN** o arquivo traz a indicação de orientação (EXIF) de uma foto tirada com o celular girado
- **THEN** o modal e o resultado MUST mostrar a imagem na orientação em que foi fotografada, e não deitada ou de cabeça para baixo

#### Scenario: Arquivo que não é uma imagem legível
- **WHEN** o arquivo tem extensão e tipo aceitos, mas o conteúdo não pode ser lido como imagem
- **THEN** a página MUST mostrar “Envie uma imagem JPG, PNG, GIF ou WEBP.”, MUST NOT abrir o modal e MUST NOT enviar a requisição

#### Scenario: Área enquadrada inválida
- **WHEN** a área recebida para o recorte fica fora da imagem, tem largura ou altura nula ou não é um quadrado
- **THEN** o recorte MUST ficar limitado à imagem, sem área vazia, ou, se não houver área válida, a página MUST mostrar a mensagem de erro de envio sem enviar a requisição e mantendo a foto atual

#### Scenario: Acessibilidade e layout do modal
- **WHEN** o modal é exibido, inclusive numa largura de 360 px
- **THEN** o modal MUST caber na largura da tela, sem rolagem horizontal
- **AND** o foco MUST ficar preso no modal e voltar a “Alterar foto” ao fechar
- **AND** o modal MUST ter o título “Ajustar foto”, e a área de enquadramento MUST ter um rótulo acessível que explique como mover e dar zoom pelo teclado
- **AND** “Cancelar”, “Usar foto” e os controles de zoom MUST ter rótulos acessíveis, contraste mínimo AA e área de toque de pelo menos 44 px

## MODIFIED Requirements

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
- **THEN** a página MUST abrir o modal de enquadramento (veja “Enquadramento da foto de perfil”) e só enviar a foto quando a pessoa acionar “Usar foto”, sem depender de “Salvar alterações”
- **AND** durante o envio, MUST mostrar um estado de envio
- **AND** no sucesso, a seção “Foto” e a prévia MUST passar a mostrar a foto nova, com uma mensagem curta de sucesso anunciada ao leitor de tela
- **AND** os valores já digitados no formulário MUST permanecer, sem serem salvos

#### Scenario: Arquivo de formato ou tamanho inválido
- **WHEN** a pessoa escolhe um arquivo que não é JPG, PNG, GIF ou WEBP, que passa de 5 MB ou cujo conteúdo não pode ser lido como imagem
- **THEN** a página MUST mostrar uma mensagem clara sobre o formato ou o tamanho, MUST NOT abrir o modal de enquadramento e MUST NOT enviar a requisição
- **AND** quando o Xano recusar o arquivo com HTTP 400, a página MUST mostrar a mensagem correspondente, mantendo a foto anterior

#### Scenario: Remover a foto
- **WHEN** a pessoa aciona “Remover foto”
- **THEN** a página MUST remover a foto na hora, sem depender de “Salvar alterações”
- **AND** a seção “Foto” e a prévia MUST voltar ao círculo da inicial

#### Scenario: Falha ao enviar ou remover
- **WHEN** ocorre falha de rede, HTTP 429, falha ao preparar o recorte ou outro erro ao enviar ou remover a foto
- **THEN** a página MUST mostrar uma mensagem de erro simples e manter a foto anterior
- **AND** um HTTP 401 MUST limpar a sessão e levar a `/login`

#### Scenario: Contador do Sobre
- **WHEN** a pessoa digita no campo Sobre
- **THEN** a página MUST mostrar o contador “N/300”, atualizado conforme o texto
- **AND** o campo MUST impedir mais de 300 caracteres

#### Scenario: Prévia do perfil
- **WHEN** a página está com o formulário preenchido
- **THEN** MUST mostrar, à esquerda, uma prévia com a foto de perfil (ou, sem foto, o círculo da inicial), o primeiro nome, “Cidade, UF” e o texto de Sobre, acompanhando o que a pessoa digita
- **AND** a prévia MUST mostrar “Doações” com o contador de ativas e “Doações realizadas” com o contador de concluídas, como aparecem para outras pessoas
- **AND** a prévia MUST mostrar o selo “E-mail verificado” somente quando o e-mail da pessoa está verificado
- **AND** a prévia MUST NOT mostrar e-mail, “Editar perfil” ou “Compartilhar”
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
