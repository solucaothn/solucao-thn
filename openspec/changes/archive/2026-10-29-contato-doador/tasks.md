# Tasks

## 1. Preparação e contrato

- [x] 1.1 Revisar as specs de `donation-detail` e `donation-creation` e confirmar que o delta mantém somente “Conteúdo do detalhe da doação” em `MODIFIED`, inclui os novos requisitos em `ADDED`, preserva os cenários vigentes, cobre o aviso no cadastro e não duplica o requisito de privacidade da resposta pública. Verificar com `openspec validate contato-doador --type change --strict`.
- [x] 1.2 Registrar a decisão de endpoint e a rota escolhida (`GET /catalog/donations/contact-email`) e confirmar que ela não conflita com `recent`, `count`, `status`, `detail` e `publish`, com verificação no código ou na documentação do grupo de API. Verificar no projeto que não existe rota com esse caminho.
- [x] 1.3 Definir e documentar o comportamento de quem doa ao clicar na própria doação: como o frontend não recebe `owner_id`, chama o endpoint quando a preferência é “E-mail” e traduz o HTTP 403 para “Esta é a sua doação.”. Verificar por revisão do design e do cenário na spec.

## 2. Implementação no frontend (Reflex)

- [x] 2.1 Ajustar o topo do cartão da página `/doacao/<id>` para apresentar `Outros meios de comunicação` e `Chat` conforme o Figma, preservando o conteúdo já definido e sem mostrar perfil do doador, perfil público, avaliações, histórico, online, verificação ou “Em breve”. Verificar visualmente no navegador e por revisão da renderização do componente.
- [x] 2.2 Implementar o fluxo do botão “Outros meios de comunicação”: sem login redireciona para `/login`; pessoa autenticada com `contact_preference == "E-mail"` chama o endpoint com o token e abre `mailto:` com e-mail codificado e assunto simples quando recebe HTTP 200; resposta HTTP 403 é traduzida para “Esta é a sua doação.”; preferência `Chat do DoaFácil` mostra “Quem doa prefere contato pelo chat.” sem chamar o endpoint; falha de rede ou respostas 401/404 exibem erro simples no estilo do site. Verificar com `unittest` para os cenários do fluxo.
- [x] 2.3 Implementar o botão “Chat” para exibir a mensagem “O chat ainda não está disponível.” e não navegar. Verificar com teste unitário e inspeção manual da tela.
- [x] 2.4 Garantir que o e-mail não permaneça no estado após o redirecionamento, que o frontend nunca receba nem guarde `owner_id` e que a resposta pública do detalhe continue sem e-mail, usando `contact_preference` do payload público. Verificar com testes unitários e os testes existentes do contrato público sem alteração.

## 3. Implementação no Xano / Catalog

- [x] 3.1 (manual) Conferir o `git status` e as diferenças dos arquivos de `xano/` já modificados; registrar que contêm somente diferenças de quebra de linha ou mudanças do painel e que nunca entram em commit. O Copilot MUST parar e pedir confirmação explícita do usuário antes de executar `xano workspace pull -d ./xano`; verificar que o pull só ocorre depois dessa confirmação. O Copilot não marca esta tarefa como concluída.
- [x] 3.2 Consultar o Xano Developer MCP para confirmar a sintaxe de autenticação, os erros HTTP 401, 403 e 404 e a função de log; escrever somente o endpoint novo `GET /catalog/donations/contact-email`, sem alterar tabelas nem endpoints existentes. Registrar cada chamada por `xano/function/quick_start/log_event.xs` usando somente `user_id`, ação e data, sem e-mail, nome, título ou token. Validar o arquivo `.xs` no MCP e verificar que o diff contém apenas o endpoint novo.
- [x] 3.3 (manual) Executar `xano workspace push -d ./xano --dry-run`, mostrar a saída completa, avisar o grupo e obter autorização antes de qualquer push real. Verificar que a saída integral foi apresentada e que a autorização do grupo foi obtida. O Copilot não marca esta tarefa como concluída.
- [x] 3.4 (manual) Solicitar confirmação explícita do usuário imediatamente antes do push real e, após recebê-la, publicar somente o endpoint novo. Verificar no resultado do push que nenhum outro endpoint ou tabela foi enviado. O Copilot não marca esta tarefa como concluída.
- [x] 3.5 (manual) Depois do push, conferir no painel e na rota que sem login retorna 401; pessoa autenticada com preferência “E-mail” recebe somente o e-mail; a pessoa dona recebe 403 sem e-mail; doação com preferência “Chat do DoaFácil” ou inexistente retorna 404; e o evento de log foi registrado sem e-mail. Se aparecer qualquer dado extra, remover o endpoint novo imediatamente. Registrar os resultados das conferências; o Copilot não marca esta tarefa como concluída.

## 4. Cadastro de doação

- [x] 4.1 Ajustar a quinta etapa do cadastro para mostrar o aviso “Seu e-mail ficará disponível para pessoas logadas que quiserem falar com você.” quando a preferência escolhida for “E-mail”. Verificar visualmente no fluxo de cadastro e em testes unitários do formulário.
- [x] 4.2 Confirmar que o restante do cadastro e as opções de contato continuam restritas a “E-mail” e “Chat do DoaFácil”, sem qualquer outro dado pessoal solicitado. Verificar por inspeção do formulário e testes de renderização.

## 5. Testes e validação

- [x] 5.1 Escrever testes `unittest` do frontend usando `httpx.MockTransport` com respostas simuladas HTTP 200, 401, 403, 404 e falha de rede para verificar: sem login redireciona a `/login` sem chamar o endpoint; pessoa autenticada com preferência `E-mail` chama o endpoint com o token; resposta 403 é traduzida para “Esta é a sua doação.”; resposta 200 abre `mailto:`; preferência `Chat` mostra a mensagem sem chamar o endpoint; e-mail e `owner_id` não permanecem no estado nem são recebidos pelo frontend; resposta pública do detalhe continua sem e-mail. Verificar com a execução dos testes focados e deixar explícito que respostas simuladas não comprovam o contrato real do endpoint Xano.
- [x] 5.2 Executar `openspec validate contato-doador --type change --strict` e corrigir qualquer divergência entre artefatos e requisitos. Verificar a saída final do comando.
- [x] 5.3 (manual) Testar no navegador depois do push: pessoa logada com preferência “E-mail” abre o e-mail de quem doa; pessoa sem login vai para `/login`; no cartão da própria doação aparece “Esta é a sua doação.”; com preferência “Chat do DoaFácil” aparece “Quem doa prefere contato pelo chat.”; o botão “Chat” mostra “O chat ainda não está disponível.”; e o aviso do cadastro aparece ao escolher “E-mail”. O Copilot não marca esta tarefa como concluída.
