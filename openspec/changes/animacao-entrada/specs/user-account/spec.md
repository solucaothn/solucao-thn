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
