# Tasks

## 1. Animação CSS e cartões

- [x] 1.1 Criar o stylesheet local com keyframes de fade e subida de aproximadamente 12px, duração de 0,3s e ease-out, desativação por `prefers-reduced-motion: reduce`, registrá-lo em `doafacil/doafacil.py` e testar presença das regras CSS.
- [x] 1.2 Aplicar a classe compartilhada somente ao cartão de `login_page` e acrescentar teste estrutural que confirme a classe no cartão sem animar o cabeçalho.
- [x] 1.3 Aplicar a mesma classe somente ao cartão de `signup_page` e acrescentar teste estrutural que confirme a classe no cartão sem animar o cabeçalho.

## 2. Documentação e verificação integrada

- [x] 2.1 Acrescentar uma linha nas seções 04 e 05 de `docs/design/README.md` registrando que a animação de entrada não está no Figma e conferir pelo diff que nenhuma outra seção mudou.
- [x] 2.2 Executar `python -m unittest discover -s tests -v` e `.venv\Scripts\reflex.exe compile --dry`; confirmar que todos os testes passam e que a compilação Reflex termina com sucesso.
