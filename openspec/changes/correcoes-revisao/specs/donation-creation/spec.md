## ADDED Requirements

### Requirement: Andamento visível da publicação
Ao acionar “Publicar doação”, a interface MUST mostrar o andamento desde o clique, antes do envio ao backend: o botão com o texto “Publicando...”, desativado, e o aviso “Enviando sua doação...”. O andamento MUST sumir quando a resposta chegar.

#### Scenario: Publicação em andamento
- **WHEN** a pessoa aciona “Publicar doação” com todos os dados válidos
- **THEN** o botão MUST aparecer como “Publicando...”, desativado, e o aviso “Enviando sua doação...” MUST aparecer antes de a resposta do backend chegar
- **AND** a publicação MUST fazer um único pedido ao backend

#### Scenario: Falha depois do andamento
- **WHEN** o backend recusa a publicação ou ocorre uma falha de rede
- **THEN** o aviso “Enviando sua doação...” MUST sumir e o botão MUST voltar a “Publicar doação”, habilitado, com a mensagem de erro e os dados mantidos

#### Scenario: Dados recusados pela tela
- **WHEN** a pessoa aciona “Publicar doação” e algum dado não passa na conferência da tela
- **THEN** a interface MUST mostrar a mensagem de erro sem mostrar o andamento e sem chamar o backend

### Requirement: Tentar de novo no carregamento do cadastro
Quando as categorias ou a localização do perfil não puderem ser carregadas ao abrir o cadastro, a interface MUST oferecer o botão “Tentar de novo”. Acioná-lo MUST mostrar “Preparando seu cadastro...” na hora e buscar os dados outra vez, com os mesmos pedidos da abertura.

#### Scenario: Tentar de novo depois da falha
- **WHEN** o carregamento do cadastro falha e a pessoa aciona “Tentar de novo”
- **THEN** a interface MUST mostrar “Preparando seu cadastro...” antes da resposta do backend
- **AND** com a resposta aceita, MUST mostrar o cadastro pronto para preencher

### Requirement: Aviso legal do cadastro
Acima dos botões de navegação, o cadastro MUST mostrar o aviso “Ao clicar no botão abaixo, você declara que é maior de 18 anos e que leu e concorda com os Termos de uso.”, com “Termos de uso” como link para `/termos`. O aviso MUST NOT citar documentos que o site não tem.

#### Scenario: Ler os Termos durante o cadastro
- **WHEN** a pessoa aciona o link “Termos de uso” do aviso
- **THEN** a página `/termos` MUST abrir em outra aba
- **AND** o cadastro em andamento MUST continuar na aba original, com os dados e as fotos preenchidos

#### Scenario: Texto do aviso
- **WHEN** o cadastro é exibido
- **THEN** o aviso MUST NOT mencionar taxas, prazos ou regulamentos

### Requirement: Título neutro da etapa de contato
A quinta etapa do cadastro MUST ter o título “Como prefere que entrem em contato?”.

#### Scenario: Abrir a etapa de contato
- **WHEN** a pessoa chega à quinta etapa do cadastro
- **THEN** o título MUST ser “Como prefere que entrem em contato?”
