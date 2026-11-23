# Proposta

## Por quê

A auditoria antes da entrega de 24/11 achou pontos que atrapalham a demonstração. O site estreia sem doações, e a Explorar vazia não leva a lugar nenhum. Algumas falhas não oferecem “Tentar de novo”. Com algumas abas de chat abertas, o limite do Xano (10 pedidos a cada 20 s para o site inteiro) estoura. Além disso, a categoria “Alimentos” foi apagada do Xano, e “Móveis” precisa voltar a ser oferecida.

## O que muda

- **Categorias:** “Móveis” passa a aparecer no cadastro, na edição, na gaveta, em `/categorias` e nos filtros da busca, com um ícone de sofá. Saem as exclusões por nome (“Alimentos” e “Móveis”). Uma categoria que não existe mais continua tratada como hoje: some da lista, e uma doação com ela pede outra na edição.
- **Perfil de quem doa:** o link “Explorar outras doações” do estado vazio passa a levar a `/explorar`, e não à home.
- **Explorar vazia, sem filtros:** a página mostra uma frase convidando a doar e o botão “Quero Doar”. Ele leva a `/cadastro-doacao` ou, sem sessão, a `/login?next=/cadastro-doacao`. Com filtros, continua o “Limpar filtros”.
- **“Tentar de novo”:** o botão, com 44 px de área de toque, aparece nas falhas da home (contagem e recentes), de Minhas doações e do perfil de quem doa.
- **Chat:**
  - as mensagens da conversa aberta são consultadas a cada 25 s, e não mais 15;
  - com uma conversa aberta, a lista de conversas não se atualiza sozinha. Ela se atualiza ao voltar para a lista ou pelo botão de atualizar.
- **Perfil de quem doa no cache público:** a resposta do perfil fica guardada por 60 s, como o detalhe. O cache é descartado junto com os outros quando a pessoa publica, edita, muda o status ou apaga uma doação, e também quando ela edita o perfil.
- **Publicação no Xano:** o `catalog/donations/publish` passa a recusar:
  - título com mais de 100 caracteres e descrição com mais de 2000;
  - entrega diferente de “A combinar”;
  - preferência de contato diferente de “E-mail” e “Chat do DoaFácil”.
  
  São os mesmos limites e valores da edição.
- **Sem mudança de comportamento:**
  - o `.gitignore` passa a incluir `.env` e `.claude/settings.local.json`;
  - a Central de ajuda corrige o texto sobre a entrega na edição;
  - dois testes deixam de usar construções que serão removidas (escape inválido e `Image.getdata`);
  - o log `[xano]` continua desligado por padrão.

## Capacidades

### Novas capacidades

Nenhuma.

### Capacidades modificadas

- `donation-creation`: a lista de categorias do cadastro deixa de excluir “Alimentos” e “Móveis”. O backend da publicação passa a validar o tamanho do título e da descrição e os valores de entrega e de contato.
- `donation-management`: a edição passa a oferecer todas as categorias do backend. Minhas doações ganha “Tentar de novo” na falha.
- `donation-categories`: a lista deixa de ter exclusões e passa a ter o ícone de “Móveis”.
- `donation-explore`: o estado vazio sem filtros ganha o convite e o botão “Quero Doar”.
- `donor-public-profile`: o link do estado vazio passa a levar a `/explorar`, e a falha ganha “Tentar de novo”.
- `public-home`: as falhas da contagem e das recentes ganham “Tentar de novo”.
- `donation-chat-interface`: as mensagens passam a ser consultadas a cada 25 s, e a lista não se atualiza sozinha com uma conversa aberta.
- `backend-request-budget`: o perfil de quem doa entra no cache público, e a edição do perfil também descarta o cache.

## Impacto

- **Reflex:**
  - `doafacil/cadastro_doacao.py`, `doafacil/explorar.py` e `doafacil/categorias.py` (categorias e ícones);
  - `doafacil/explorar.py` (estado vazio);
  - `doafacil/perfil_doador.py` (link, “Tentar de novo” e cache);
  - `doafacil/doafacil.py` (home);
  - `doafacil/minhas_doacoes.py` (“Tentar de novo”);
  - `doafacil/chat.py` (atualização automática);
  - `doafacil/cache_publico.py` (novo espaço do cache);
  - `doafacil/editar_perfil.py` (descartar o cache);
  - `doafacil/cabecalho.py` (botão “Tentar de novo” compartilhado);
  - `doafacil/institucional.py` (texto da Ajuda).
- **Xano:** só `xano/api/catalog/catalog/donations/publish_POST.xs`. O push fica com o Higor, depois do dry-run e do OK do grupo, porque o endpoint tem outros consumidores.
- **Outros:**
  - `.gitignore`;
  - testes em `tests/`;
  - o novo script `scripts/teste_publicar_limites_real.py`, que só envia uma entrada inválida e não cria doação;
  - `docs/guia-do-colaborador.md` e `docs/design/README.md`.
