## MODIFIED Requirements

### Requirement: Segurança e transparência
A página `/seguranca` SHALL ter a etiqueta “SAIBA MAIS SOBRE NOSSA”, o título “Segurança e Transparência”, o texto de apresentação, os 4 benefícios (Segurança em primeiro lugar, Sua privacidade importa, Transparência total, Seu parceiro de confiança) e os cartões “Criei uma doação” e “Doei em uma doação”, com textos fiéis ao que o site faz. Ao lado do texto de apresentação, a página SHALL mostrar a foto do Figma (nó 406:1243), com texto alternativo descritivo em português e, logo abaixo, o crédito da origem da foto.

#### Scenario: Abrir a página de segurança
- **WHEN** uma pessoa abre `/seguranca`
- **THEN** a página MUST mostrar esses blocos, com um ícone em cada benefício e cartão
- **AND** a imagem ao lado do texto de apresentação MUST ser a foto da página, não um placeholder

#### Scenario: Foto da segurança com formato do Figma, texto alternativo e crédito
- **WHEN** a foto da `/seguranca` aparece, em qualquer largura de tela
- **THEN** ela MUST manter a proporção do retângulo do Figma (507 × 339), com os cantos arredondados e preenchendo a área sem distorcer
- **AND** ela MUST ter um texto alternativo em português que descreve a cena
- **AND** logo abaixo dela MUST aparecer, em texto pequeno e legível, o crédito “Foto: ” seguido da origem da foto

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
