## ADDED Requirements

### Requirement: Posição da seta de retorno do cadastro de doação
A página `/cadastro-doacao` MUST apresentar a seta de retorno no canto superior esquerdo da área de conteúdo, logo abaixo do cabeçalho, alinhada à margem lateral esquerda da página e não ao conteúdo centralizado do wizard. A posição MUST ser a mesma nas cinco etapas. A seta MUST continuar levando à home (`/`) com o rótulo acessível “Voltar ao início”.

#### Scenario: Seta no canto em tela larga
- **WHEN** a pessoa abre `/cadastro-doacao` numa janela de 1440 px de largura
- **THEN** a seta MUST aparecer logo abaixo do cabeçalho, próxima à borda esquerda da janela, dentro da margem lateral da página
- **AND** MUST NOT ficar alinhada à coluna centralizada do formulário

#### Scenario: Mesma posição em todas as etapas
- **WHEN** a pessoa navega da etapa 1 à etapa 5 com “Continuar” e volta com “Voltar”
- **THEN** a seta MUST permanecer na mesma posição, sem deslocamento entre etapas

#### Scenario: Seta em tela estreita
- **WHEN** a pessoa abre `/cadastro-doacao` numa largura de celular (360 px)
- **THEN** a seta MUST continuar no canto superior esquerdo, sem sobrepor o cabeçalho, a barra de progresso ou os campos e sem causar rolagem horizontal

#### Scenario: Destino e rótulo preservados
- **WHEN** a pessoa ativa a seta pelo mouse ou pelo teclado
- **THEN** o sistema MUST levar à home (`/`)
- **AND** a seta MUST manter o rótulo acessível “Voltar ao início”

## MODIFIED Requirements

### Requirement: Legibilidade dos textos de exemplo e seleção
A interface MUST apresentar os textos de exemplo dos campos de texto do cadastro de doação em cinza médio legível, equivalente a `#6B6B6B`, para que não se confundam com texto digitado. Os prompts e textos de seleção MUST usar cor preta ou cinza bem escura, em todas as cinco etapas. O texto digitado ou colado MUST aparecer em cor escura opaca, mais escura que o texto de exemplo, independentemente do tema claro ou escuro do sistema.

#### Scenario: Texto de exemplo dos campos em cinza médio
- **WHEN** o campo “Nome do item” da etapa 1 ou o campo “Descrição” da etapa 2 está vazio
- **THEN** o texto de exemplo MUST usar cor equivalente a `#6B6B6B`, com opacidade total
- **AND** MUST NOT herdar a cor do texto digitado nem aparecer semitransparente

#### Scenario: Placeholders e prompts escuros
- **WHEN** qualquer etapa do cadastro apresenta um prompt de seleção, incluindo “Selecione uma categoria” e “Selecione a condição”
- **THEN** esses prompts MUST usar cor escura equivalente a `#333333` ou mais escura
- **AND** os textos de exemplo dos campos de texto MUST seguir o cenário “Texto de exemplo dos campos em cinza médio”, e não esta regra
- **AND** o placeholder de um Select do Radix MUST manter essa cor no elemento de conteúdo interno marcado pelo estado de placeholder, sem alterar o fundo do controle
- **AND** a regra MUST NOT alterar a aparência das opções na lista aberta

#### Scenario: Preferências de contato legíveis
- **WHEN** a quinta etapa apresenta o prompt e as opções de forma de contato
- **THEN** os textos “Selecione uma forma de contato”, “E-mail” e “Chat do DoaFácil” MUST permanecer em cor escura legível, sem aparência apagada

#### Scenario: Texto digitado legível
- **WHEN** a pessoa digita no campo “Nome do item” da etapa 1 ou no campo “Descrição” da etapa 2
- **THEN** o texto digitado MUST usar cor escura equivalente a `#1F1F1F` ou mais escura, com opacidade total
- **AND** MUST NOT herdar cor clara do tema nem aparecer semitransparente

#### Scenario: Texto colado legível
- **WHEN** a pessoa cola um texto num desses campos
- **THEN** o texto colado MUST aparecer com a mesma cor e opacidade do texto digitado

#### Scenario: Tema escuro do sistema
- **WHEN** o sistema operacional ou o navegador está no tema escuro e a pessoa digita num desses campos
- **THEN** o texto MUST continuar escuro e legível sobre o fundo branco do campo

#### Scenario: Placeholder volta ao apagar o texto
- **WHEN** a pessoa digita ou cola um texto em “Nome do item” ou “Descrição” e depois apaga todo o conteúdo
- **THEN** o campo MUST voltar a mostrar o texto de exemplo, em cor equivalente a `#6B6B6B`
- **AND** o valor do campo guardado pelo formulário MUST ficar vazio
