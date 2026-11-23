## MODIFIED Requirements

### Requirement: Estado vazio e falha em Explorar
A página `/explorar` SHALL informar quando não há resultados e quando a busca falha, sem cartões fictícios. Sem filtros e sem resultados, SHALL convidar a pessoa a doar.

#### Scenario: Nenhum resultado
- **WHEN** a busca com texto, categoria ou estado não encontra doações
- **THEN** a página MUST mostrar “Nenhuma doação encontrada” e o link “Limpar filtros” para `/explorar`
- **AND** MUST NOT mostrar o convite para doar

#### Scenario: Nenhuma doação no site
- **WHEN** a busca sem filtros não encontra doações
- **THEN** a página MUST mostrar “Nenhuma doação encontrada”, uma frase convidando a pessoa a doar e o botão “Quero Doar”
- **AND** com sessão, o botão MUST levar a `/cadastro-doacao`; sem sessão, MUST levar a `/login?next=/cadastro-doacao`
- **AND** o botão MUST ter área de toque de pelo menos 44 px, foco visível e contraste mínimo AA, e MUST NOT ser mostrado o link “Limpar filtros”

#### Scenario: Falha da busca
- **WHEN** o serviço de busca falha
- **THEN** a página MUST informar que as doações não puderam ser carregadas, com um botão para tentar de novo
- **AND** numa falha ao carregar mais, os cartões já exibidos MUST continuar na tela
