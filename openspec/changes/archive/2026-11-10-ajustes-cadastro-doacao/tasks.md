# Tarefas

## 1. Diagnóstico no navegador

- [x] 1.1 (manual) Com `reflex run`, abrir `/cadastro-doacao` logado, digitar e colar texto em “Nome do item” e “Descrição” e anotar no DevTools a cor calculada (`color` e `-webkit-text-fill-color`) do `<input>` / `<textarea>` e o tema do sistema (claro ou escuro). Verificação: as cores anotadas confirmam ou descartam as hipóteses 1 e 2 do `design.md`. *Registro: o print do problema antes da correção serve de evidência; a causa exata não foi medida no DevTools.*
- [x] 1.2 (manual) Repetir a checagem em `/login`, `/cadastro`, `/recuperar-senha`, `/verificar-email`, `/nova-senha` e na busca da home, sem corrigir nada. Verificação: a tabela “Levantamento” do `design.md` ganha uma coluna “Confirmado no navegador” com sim/não por campo.

## 2. Posição da seta de retorno

- [x] 2.1 Em `donation_creation_page()`, trocar o contêiner da seta por uma faixa de largura total alinhada à esquerda (`width="100%"`, sem `max_width` e sem `margin="0 auto"`, `padding="0.75rem 1.25rem 0"`), mantendo `href="/"` e `aria_label="Voltar ao início"`. Verificação: um teste em `tests/test_donation_creation.py` confirma que o contêiner não tem `max_width` nem margem automática e que o link mantém destino e rótulo; `python -m unittest discover -s tests -v` passa.
- [x] 2.2 (manual) Conferir a seta em 1440 px, 1000 px e 360 px de largura e nas cinco etapas. Verificação: a seta fica logo abaixo do cabeçalho, junto à borda esquerda, não se desloca entre as etapas e não causa rolagem horizontal nem sobreposição.
- [x] 2.3 Atualizar a seção “Cadastro de doação em cinco etapas” de `docs/design/README.md` com a posição da seta (canto superior esquerdo, abaixo do cabeçalho, destino `/`). Verificação: o texto bate com o requisito “Posição da seta de retorno do cadastro de doação”.

## 3. Cor do texto digitado

- [x] 3.1 Acrescentar em `rx.App(style=...)` (`doafacil/doafacil.py`) a regra para `#donation-title, #donation-description` com `color: #1F1F1F`, `-webkit-text-fill-color: #1F1F1F` e `opacity: 1`, sem mudar as regras de placeholder nem as dos outros formulários. Verificação: um teste em `tests/test_donation_creation.py` confirma a regra em `app.style` e que `#donation-title::placeholder` e `#donation-description::placeholder` continuam `{"color": "#333333", "opacity": "1"}`; a suíte passa.
- [x] 3.2 (manual) Repetir a medição da tarefa 1.1 com o tema claro e o escuro do sistema, digitando e colando nos dois campos. Verificação: a cor calculada do texto é `#1F1F1F` (rgb(31, 31, 31)) com opacidade 1 nos dois temas, e o placeholder segue `#333333`. *Registro: texto escuro confirmado nos dois temas, nas cinco etapas e no modo celular. A cor do placeholder muda no grupo 5.*
- [x] 3.3 Registrar em `docs/design/README.md`, na mesma seção, que o texto digitado usa `#1F1F1F` e o placeholder `#333333`. Verificação: o texto bate com o requisito “Legibilidade dos textos de exemplo e seleção”.

## 4. Verificação final

- [x] 4.1 Rodar `python -m unittest discover -s tests -v` e mostrar `git status` e `git diff --stat`. Verificação: todos os testes passam e só aparecem alterações em `doafacil/cadastro_doacao.py`, `doafacil/doafacil.py`, `tests/test_donation_creation.py`, `docs/design/README.md` e nos artefatos desta change; nada em `xano/`.

## 5. Placeholder que não volta e nova cor do placeholder

- [x] 5.1 Nas regras `#donation-title::placeholder` e `#donation-description::placeholder` de `rx.App(style=...)`, trocar a cor para `#6B6B6B` e acrescentar `-webkit-text-fill-color: #6B6B6B`, para que o placeholder não herde o `#1F1F1F` do campo. Os prompts de seleção e as preferências de contato continuam `#333333`. Verificação: o teste de legibilidade em `tests/test_donation_creation.py` confere `{"color": "#6B6B6B", "WebkitTextFillColor": "#6B6B6B", "opacity": "1"}` nos dois placeholders, a regra do texto digitado e os prompts em `#333333`; a suíte passa.
- [x] 5.2 Atualizar `docs/design/README.md` (cor do placeholder `#6B6B6B` e motivo do `-webkit-text-fill-color`) e a tabela “Levantamento” do `design.md` com o resultado da tarefa 1.2. Verificação: o texto bate com o requisito “Legibilidade dos textos de exemplo e seleção”.
- [x] 5.3 (manual) Em “Nome do item” e “Descrição”, digitar e apagar tudo, e depois colar e apagar tudo, nos temas claro e escuro. Verificação: o placeholder volta em cinza `#6B6B6B` (rgb(107, 107, 107)), visivelmente mais claro que o texto digitado; se o campo ficar vazio sem placeholder, registrar e voltar à investigação do `DebounceInput` (veja o `design.md`).
