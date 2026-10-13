# Spec Delta

## ADDED Requirements

### Requirement: Entrada animada nas telas de autenticação
A aplicação SHALL animar somente o cartão das telas públicas de login e cadastro ao abrir cada página.

#### Scenario: Animar o cartão ao abrir login ou cadastro
- **WHEN** uma pessoa abre `/login` ou `/cadastro` com preferência padrão de movimento
- **THEN** somente o cartão branco aparece uma vez com fade e subida de aproximadamente 12px, em cerca de 0,3 segundo com aceleração ease-out
- **AND** o cabeçalho, o fundo, o layout, o foco e o comportamento dos formulários permanecem inalterados

#### Scenario: Respeitar preferência por movimento reduzido
- **WHEN** o sistema operacional ou navegador indica `prefers-reduced-motion: reduce`
- **THEN** os cartões de login e cadastro aparecem sem animação

### Requirement: Entrada suave do conteúdo estático da home
A aplicação SHALL aplicar um fade de entrada ao conteúdo estático da home sem animar o cabeçalho, o rodapé ou dados carregados do Xano.

#### Scenario: Retornar do login para a home
- **WHEN** uma pessoa aciona “← Voltar” no login e a home é exibida
- **THEN** as seções estáticas da home aparecem com fade de opacidade por cerca de 0,3 segundo com aceleração ease-out
- **AND** a animação não altera o layout nem a contagem e o carrossel de doações

#### Scenario: Respeitar movimento reduzido na home
- **WHEN** o sistema operacional ou navegador indica `prefers-reduced-motion: reduce`
- **THEN** as seções estáticas da home aparecem sem animação
