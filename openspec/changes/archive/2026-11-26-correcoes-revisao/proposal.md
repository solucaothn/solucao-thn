# Proposta

## Por quê

A revisão de 26/11 achou falhas que a suíte de testes não pegava. No celular, a busca da Explorar e da `/categorias` some: o campo fica com 0 px e a página rola para o lado. No chat, apertar Enter duas vezes pode mandar a mesma mensagem duas vezes. Em várias telas, o “carregando” nunca aparece. Isso acontece ao publicar uma doação, ao entrar, ao criar conta, na recuperação de senha, ao atualizar o chat e nos botões de tentar de novo: a pessoa clica e nada muda até a resposta. Alguns textos também têm erro ou prometem o que o site não tem, como “Taxas, Prazos e Regulamentos”.

## O que muda

- **Busca do cabeçalho no celular:** em `/explorar` e `/categorias`, abaixo de 992 px, a busca passa a ocupar uma linha inteira, abaixo do logotipo. O campo fica com largura para digitar, e a página não rola para o lado em 360 px.
- **Chat:**
  - “Enviar” e “Salvar” (da edição) ficam desativados assim que a pessoa aciona o envio, e não só no fim. Uma segunda tecla Enter durante o envio não manda a mensagem de novo.
  - “Atualizar conversas”, “Carregar mais conversas” e “Carregar anteriores” mostram o carregamento desde o clique.
  - O botão da falha da lista passa a se chamar “Tentar de novo”.
- **Publicar doação:** desde o clique em “Publicar doação”, o botão mostra “Publicando...” desativado, junto com o aviso “Enviando sua doação...”. Hoje a tela fica parada durante o envio, que pode levar até 60 s.
- **Login, cadastro e recuperação de senha:** “Entrando...”, “Criando...” e os textos de carregamento da recuperação aparecem enquanto o pedido está em andamento.
- **Tentar de novo:**
  - no detalhe da doação, na `/categorias`, na gaveta de categorias da home e no cadastro de doação, o botão mostra o carregamento na hora;
  - todos os botões de tentar de novo passam a ter o mesmo texto, “Tentar de novo”. Hoje há “Tentar novamente” no detalhe e no chat, e “Tentar carregar novamente” no cadastro.
- **Textos:**
  - o cartão “Doei em uma doação”, da `/seguranca`, vira “Recebi uma doação”;
  - o aviso legal do cadastro de doação passa a citar só os Termos de uso, com link para `/termos` aberto em outra aba, para a pessoa não perder o que preencheu;
  - a dica da verificação de e-mail vira “Pode demorar um minutinho. Confira também a caixa de spam.”;
  - na `/seguranca`, o texto de apresentação passa a dizer “a segurança e a transparência”;
  - três textos ficam neutros quanto a gênero:
    - o cartão “Para você mesmo” vira “Para você”;
    - “Como prefere ser contatado?” vira “Como prefere que entrem em contato?”;
    - na Ajuda, “vá acompanhado” vira “vá com alguém”.

## Fora do escopo

- O HTTP 404 que o servidor de produção devolve em `/doacao/<id>` e `/doacao/<id>/quem-doa`. É o comportamento do Reflex para rotas com parâmetro, e a página aparece certa no navegador.
- O selo “Built with Reflex” do modo de produção.
- O Xano: nenhuma mudança em `xano/`, nenhum endpoint novo e nenhuma chamada a mais. As correções só mudam quando a tela é atualizada, não o que é pedido ao backend.
- As capturas de tela do README. A do passo 5 do cadastro continua com o título antigo até a próxima atualização das imagens.

## Capacidades

### Novas capacidades

Nenhuma.

### Capacidades modificadas

- `donation-explore`: a busca do cabeçalho fica utilizável em 360 px, na Explorar e na `/categorias`.
- `donation-chat-interface`: o envio e o salvar edição ficam bloqueados desde o acionamento, sem envio repetido. O carregamento das ações da lista e do histórico aparece desde o clique.
- `donation-creation`: o andamento da publicação aparece desde o clique, o tentar de novo do carregamento mostra o carregamento e o aviso legal muda.
- `user-account`: “Entrando...” e “Criando...” aparecem durante o pedido.
- `password-recovery`: os textos de carregamento aparecem durante o pedido, e a dica do spam muda.
- `donation-detail`: o botão da falha vira “Tentar de novo” e mostra o carregamento na hora.
- `donation-categories`: o “Tentar de novo” da lista mostra o carregamento na hora.
- `institutional-pages`: o cartão “Recebi uma doação” e o texto de apresentação da `/seguranca`.
- `public-home-content`: o cartão “Para você”.

## Impacto

- **Reflex:**
  - `doafacil/explorar.py` (cabeçalho);
  - `doafacil/chat.py` (envio, edição, atualizações e o texto do botão);
  - `doafacil/cadastro_doacao.py` (publicação, tentar de novo e textos);
  - `doafacil/login.py` (login, cadastro e recuperação);
  - `doafacil/detalhe_doacao.py` (tentar de novo);
  - `doafacil/categorias.py` e `doafacil/doafacil.py` (tentar de novo das categorias e o cartão “Para você”);
  - `doafacil/recuperacao_senha.py` (dica do spam);
  - `doafacil/institucional.py` (textos da `/seguranca` e da Ajuda).
- **Testes:** os de cada módulo em `tests/`. Os que conferem a lista exata de eventos emitidos passam a contar com o envio de estado antes do pedido.
- **Documentação:** `docs/design/README.md`, `docs/guia-do-colaborador.md` e `README.md`, onde citam os textos que mudam.
- **Xano:** nenhum.
