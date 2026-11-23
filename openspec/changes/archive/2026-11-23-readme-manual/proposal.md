# Proposta: README como manual de uso

## Why

A disciplina pede um manual de uso do DoaFácil para usuários e para o professor, com uma estrutura definida (apresentação, acesso, perfis, funcionalidades, passo a passo, exemplos e limitações). Hoje o repositório não tem `README.md` na raiz: quem chega pelo GitHub não encontra como rodar o site nem como usá-lo, e a documentação existente (`docs/guia-do-colaborador.md`) é técnica, escrita para quem desenvolve.

## What Changes

- Criar o `README.md` da raiz como manual de uso, em português, para quem usa o site (não para quem desenvolve), nesta ordem:
  1. Apresentação: nome, descrição curta, problema que resolve e público-alvo.
  2. Acesso ao aplicativo: não há deploy; como rodar localmente (clone, ambiente virtual, `pip install -r requirements.txt`, as duas variáveis do Xano fornecidas pelo grupo, `reflex run` e `http://localhost:3000`), requisitos e o aviso de que os dados vêm do Xano compartilhado.
  3. Perfis de usuários: visitante, quem doa e quem tem interesse, com o que cada um pode fazer.
  4. Funcionalidades principais.
  5. Manual de utilização: passo a passo por jornada, com ação, resultado esperado e um espaço de captura de tela por passo (`![descrição](docs/manual/NN-nome.png)`).
  6. Exemplos de utilização: um cenário completo (Mariana doa um teclado, Lucas conversa pelo chat, ela marca como concluída) e os dados a cadastrar para a demonstração.
  7. Limitações conhecidas.
  - No fim: “Equipe” com espaço para os nomes, o link para a documentação técnica e a lista das capturas de tela a tirar.
- Criar `docs/README-tecnico.md`, a porta de entrada técnica (stack, como rodar, testes e onde está cada documento). Como não existe README anterior, não há conteúdo técnico a mover; o detalhe técnico continua no `docs/guia-do-colaborador.md`.
- Criar a pasta `docs/manual/` (com um `.gitkeep`) para as capturas.
- Todo o conteúdo do manual é conferido no código atual; nada de funcionalidade que o site não tem.

## Capabilities

### New Capabilities

(nenhuma)

### Modified Capabilities

(nenhuma — a change só cria documentação e não muda o comportamento do sistema; o `.openspec.yaml` declara `skip_specs: true`)

## Impact

- Novos arquivos: `README.md`, `docs/README-tecnico.md` e `docs/manual/.gitkeep`.
- Nenhuma mudança no código, nos testes, no Xano ou nas APIs.
- O manual não contém URLs do Xano, tokens, chaves nem e-mails pessoais; só o contato público do projeto (`solucaothn@gmail.com`).

## Fora do escopo

- Tirar as capturas de tela (o manual lista quais são; quem tira é o grupo).
- Fazer deploy do site.
- Mudar o `docs/guia-do-colaborador.md`, salvo o link para a nova porta de entrada técnica.
