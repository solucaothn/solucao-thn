# Tarefas

## 1. Diagnóstico no navegador

- [ ] 1.1 (manual) Com `reflex run`, abrir `/cadastro-doacao` logado, digitar e colar texto em “Nome do item” e “Descrição” e anotar no DevTools a cor calculada (`color` e `-webkit-text-fill-color`) do `<input>` / `<textarea>` e o tema do sistema (claro ou escuro). Verificação: as cores anotadas confirmam ou descartam as hipóteses 1 e 2 do `design.md`.
- [ ] 1.2 (manual) Repetir a checagem em `/login`, `/cadastro`, `/recuperar-senha`, `/verificar-email`, `/nova-senha` e na busca da home, sem corrigir nada. Verificação: a tabela “Levantamento” do `design.md` ganha uma coluna “Confirmado no navegador” com sim/não por campo.

## 2. Posição da seta de retorno

- [ ] 2.1 Em `donation_creation_page()`, trocar o contêiner da seta por uma faixa de largura total alinhada à esquerda (`width="100%"`, sem `max_width` e sem `margin="0 auto"`, `padding="0.75rem 1.25rem 0"`), mantendo `href="/"` e `aria_label="Voltar ao início"`. Verificação: um teste em `tests/test_donation_creation.py` confirma que o contêiner não tem `max_width` nem margem automática e que o link mantém destino e rótulo; `python -m unittest discover -s tests -v` passa.
- [ ] 2.2 (manual) Conferir a seta em 1440 px, 1000 px e 360 px de largura e nas cinco etapas. Verificação: a seta fica logo abaixo do cabeçalho, junto à borda esquerda, não se desloca entre as etapas e não causa rolagem horizontal nem sobreposição.
- [ ] 2.3 Atualizar a seção “Cadastro de doação em cinco etapas” de `docs/design/README.md` com a posição da seta (canto superior esquerdo, abaixo do cabeçalho, destino `/`). Verificação: o texto bate com o requisito “Posição da seta de retorno do cadastro de doação”.

## 3. Cor do texto digitado

- [ ] 3.1 Acrescentar em `rx.App(style=...)` (`doafacil/doafacil.py`) a regra para `#donation-title, #donation-description` com `color: #1F1F1F`, `-webkit-text-fill-color: #1F1F1F` e `opacity: 1`, sem mudar as regras de placeholder nem as dos outros formulários. Verificação: um teste em `tests/test_donation_creation.py` confirma a regra em `app.style` e que `#donation-title::placeholder` e `#donation-description::placeholder` continuam `{"color": "#333333", "opacity": "1"}`; a suíte passa.
- [ ] 3.2 (manual) Repetir a medição da tarefa 1.1 com o tema claro e o escuro do sistema, digitando e colando nos dois campos. Verificação: a cor calculada do texto é `#1F1F1F` (rgb(31, 31, 31)) com opacidade 1 nos dois temas, e o placeholder segue `#333333`.
- [ ] 3.3 Registrar em `docs/design/README.md`, na mesma seção, que o texto digitado usa `#1F1F1F` e o placeholder `#333333`. Verificação: o texto bate com o requisito “Legibilidade dos textos de exemplo e seleção”.

## 4. Verificação final

- [ ] 4.1 Rodar `python -m unittest discover -s tests -v` e mostrar `git status` e `git diff --stat`. Verificação: todos os testes passam e só aparecem alterações em `doafacil/cadastro_doacao.py`, `doafacil/doafacil.py`, `tests/test_donation_creation.py`, `docs/design/README.md` e nos artefatos desta change; nada em `xano/`.
