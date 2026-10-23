# Tasks

## 1. Reinício do estado do formulário

- [x] 1.1 Reinicializar os campos e estados temporários do cadastro no início de cada `load_initial_data`, antes de carregar categorias e cidade/UF; acrescentar unittest simulando publicação concluída seguida de nova entrada e verificar passo 1, campos vazios, mensagens limpas e `published=False`, além de confirmar que os dados remotos da nova visita continuam sendo carregados.
- [x] 1.2 Limpar os arquivos selecionados pelo componente de upload no carregamento da página; acrescentar unittest para confirmar a ação de limpeza e que, após reiniciar, “Continuar” valida novamente o título e o passo das fotos volta a exigir ao menos uma imagem.

## 2. Verificação integrada e manual

- [x] 2.1 Executar `python -m unittest discover -s tests -v` e `.venv\Scripts\reflex.exe compile --dry`; corrigir falhas relacionadas ao reinício, confirmar que os testes existentes continuam passando sem alteração e que `test_navigation_preserves_fields` continua cobrindo a preservação dos campos ao avançar e voltar.
- [x] 2.2 (manual) No navegador, publicar uma doação de teste, abrir `/cadastro-doacao` novamente e conferir que o formulário está limpo no passo 1; preencher o passo 1, avançar até o passo 3, voltar e conferir que os dados continuam preenchidos; repetir a publicação e a conferência de formulário limpo após sair e entrar com outra conta na mesma aba. O Copilot não marca esta tarefa como concluída.
