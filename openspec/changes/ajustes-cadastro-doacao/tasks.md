# Tasks

## 1. Opções do cadastro

- [x] 1.1 Filtrar “Alimentos” e “Móveis” no frontend antes de popular as opções e os IDs válidos do wizard; ampliar `tests/test_donation_creation.py` para confirmar que essas categorias não aparecem, as demais são preservadas e a resposta do catálogo não é alterada.
- [x] 1.2 Limitar as opções e a validação de entrega a “A combinar”; atualizar os testes de validação e publicação para confirmar que o payload continua enviando esse valor aceito pelo enum do endpoint existente, sem alterar `xano/`.

## 2. Legibilidade

- [x] 2.1 Aplicar cor escura consistente aos placeholders e prompts dos selects e aos textos das opções de contato; adicionar testes estruturais dos textos/cores nos cinco passos, incluindo prompts de categoria e condição e opções do último passo.

## 3. Verificação integrada

- [x] 3.1 Rodar `python -m unittest discover -s tests -v` e `.venv\Scripts\reflex.exe compile --dry`; confirmar que todos os testes passam, o wizard compila e não há alterações em `xano/`.

## 4. Ajustes complementares no cadastro

- [x] 4.1 Estilizar o conteúdo `.rt-SelectTriggerInner` dos triggers marcados com `data-placeholder` para `#333333`, sem mudar fundos nem listas abertas; atualizar teste estrutural para o seletor interno e a cor.
- [x] 4.2 Garantir o avanço da etapa de fotos sem arquivos; testar a transição do passo 3 ao 4 sem fotos e a publicação multipart sem campo de arquivo; confirmar no endpoint local que `photos` é opcional.
- [x] 4.3 Remover “WhatsApp” das opções e da validação de contato; testar que “E-mail” e “Chat do DoaFácil” são válidos e “WhatsApp” é rejeitado, e confirmar que os dois valores constam no enum do endpoint local.
- [x] 4.4 Rodar `python -m unittest discover -s tests` e `.venv\Scripts\reflex.exe compile --dry`; confirmar que tudo passa e que não houve alterações em `xano/`.

## 5. Exemplo do item e foto obrigatória

- [x] 5.1 Trocar o placeholder do nome do item para “Ex.: Carrinho de brinquedo” e exigir ao menos uma foto para avançar do passo 3; adicionar testes estruturais e de evento para ausência/presença de foto, e atualizar `docs/design/README.md` para documentar a exigência mantendo o limite de cinco.
- [x] 5.2 Rodar `python -m unittest discover -s tests` e `.venv\Scripts\reflex.exe compile --dry`; confirmar os testes, compilação e ausência de alterações em `xano/`.
