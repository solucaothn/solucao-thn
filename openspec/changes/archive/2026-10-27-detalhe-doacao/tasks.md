# Tasks

## 1. API pública no Xano

- [x] 1.1 Conferir `git status` e registrar que os oito arquivos preexistentes em `xano/` diferem somente por LF/CRLF do último pull; eles não entram em commit e podem ser reescritos pelo pull. Antes de executar `xano workspace pull -d ./xano`, o Copilot MUST parar e pedir confirmação explícita ao usuário; só prosseguir após confirmação, registrando o resultado.
- [x] 1.2 Consultar no Xano Developer MCP a sintaxe de consultas relacionadas, ordenação, composição de URLs de imagem e respostas/erros; implementar apenas o novo `GET /catalog/donations/detail` com `donation_id`, sem alterar tabelas ou endpoints existentes, e validar todos os `.xs` novos no MCP.
- [x] 1.3 (manual) Executar `xano workspace push -d ./xano --dry-run`, mostrar a saída inteira ao usuário, revisar e registrar o escopo; avisar o grupo e obter sua autorização para o push real. Não marcar esta tarefa concluída pelo Copilot.
- [x] 1.4 (manual) Após autorização do grupo, parar e pedir confirmação explícita ao usuário imediatamente antes do push real; somente após confirmação publicar exclusivamente o endpoint novo. Não marcar esta tarefa concluída pelo Copilot.
- [x] 1.5 (manual) Após a publicação, conferir no painel do Xano e na rota pública a resposta do endpoint: doação disponível retorna fotos sem repetição e dados aprovados; doação inexistente ou indisponível retorna o mesmo resultado genérico; nenhum dado privado é retornado. Se aparecer qualquer dado privado, remover o endpoint novo imediatamente como rollback. Não marcar esta tarefa concluída pelo Copilot.

## 2. Página Reflex e navegação da home

- [x] 2.1 Implementar e testar com `unittest` o cliente/validador da resposta do detalhe: aceitar somente campos públicos esperados, montar a URL usando `XANO_API_URL`, preservar a ordem das fotos, deduplicar quando a capa for igual à primeira foto adicional e rejeitar respostas malformadas sem armazenar nem exibir campos privados; testar IDs não inteiros positivos e confirmar que não disparam chamada ao Xano.
- [x] 2.2 Implementar a página dinâmica `/doacao/[id]` com galeria, título, condição, descrição, categoria, cidade/UF, entrega, preferência de contato em texto e cartão mínimo de quem doa; incluir imagem genérica quando não houver fotos e testar a renderização dos elementos aprovados e a ausência dos elementos fora do escopo.
- [x] 2.3 Implementar e testar os estados de carregamento, doação não encontrada para status HTTP 404 e falha de rede/resposta inválida; testar `/doacao/abc`, `/doacao/0` e `/doacao/-1` sem chamada ao Xano e `/doacao/999999` com consulta e mensagem “Doação não encontrada”; validar também `page-fade-enter` e `prefers-reduced-motion`, sem animar cabeçalho nem dados carregados.
- [x] 2.4 Alterar e testar o botão “Acessar” da home para abrir `/doacao/<id>` da doação correspondente, mantendo os demais elementos e comportamentos dos cartões.
- [x] 2.5 Atualizar `docs/design/README.md` com a descrição da tela única, distinguir 14 como página inteira e 15 como topo, e registrar explicitamente os elementos ocultos e os motivos; revisar o diff para confirmar que a edição ficou restrita à nova seção.

## 3. Verificação integrada

- [x] 3.1 Executar `python -m unittest discover -s tests -v` e confirmar aprovação dos testes existentes e novos de detalhe e navegação.
- [x] 3.2 Executar `.venv\Scripts\reflex.exe compile --dry` e corrigir qualquer erro de registro da rota dinâmica ou da página.
- [x] 3.3 Conferir `git status --short` e `git diff --stat`; confirmar que só os arquivos previstos da change foram alterados e que as alterações preexistentes de `xano/` foram preservadas.

## 4. Teste manual após publicação

- [x] 4.1 (manual) Depois da publicação do endpoint, abrir no navegador uma doação disponível real por `/doacao/<id>` e conferir o detalhe, galeria sem foto repetida, dados do doador limitados ao primeiro nome e cidade/UF, responsividade e estados de erro; também acessar `/doacao/abc` e `/doacao/999999` e conferir “Doação não encontrada”. O Copilot não marca esta tarefa como concluída.
