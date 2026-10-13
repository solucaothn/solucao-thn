# Design

## Context

O app Reflex centraliza estilos globais em `doafacil/doafacil.py`. As telas `login_page` e `signup_page` constroem cada cartão em um `rx.box` branco com estilo próprio. Ver `proposal.md` para a motivação e `specs/user-account/spec.md` para o comportamento esperado.

## Goals / Non-Goals

**Goals:**
- Compartilhar uma única animação CSS entre os dois cartões.
- Manter a animação isolada das demais telas e removê-la para quem prefere movimento reduzido.
- Preservar o layout e os comportamentos existentes.

**Non-Goals:**
- Animar o cabeçalho, o fundo, campos ou botões.
- Adicionar dependências, JavaScript, transições entre rotas ou animação na home.

## Decisions

- Usar uma classe CSS compartilhada aplicada somente ao `rx.box` que representa o cartão de cada formulário. Isso evita duplicar regras e não seleciona outros cartões ou elementos.
- Definir keyframes e o `@media (prefers-reduced-motion: reduce)` em um stylesheet CSS local referenciado pela configuração `stylesheets` da aplicação em `doafacil/doafacil.py`. A configuração atual usa `app.style` para seletores e `stylesheets` para arquivos CSS externos; um stylesheet local permite expressar diretamente regras CSS de keyframes e media query sem JavaScript ou biblioteca de animação.
- Usar animação de opacidade e `translateY` de aproximadamente 12px, por cerca de 0,3s com `ease-out`, sem atraso e com uma única execução. O media query desativa a animação; assim, o cartão não se move nem faz fade nessa preferência.
- Adicionar uma linha às descrições das telas 04 e 05 em `docs/design/README.md`, sem alterar o restante do documento.
- Para o fade da home, aplicar uma classe distinta diretamente aos elementos estáticos existentes (destaque, ilustração e seções informativas), sem criar um invólucro que altere o layout. Manter fora da animação o cabeçalho, a contagem e o carrossel carregados do Xano e o rodapé. A classe também respeita a preferência por movimento reduzido.
- Registrar a regra geral para páginas futuras em `AGENTS.md` e uma linha de referência na parte geral do `docs/design/README.md`.

## Risks / Trade-offs

- [A transformação pode parecer mais intensa em telas pequenas] → manter o deslocamento curto e animar somente o cartão; validar também com `reflex compile --dry` e testes estruturais.
- [CSS local pode não ser incluído pelo build se não estiver na pasta de assets ou registrado corretamente] → manter o arquivo no local servido pelo Reflex e testar a referência do stylesheet e suas regras.
