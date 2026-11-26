# institutional-pages Specification

## Purpose
Define as páginas institucionais públicas do DoaFácil (Central de ajuda, Segurança e transparência, Termos de uso, Política de privacidade, Quem somos e Contato), estáticas e com conteúdo fiel ao que o site realmente faz.

## Requirements

### Requirement: Estrutura comum das páginas institucionais
Cada página institucional SHALL ter o cabeçalho com o logotipo centralizado levando à home e os controles do site à direita (spec `site-navigation`), o link “Voltar ao início”, um único título de nível 1 seguido de títulos em ordem, o rodapé público da home e o botão flutuante do chat.

#### Scenario: Abrir uma página institucional
- **WHEN** uma pessoa abre `/duvidas`, `/seguranca`, `/termos`, `/privacidade`, `/quem-somos` ou `/contato`
- **THEN** a página MUST mostrar o cabeçalho com o logotipo (link para `/`), “Voltar ao início” (link para `/`), o conteúdo e o rodapé público da home
- **AND** MUST ter exatamente um título de nível 1, e os títulos seguintes MUST NOT pular níveis
- **AND** o conteúdo principal MUST ter a animação `page-fade-enter`, desligada com `prefers-reduced-motion`

#### Scenario: Página em 360 px
- **WHEN** qualquer página institucional é exibida com 360 px de largura
- **THEN** a página MUST NOT ter rolagem horizontal, os textos longos MUST quebrar linha e os controles MUST ter área de toque de pelo menos 44 px

#### Scenario: Controles do site no cabeçalho
- **WHEN** uma página institucional é exibida
- **THEN** o cabeçalho MUST mostrar à direita do logotipo, no desktop, “Entrar” ou o menu da conta e “Quero Doar”, e, abaixo de 992 px, o botão ☰
- **AND** o logotipo MUST continuar centralizado

### Requirement: Conteúdo verdadeiro
As páginas institucionais SHALL descrever só o que o DoaFácil realmente é e faz: um projeto acadêmico de doação de objetos, sem dinheiro, com os dados que o site de fato coleta. O e-mail de contato do projeto é `solucaothn@gmail.com`, definido na configuração do site.

#### Scenario: Sem dados ou serviços inexistentes
- **WHEN** qualquer página institucional é exibida
- **THEN** ela MUST NOT mencionar pagamentos, Pix, cartão, saques, tarifas, CPF, CNPJ, razão social, foro ou e-mails e endereços que o projeto não tem
- **AND** MUST NOT afirmar datas de fundação, números de doações ou medidas de segurança que o site não tem
- **AND** o único e-mail mostrado MUST ser o de contato do projeto, `solucaothn@gmail.com`

#### Scenario: Contato ainda não definido
- **WHEN** o e-mail de contato do projeto não está definido na configuração do site
- **THEN** os convites de contato (“Fale com a gente”, “Clique aqui para falar conosco”) MUST levar a `/contato`
- **AND** a página `/contato`, a caixa da Central de ajuda e as seções de contato dos Termos e da Privacidade MUST informar que o canal de contato ainda vai ser publicado, sem mostrar um endereço inventado

#### Scenario: Contato definido
- **WHEN** o e-mail de contato do projeto está definido na configuração do site (hoje, `solucaothn@gmail.com`)
- **THEN** “Fale com a gente” (Central de ajuda) e “Clique aqui para falar conosco” (rodapé) MUST levar a `/contato`, onde o e-mail aparece escrito, e não direto a um `mailto:` que não mostra o endereço
- **AND** a página `/contato` MUST mostrar o e-mail escrito e com link `mailto:`, e os links para a Central de ajuda e para a Política de privacidade
- **AND** nenhuma página institucional MUST dizer que o canal de contato ainda vai ser publicado

#### Scenario: Contato nos textos da Central de ajuda, dos Termos e da Privacidade
- **WHEN** o e-mail de contato está definido e a pessoa lê a caixa “Não encontrou o que procurava?”, a seção de contato dos Termos ou a seção de direitos da Política de privacidade
- **THEN** o texto MUST indicar esse e-mail, escrito e com link `mailto:`, como o canal de contato do projeto, inclusive para os pedidos sobre dados pessoais

### Requirement: Central de ajuda
A página `/duvidas` SHALL ter o título “Central de ajuda”, uma busca nas perguntas, atalhos de busca, as 6 categorias com a quantidade de perguntas, a lista “Mais perguntadas” e a caixa “Não encontrou o que procurava?”.

#### Scenario: Perguntas expansíveis
- **WHEN** a pessoa aciona uma pergunta, pelo mouse ou pelo teclado (Enter ou Espaço)
- **THEN** a resposta MUST aparecer abaixo da pergunta, e a pergunta aberta antes MUST fechar
- **AND** cada pergunta MUST ser um botão com o estado aberto ou fechado anunciado ao leitor de tela

#### Scenario: Buscar uma dúvida
- **WHEN** a pessoa digita um termo na busca ou aciona um atalho (“Tem taxa?”, “Quem paga a entrega”, “O que não pode doar”)
- **THEN** a página MUST mostrar “N resultados para “<termo>”” e só as perguntas cuja pergunta ou resposta contém o termo, sem diferenciar maiúsculas nem acentos
- **AND** sem resultados, MUST mostrar “Nenhuma resposta para “<termo>”” com a sugestão de tentar outra palavra ou escolher uma categoria
- **AND** com a busca vazia, MUST voltar às categorias e às “Mais perguntadas”

