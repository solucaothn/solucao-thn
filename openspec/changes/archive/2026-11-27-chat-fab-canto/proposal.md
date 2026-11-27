# Proposta

## Por quê

A change acabamento-visual (27/11/2026) subiu o botão flutuante do chat para ficar acima do selo “Built with Reflex”. Mas o selo só aparece com `reflex run --env prod`. No modo dev, que é como o projeto roda, ele não existe, e o botão ficou alto demais. O código já voltou à posição original (tarefa 2.3 da acabamento-visual, revertida). Só a spec `donation-chat-interface` ainda descreve o botão acima do selo.

## O que muda

- O cenário “Aparência do botão” volta ao texto original: o botão fica fixo a 24 px das bordas inferior e direita no computador e a 16 px no celular.
- O mesmo cenário passa a dizer o espaço livre no fim das páginas com o botão: 104 px no computador e 88 px no celular (o botão mais as duas margens), que é o valor que o código usa.

## Fora do escopo

- Qualquer mudança de código: `doafacil/chat.py` já usa 24/16 px e 104/88 px.
- O selo “Built with Reflex”, que continua como está no modo de produção.

## Capacidades

### Novas capacidades

Nenhuma.

### Capacidades modificadas

- `donation-chat-interface`: o cenário “Aparência do botão” do requisito “Entrada no chat pelo cabeçalho da home” volta ao canto da tela.

## Impacto

Só a spec. Nenhum código, teste, endpoint ou dependência muda.
