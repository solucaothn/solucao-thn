# Tarefas

Os comandos `git` e `xano` são do Higor. Change só de documentação (`skip_specs: true`); o design é dispensado por não haver decisão técnica.

## 1. Manual de uso

- [x] 1.1 Escrever o `README.md` da raiz com as 7 seções pedidas, a “Equipe”, o link para `docs/README-tecnico.md` e a lista de capturas de tela. Verificação: o arquivo tem os títulos “1. Apresentação” a “7. Limitações conhecidas”, “Equipe” e “Capturas de tela a tirar”, nessa ordem.
- [x] 1.2 Conferir cada passo do manual no código atual (rotas em `doafacil/doafacil.py`, textos dos botões e mensagens nos módulos de cada tela). Verificação: `tests/test_readme_manual.py` confere que as rotas citadas no `README.md` existem em `doafacil/doafacil.py` e que os rótulos de botões e mensagens citados existem no código.
- [x] 1.3 Conferir que cada `![…](docs/manual/NN-nome.png)` do manual aparece na lista de capturas, sem nome repetido, e que o manual não tem URL do Xano, token nem e-mail além do `solucaothn@gmail.com`. Verificação: o mesmo teste.

## 2. Documentação técnica

- [x] 2.1 Criar `docs/README-tecnico.md` (stack, variáveis de ambiente, como rodar, testes, estrutura e links para `docs/guia-do-colaborador.md`, `docs/project-overview.md`, `docs/domain-model.md`, `docs/design/README.md` e `AGENTS.md`) e `docs/manual/.gitkeep`. Verificação: os links relativos do `README.md` e do `docs/README-tecnico.md` apontam para arquivos que existem (conferido pelo teste da tarefa 1.2).

## 3. Verificação

- [x] 3.1 Rodar a suíte inteira. Verificação: `python -m unittest discover -s tests` passa.
- [x] 3.2 Roteiro manual (para o Higor e o grupo): tirar as capturas da lista, salvá-las em `docs/manual/` com os nomes indicados, preencher a “Equipe” e conferir o README renderizado no GitHub.
