# Proposta

## Por quê

O cadastro de doação (`/cadastro-doacao`) tem dois problemas visuais relatados por quem usa:

- **Seta de retorno fora do lugar.** A seta “<” fica dentro de uma faixa centralizada de até 1000 px. Em telas largas ela aparece solta, longe da borda, e não no canto superior esquerdo como no Figma (`docs/design/06-cadastro-de-doacao.png`).
- **Texto digitado difícil de ler.** O texto digitado ou colado nos campos aparece quase transparente, parecido com o placeholder. A spec atual garante a cor dos placeholders e prompts de seleção, mas não diz nada sobre o texto que a pessoa digita.

## O que muda

- A seta de retorno do cadastro de doação passa a ficar no canto superior esquerdo da área de conteúdo, logo abaixo do cabeçalho, na mesma posição nas cinco etapas e em qualquer largura de tela. O destino continua sendo a home (`/`) e o rótulo acessível continua “Voltar ao início”.
- O texto digitado ou colado no “Nome do item” (etapa 1) e na “Descrição” (etapa 2) passa a ter cor escura legível, mais escura que o placeholder, inclusive com o tema escuro do sistema operacional.
- O placeholder desses dois campos passa de `#333333` para `#6B6B6B`, igual aos outros formulários, para não parecer texto digitado, e volta a aparecer quando o campo é apagado. Os prompts dos Selects e as preferências de contato continuam escuros.
- Levantamento, sem correção nesta change, dos formulários de login, cadastro de conta e recuperação de senha que usam o mesmo padrão de campo. O resultado é registrado no design para uma change futura.

## Fora do escopo

- Corrigir login, cadastro de conta, recuperação de senha e a busca da home. Esses formulários só são verificados e listados.
- Mudar o destino da seta, os botões “Voltar” e “Continuar” do rodapé do wizard, a cor dos prompts dos Selects ou o conteúdo das etapas.
- Qualquer alteração no Xano (`xano/`) ou nas APIs.

## Capacidades

### Novas capacidades

Nenhuma.

### Capacidades modificadas

- `donation-creation`: o requisito “Legibilidade dos textos de exemplo e seleção” passa a cobrir também o texto digitado ou colado, muda o placeholder dos campos de texto para `#6B6B6B` e exige que ele volte quando o campo é apagado. Entra um requisito novo para a posição da seta de retorno.

## Impacto

- **Código:** `doafacil/cadastro_doacao.py` (posição da seta e estilo dos campos) e, se a correção usar regras globais por `id`, o dicionário `style` de `rx.App` em `doafacil/doafacil.py`, restrito a `#donation-title` e `#donation-description`.
- **Testes:** `tests/test_donation_creation.py`, mais um roteiro manual no navegador.
- **Documentação:** `docs/design/README.md`, seção “Cadastro de doação em cinco etapas”, com a posição da seta e a cor do texto digitado.
- **Sem impacto** em APIs, Xano, dependências ou dados.
