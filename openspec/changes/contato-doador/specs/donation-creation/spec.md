# Spec Delta

## Purpose

Permite informar ao doador que, ao escolher a preferência "E-mail" no cadastro de doação, o endereço de e-mail ficará disponível para pessoas autenticadas que quiserem entrar em contato.

## MODIFIED Requirements

### Requirement: Entrega e preferência de contato
O sistema MUST apresentar “A combinar” como única modalidade de entrega selecionável e MUST oferecer somente as preferências “E-mail” e “Chat do DoaFácil”. Esta change MUST persistir somente a preferência de contato e MUST NOT solicitar nem persistir telefone, endereço específico ou outro dado pessoal de contato.

#### Scenario: Publicação com entrega e preferência escolhidas
- **WHEN** o doador seleciona uma preferência de contato válida e a modalidade de entrega “A combinar”
- **THEN** ambas as escolhas MUST ser persistidas com a doação
- **AND** o frontend MUST enviar “A combinar”, valor aceito pelo endpoint de publicação existente
- **AND** a preferência MUST ser “E-mail” ou “Chat do DoaFácil”, ambos aceitos pelo endpoint existente

#### Scenario: Opção de contato removida
- **WHEN** o doador escolhe uma preferência de contato
- **THEN** a interface MUST oferecer “E-mail” e “Chat do DoaFácil” e MUST NOT oferecer “WhatsApp”

#### Scenario: Dados pessoais de contato não solicitados
- **WHEN** o doador preenche o passo de contato
- **THEN** a interface MUST apresentar apenas a escolha de preferência e MUST NOT solicitar número de telefone, endereço de contato ou identificador externo

#### Scenario: Aviso de visibilidade do e-mail
- **WHEN** o doador seleciona “E-mail” como preferência de contato na quinta etapa
- **THEN** a interface MUST exibir o aviso curto: “Seu e-mail ficará disponível para pessoas logadas que quiserem falar com você.”
- **AND** MUST manter a seleção da preferência e o restante do fluxo de publicação sem alterar as etapas anteriores

#### Scenario: Escolha de chat sem aviso de e-mail
- **WHEN** o doador seleciona “Chat do DoaFácil” como preferência de contato
- **THEN** a interface MUST NÃO exibir o aviso de disponibilidade de e-mail
- **AND** MUST continuar seguindo o comportamento atual do wizard
