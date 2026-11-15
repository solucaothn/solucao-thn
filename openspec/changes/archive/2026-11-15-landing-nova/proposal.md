# Proposal

## Why

O grupo aprovou uma nova landing no Figma (frame `655:2691`, referência em `docs/design/16-landing-nova.png`). A home atual já tem as mesmas seções, mas ainda é quase toda “de vitrine”: o menu, a busca, os cartões e o rodapé não levam a lugar nenhum, falta a estatística “Pessoas alcançadas”, e a seção institucional ainda usa os textos antigos. Esta change alinha a home ao Figma e liga a navegação, preparando a tela de Explorar doações da próxima change.

## What Changes

Comparação seção por seção entre o Figma e a home atual (`doafacil/doafacil.py`):

| Seção | Já existe igual | Muda | Novo |
|---|---|---|---|
| **Cabeçalho** | logo, “Explorar Doações”, “Como funciona”, “Categorias”, “Quero Doar”, “Entrar” sem sessão | os três itens do menu viram links; com sessão, “Minhas doações” + “Olá, nome” + “Sair” dão lugar ao **menu da conta** (inicial + primeiro nome + seta) | menu da conta com “Minhas doações”, “Editar perfil” e “Sair” |
| **Título** | “Doar é fácil. No DoaFácil, o que sobra em você vira recomeço para alguém.” | tamanho e largura (uma linha mais larga no computador) | — |
| **Números** | “Doações em circulação” com a contagem real (`catalog/donations/count`) | o rótulo ganha “!” e o número fica menor, em verde escuro, à esquerda | **“Pessoas alcançadas”**, com o número de doações concluídas. Precisa de Xano: o `catalog/donations/count` passa a devolver também `completed` |
| **Doações mais recentes** | cartões com foto, NOVO, título, condição e “Acessar” (até 4, em carrossel) | o título ganha “:”; o cartão continua mostrando “Condição” (o Figma diz “Estado”, mas o termo do domínio é condição) | link **“Ver mais...”** para `/explorar` |
| **Faixa de ilustração e chat** | a ilustração em largura total e o botão flutuante do chat | — | — |
| **“Quer criar uma doação?”** | etiqueta, título, frase e os três cartões com os mesmos textos | “Para você mesmo” leva a `/explorar` e “Ajude quem precisa” leva a `/cadastro-doacao`; “Desapego em grupo” continua “Em breve”; a etiqueta segue em verde legível (no Figma ela está quase invisível) | — |
| **Barra de busca** | os campos, os rótulos e o botão “Buscar” | passa a funcionar: as categorias vêm do Xano (`catalog/categories`) e a localização lista as 27 UFs; “Buscar” leva a `/explorar?q=…&categoria=…&uf=…` | página **provisória** `/explorar`, que mostra os filtros recebidos até a tela de verdade chegar na próxima change |
| **“Doar no DoaFácil é simples e seguro”** | título, texto de apoio e as categorias dos 4 cartões | os títulos passam a “Histórias que continuam”, “Você no controle”, “Nada se perde” e “Doar leva minutos”; os cartões ficam quadrados, com ícone em círculo verde e sem “Saiba mais”; o fundo passa a creme e o texto de apoio a verde | **placeholder** no lugar das fotos do Figma, que têm marca d'água “shutterstock”, até chegarem fotos próprias |
| **Rodapé** | logo, “Fale conosco”, “Links rápidos” e os 8 links | os links passam a navegar (rotas futuras abaixo); “Links rápidos” sem o erro de digitação do Figma (“Linkes”) | — |

- **Rotas que ainda não existem e ficam apontadas:** `/como-funciona`, `/categorias`, `/quem-somos`, `/contato`, `/privacidade`, `/termos`, `/duvidas` e `/seguranca`. Até serem criadas, mostram a página “não encontrada” do Reflex.
- **Rotas que já existem:** `/cadastro-doacao`, `/minhas-doacoes`, `/perfil/editar` e `/doacao/<id>`. “Doações mais recentes”, no rodapé, leva à âncora `/#doacoes-recentes`.
- **360 px:** nenhuma rolagem horizontal da página. O carrossel continua rolando só dentro dele.
- **Fora do escopo:**
  - a tela de Explorar doações de verdade e o filtro por UF no Xano (próxima change);
  - as páginas institucionais;
  - a foto de perfil no menu da conta, que exigiria mais uma requisição;
  - o cartão “Desapego em grupo”.

## Capabilities

### New Capabilities

- `donation-explore`: a página `/explorar`, por enquanto provisória, que recebe os filtros da busca da home.

### Modified Capabilities

- `public-home`: o menu do cabeçalho com links, o menu da conta, a estatística “Pessoas alcançadas” (que a spec atual proíbe) e o link “Ver mais...”.
- `public-home-content`: os cartões de “Comece por aqui” e a barra de busca passam a navegar; a seção institucional ganha os textos e o placeholder novos; o rodapé ganha os links; e o layout fica sem rolagem horizontal em 360 px.
- `public-donation-discovery`: a contagem pública passa a incluir as doações concluídas.
- `user-account`: o cabeçalho autenticado da home mostra o primeiro nome e o “Sair” dentro do menu da conta, e não mais “Olá, nome” e o botão “Sair”.
- `donation-management`: “Minhas doações” passa a ser item do menu da conta, e não mais um link ao lado de “Olá, nome”.
- `donation-chat-interface`: o cabeçalho logado descrito na entrada do chat passa a ser o novo, e a página provisória `/explorar` entra na lista de páginas sem o botão flutuante.

## Impact

- **Frontend:** `doafacil/doafacil.py` (a home, o `HomeState` e a rota `/explorar`), um módulo novo para a página provisória e `tests/test_public_home.py`.
- **Xano:** só o `catalog/donations/count` (um campo a mais na resposta, compatível com o que o site já lê). O push leva só esse arquivo, com `-i` e dry-run antes.
- **Documentação:** `docs/design/README.md` (as diferenças aprovadas em relação ao Figma) e `docs/guia-do-colaborador.md`. O PNG de referência já está em `docs/design/16-landing-nova.png`.
