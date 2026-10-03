AGENTS.md — DoaFácil
Instruções para agentes de IA que trabalham neste repositório. Este arquivo define como trabalhar. O que é o projeto está nos documentos de contexto.
Documentação
Antes de qualquer alteração significativa, leia:
`docs/project-overview.md` — o que é o projeto, escopo e restrições;
`docs/domain-model.md` — conceitos do domínio e relacionamentos;
`openspec/config.yaml` — contexto e regras dos workflows do OpenSpec.
Não presuma regras de negócio que não estejam nesses documentos ou nas specs. Quando algo estiver em aberto (veja "Pontos em aberto" em `docs/domain-model.md`), pergunte ao grupo em vez de decidir sozinho.
Desenvolvimento com OpenSpec
Toda mudança funcional deve ser especificada com OpenSpec antes de ser implementada.
Siga o ciclo: Explore → Propose → Review → Apply → Archive.
Não implemente código durante o Explore, e não crie uma cAhange sem pedido do grupo.
Trabalhe uma change por vez, pequena e verificável. Não tente construir o sistema inteiro de uma vez.
Não crie nem edite manualmente `openspec/specs/`. Elas são atualizadas pelo Archive.
Não altere nem remova os arquivos instalados pelo `openspec init` (workflows e comandos das ferramentas de IA) sem entender sua finalidade.
Se surgir uma decisão que contradiga o domínio, mude a arquitetura ou aumente muito o escopo, pare e proponha revisar a change.
Arquitetura
Frontend: Reflex (Python). Interface, páginas, navegação e formulários.
Backend: Xano. Usuários, autenticação, banco de dados, regras de negócio e APIs.
Respeite essas tecnologias. Não introduza alternativas sem justificativa explícita.
O frontend consome as APIs do Xano e não acessa o banco diretamente.
Segurança
Autorização e validação de dados devem ser aplicadas no backend (Xano). O frontend não é mecanismo de segurança.
Nunca coloque tokens, chaves de API ou senhas em arquivos versionados.
Não registre dados pessoais dos usuários em logs ou em exemplos de código.
Xano e XanoScript
A pasta `xano/` é a representação local do workspace do Xano e é sincronizada pelo Xano CLI.
Não presuma a sintaxe do XanoScript. Consulte e valide com o Xano Developer MCP antes de escrever ou alterar arquivos `.xs`.
O workspace do Xano é compartilhado. Antes de começar, rode `xano workspace pull -d ./xano`.
Antes de enviar alterações ao Xano, rode `xano workspace push -d ./xano --dry-run`, revise o resultado e só então faça o push.
Não use o Xano MCP Server para alterar o workspace diretamente. As alterações passam pelos arquivos, pelo Git e pelo Xano CLI.
Código
Reutilize o que já existe e evite duplicação.
Não modifique funcionalidades não relacionadas à change atual sem justificativa.
Mantenha as mudanças pequenas e fáceis de revisar.
Testes e verificação
Toda mudança funcional deve ter uma forma de verificação (teste automatizado ou roteiro de verificação manual descrito nas tasks).
Antes de dar uma tarefa por concluída, execute as verificações relevantes.
Git
Não faça commit nem push sem pedido do grupo.
Antes de propor um commit, mostre o `git diff` e descreva a alteração.
Trabalhe em branches, sem alterar a `main` diretamente.
Nunca use `git push --force` sem autorização explícita.
Idioma
Escreva documentação, artefatos do OpenSpec e comentários relevantes em português brasileiro. Nomes de variáveis e de arquivos de código seguem o padrão já usado no projeto.