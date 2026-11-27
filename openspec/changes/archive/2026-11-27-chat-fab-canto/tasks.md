# Tarefas

Os comandos `git` e `xano` são do Higor. Esta change só altera a spec: o código já está no canto desde a reversão da tarefa 2.3 da acabamento-visual.

## 1. Spec

- [x] 1.1 Devolver o cenário “Aparência do botão” de `donation-chat-interface` ao texto original (24 px das bordas no computador e 16 px no celular), com o espaço livre de 104/88 px no fim das páginas. Verificação: `openspec validate chat-fab-canto --strict` sem erros.

## 2. Conferência

- [x] 2.1 Conferir que o código bate com a spec: `CHAT_FAB_OFFSET` com 16/24 px e `CHAT_FAB_CLEARANCE` com 88/104 px em `doafacil/chat.py`. Verificação: a suíte completa passa, incluindo `tests/test_chat.py` e `tests/test_acabamento_visual.py`.
- [x] 2.2 Depois de arquivar, rodar `openspec validate --specs --strict`. Verificação: todas as specs válidas e sem menção a 72 px, 60 px ou ao selo na spec `donation-chat-interface`. Verificado em 27/11/2026: 18 specs válidas; a spec mostra “a 24 px das bordas inferior e direita no computador, e a 16 px no celular” e o espaço de 104/88 px, sem menção ao selo.
