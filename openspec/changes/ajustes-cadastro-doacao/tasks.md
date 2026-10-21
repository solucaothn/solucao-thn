# Tasks

## 1. Opções do cadastro

- [ ] 1.1 Filtrar “Alimentos” e “Móveis” no frontend antes de popular as opções e os IDs válidos do wizard; ampliar `tests/test_donation_creation.py` para confirmar que essas categorias não aparecem, as demais são preservadas e a resposta do catálogo não é alterada.
- [ ] 1.2 Limitar as opções e a validação de entrega a “A combinar”; atualizar os testes de validação e publicação para confirmar que o payload continua enviando esse valor aceito pelo enum do endpoint existente, sem alterar `xano/`.

## 2. Legibilidade

- [ ] 2.1 Aplicar cor escura consistente aos placeholders e prompts dos selects e aos textos das opções de contato; adicionar testes estruturais dos textos/cores nos cinco passos, incluindo prompts de categoria e condição e opções do último passo.

## 3. Verificação integrada

- [ ] 3.1 Rodar `python -m unittest discover -s tests -v` e `.venv\Scripts\reflex.exe compile --dry`; confirmar que todos os testes passam, o wizard compila e não há alterações em `xano/`.