#### Scenario: Categorias
- **WHEN** a pessoa aciona uma das categorias (Primeiros passos, Doar um item, Receber uma doação, Conta e perfil, Segurança, Conversas)
- **THEN** a página `/duvidas/<categoria>` MUST abrir com o nome da categoria como título, a quantidade de perguntas, as perguntas da categoria em acordeão e o link “Voltar para dúvidas frequentes”
- **AND** um endereço de categoria inexistente MUST mostrar que a categoria não foi encontrada, com o link de volta para `/duvidas`

#### Scenario: Quantidades coerentes
- **WHEN** as categorias são exibidas
- **THEN** a quantidade mostrada em cada categoria MUST ser igual ao número de perguntas que ela realmente tem

### Requirement: Segurança e transparência
A página `/seguranca` SHALL ter a etiqueta “SAIBA MAIS SOBRE NOSSA”, o título “Segurança e Transparência”, o texto de apresentação, os 4 benefícios (Segurança em primeiro lugar, Sua privacidade importa, Transparência total, Seu parceiro de confiança) e os cartões “Criei uma doação” e “Recebi uma doação”, com textos fiéis ao que o site faz. Ao lado do texto de apresentação, a página SHALL mostrar a foto do Figma (nó 406:1243), com texto alternativo descritivo em português e, logo abaixo, o crédito da origem da foto.

#### Scenario: Abrir a página de segurança
- **WHEN** uma pessoa abre `/seguranca`
- **THEN** a página MUST mostrar esses blocos, com um ícone em cada benefício e cartão
- **AND** o texto de apresentação MUST dizer que a prioridade do DoaFácil é “a segurança e a transparência para todos”
- **AND** o cartão “Recebi uma doação” MUST orientar quem recebe: o DoaFácil não confere os itens, a entrega é combinada entre as pessoas e o item deve ser conferido antes de levar
- **AND** a imagem ao lado do texto de apresentação MUST ser a foto da página, não um placeholder

#### Scenario: Foto da segurança com formato do Figma, texto alternativo e crédito
- **WHEN** a foto da `/seguranca` aparece, em qualquer largura de tela
- **THEN** ela MUST manter a proporção do retângulo do Figma (507 × 339), com os cantos arredondados e preenchendo a área sem distorcer
- **AND** ela MUST ter um texto alternativo em português que descreve a cena
- **AND** logo abaixo dela MUST aparecer, em texto pequeno e legível, o crédito “Foto: ” seguido da origem da foto

### Requirement: Termos de uso e Política de privacidade
As páginas `/termos` e `/privacidade` SHALL apresentar textos escritos para o DoaFácil, organizados em seções numeradas com títulos. A Política de privacidade SHALL ter uma tabela dos dados tratados, com a finalidade e onde ficam guardados.

#### Scenario: Ler os termos
- **WHEN** uma pessoa abre `/termos`
- **THEN** a página MUST apresentar as regras de uso do DoaFácil como plataforma de doação de objetos entre pessoas, num projeto acadêmico, incluindo cadastro com e-mail confirmado, publicação de doações, combinação da entrega entre as pessoas e conduta no chat

#### Scenario: Ler a política de privacidade
- **WHEN** uma pessoa abre `/privacidade`
- **THEN** a tabela MUST listar só os dados que o site trata hoje: nome, e-mail, senha (guardada com hash), cidade e estado, foto de perfil, texto “Sobre”, doações e suas fotos, mensagens do chat e registros de eventos (número da conta, ação e horário, sem textos nem senhas)
- **AND** o texto MUST dizer o que é público (primeiro nome, foto, cidade/UF, Sobre e as doações disponíveis) e o que não é (e-mail, exceto quando a pessoa escolhe o contato por e-mail numa doação, e senha)

#### Scenario: Ligação entre as duas
- **WHEN** a pessoa lê os Termos ou a Política
- **THEN** cada uma MUST ter um link para a outra

#### Scenario: Aviso de documento acadêmico
- **WHEN** a pessoa abre `/termos` ou `/privacidade`
- **THEN** a página MUST mostrar, visível logo abaixo do título, a linha “Documento de projeto acadêmico, sem valor jurídico.”

### Requirement: Quem somos
A página `/quem-somos` SHALL ter a frase de missão “Conectar quem tem algo para doar com quem precisa, de um jeito simples, gratuito e transparente.”, com o destaque em “doar”, e a seção “COMO FOI” / “O início do DoaFácil” descrevendo o projeto acadêmico. Ao lado da frase de missão, a página SHALL mostrar a foto do Figma (nó 354:851), com texto alternativo descritivo em português e, logo abaixo, o crédito exigido pela licença da foto.

#### Scenario: Abrir a página Quem somos
- **WHEN** uma pessoa abre `/quem-somos`
- **THEN** a página MUST mostrar a frase de missão, a seção sobre o início do projeto e os blocos decorativos verdes
- **AND** a imagem ao lado da frase de missão MUST ser a foto da página, não um placeholder
- **AND** os blocos verdes MUST continuar decorativos, sem fotos, até o grupo trazer as fotos deles

#### Scenario: Foto com formato do Figma, texto alternativo e crédito
- **WHEN** a foto da `/quem-somos` aparece, em qualquer largura de tela
- **THEN** ela MUST manter a proporção do retângulo do Figma (375 × 421), com os cantos arredondados e preenchendo a área sem distorcer
- **AND** ela MUST ter um texto alternativo em português que descreve a cena
- **AND** logo abaixo dela MUST aparecer, em texto pequeno e legível, o crédito “Foto: Freepik”
