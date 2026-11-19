## MODIFIED Requirements

### Requirement: Posição da seta de retorno do cadastro de doação
A página `/cadastro-doacao` MUST apresentar a seta de retorno na linha do logotipo, à esquerda, no mesmo cabeçalho das outras páginas com “Voltar” (spec `site-navigation`), e não numa faixa própria abaixo do cabeçalho. A posição MUST ser a mesma nas cinco etapas. A seta MUST continuar levando à home (`/`) com o rótulo acessível “Voltar ao início”.

#### Scenario: Seta no canto em tela larga
- **WHEN** a pessoa abre `/cadastro-doacao` numa janela de 1440 px de largura
- **THEN** a seta MUST aparecer na linha do logotipo, à esquerda, alinhada à margem do cabeçalho
- **AND** MUST NOT ficar alinhada à coluna centralizada do formulário nem numa faixa solta abaixo do cabeçalho

#### Scenario: Mesma posição em todas as etapas
- **WHEN** a pessoa navega da etapa 1 à etapa 5 com “Continuar” e volta com “Voltar”
- **THEN** a seta MUST permanecer na mesma posição, sem deslocamento entre etapas

#### Scenario: Seta em tela estreita
- **WHEN** a pessoa abre `/cadastro-doacao` numa largura de celular (360 px)
- **THEN** a seta MUST continuar à esquerda na linha do logotipo, com 44 px de área de toque, sem sobrepor o logotipo, a barra de progresso ou os campos e sem causar rolagem horizontal

#### Scenario: Destino e rótulo preservados
- **WHEN** a pessoa ativa a seta pelo mouse ou pelo teclado
- **THEN** o sistema MUST levar à home (`/`)
- **AND** a seta MUST manter o rótulo acessível “Voltar ao início”
