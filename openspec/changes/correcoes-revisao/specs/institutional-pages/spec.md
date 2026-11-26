## MODIFIED Requirements

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
