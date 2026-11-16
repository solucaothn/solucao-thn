# Design

## Context

O motivo está no `proposal.md`. As referências são os quadros do Figma `479:2738`, `621:2530`, `621:2648` e `621:2752` (Central de ajuda), `406:1243` (Segurança), `399:1608` e `400:1674` (Termos), `396:1040` e `390:926` (Privacidade) e `354:851` (Sobre nós), salvos em `docs/design/19-duvidas-01.png` a `19-duvidas-04.png`, `20-seguranca.png`, `21-termos.png`, `22-privacidade.png` e `23-quem-somos.png`. Nenhum tem marca d'água; as fotos de Segurança e Sobre nós são de banco de imagens e não vão para o site.

**O que o Figma traz:**
- **Cabeçalho das páginas:** só o logotipo centralizado e o “Voltar ao inicio” abaixo, à esquerda. No “Sobre nós”, o “Voltar” fica dentro do cabeçalho.
- **Central de ajuda:**
  - busca “Buscar por uma dúvida”;
  - atalhos “Tem taxa?”, “Quem paga a entrega” e “O que não pode doar”;
  - 6 cartões de categoria (Primeiros passos 4, Doar um item 6, Receber uma doação 5, Conta e perfil 4, Segurança 5, Conversas 3, num total de 27);
  - “Mais perguntadas” em acordeão;
  - a caixa “Não encontrou o que procurava?” com “Fale com a gente”.
  - O componente “Pergunta” diz: “Fechado mostra só a pergunta; Aberto mostra a resposta e o voto de utilidade. Abrir um item fecha os outros; a linha inteira é clicável.” As perguntas fechadas **não têm resposta** no componente. Só há duas respostas no Figma: “O DoaFácil cobra alguma taxa?” e “Como publico uma doação?”.
- **Os textos de Termos e Privacidade** são de uma plataforma de doações em dinheiro (Pix, cartão, Banco Central, saques, KYC, CPF, telefone, endereço, empresa e CNPJ fictícios, foro de Osasco, e-mails inexistentes).
- **Segurança e Sobre nós** têm frases falsas para o projeto (decisão 9).

**Código atual:**
- `doafacil/doafacil.py` tem o rodapé (`public_home_footer`), `FOOTER_LINK_GROUPS` e `FUTURE_ROUTES` (`como_funciona`, `quem_somos`, `contato`, `privacidade`, `termos`, `duvidas` e `seguranca`);
- `doafacil/cabecalho.py` tem o menu da conta e os controles de sessão;
- `doafacil/chat.py` tem o `chat_fab()` e o `CHAT_FAB_CLEARANCE`;
- não existe e-mail de contato do projeto em lugar nenhum do código nem dos docs.

**O que o site realmente trata**, a base dos textos novos (`docs/guia-do-colaborador.md` e as specs `user-account`, `donation-*` e `event-logging`):
- conta: nome, e-mail (confirmado por código de 6 dígitos), senha (hash no Xano), cidade e UF, foto de perfil e “Sobre”;
- doações: título, descrição, categoria, condição, até 5 fotos sem metadados, cidade e UF do perfil, preferência de contato e status;
- chat: mensagens entre quem doa e quem tem interesse;
- registros de eventos: só `user_id`, ação e data;
- é público: o primeiro nome, a foto, a cidade e UF, o “Sobre” e as doações disponíveis (o detalhe das reservadas e concluídas dá 404). O e-mail só aparece para quem tem login, numa doação com contato “E-mail”;
- o envio de código usa o SendGrid, e os dados ficam no Xano;
- não há dinheiro, CPF, telefone nem endereço.

## Goals / Non-Goals

**Goals:**
- As 7 rotas no ar, com o layout do Figma e conteúdo verdadeiro.
- A Central de ajuda pesquisável e acessível, só no frontend.
- O rodapé e o cabeçalho reaproveitados, sem import circular.

**Non-Goals:**
- O e-mail de contato, que é pendência do grupo.
- Um formulário de contato.
- O voto “Esta resposta ajudou?”.
- Uma página “Como funciona” própria.
- A exclusão de conta pelo site.
- Textos jurídicos revisados por um profissional: os textos são de um projeto acadêmico, e o grupo os revisa.

## Decisions

### 1. Módulos

- **`doafacil/rodape.py` (novo):**
  - `public_home_footer()`, `FOOTER_LINK_GROUPS`, `_footer_link` e `FOOTER_FOCUS_RING`, movidos de `doafacil.py` sem mudança visual;
  - `INSTITUTIONAL_ROUTES`: `/duvidas`, `/seguranca`, `/termos`, `/privacidade`, `/quem-somos` e `/contato`, no lugar do `FUTURE_ROUTES`;
  - `CONTACT_ROUTE = "/contato"` e `CONTACT_EMAIL = ""`.
  - `doafacil.py` importa daqui, e os testes que usam `FUTURE_ROUTES` passam a usar `INSTITUTIONAL_ROUTES`.
- **`doafacil/cabecalho.py`:** acrescenta `logo_header()`, o cabeçalho branco com o logotipo centralizado (link para `/`, 190 px no computador e 100 px no celular, como na home).
- **`doafacil/institucional.py` (novo):**
  - o conteúdo em estruturas Python: `HELP_CATEGORIES`, cada uma com `slug`, `name`, `summary` e `questions`, com perguntas e respostas; `MOST_ASKED`; e os blocos de Segurança, Termos, Privacidade e Sobre nós;
  - `institutional_shell(content)`: cabeçalho, “Voltar ao início”, conteúdo com `page-fade-enter`, rodapé, `chat_fab()` e o espaço do botão;
  - as 7 páginas e o `HelpState`.

### 2. Central de ajuda e acordeão

- **Acordeão:** um `rx.accordion.root(type="single", collapsible=True)` com um `rx.accordion.item` por pergunta. O Radix já entrega o que o componente do Figma pede: o cabeçalho é um botão, com Enter e Espaço, `aria-expanded`, e abrir um fecha o outro. O visual segue o Figma: cartão branco, borda `#D9D9D9`, divisórias, item aberto em `#F3F4F6`, chevron, pergunta em Bold 16 px `#2A2A2A` e resposta em `#555555`.
- **Busca (`HelpState`):**
  - `query`, atualizado no `on_change` do campo com debounce;
  - `results`, uma variável calculada que filtra todas as perguntas, comparando sem acento e em minúsculas (com `unicodedata`) na pergunta e na resposta;
  - com `query` vazio, a página mostra as categorias e as “Mais perguntadas”; com texto, “N resultados para “x”” e o acordeão dos resultados, ou o estado vazio;
  - os atalhos são botões que preenchem a busca.
- **Página da categoria:** `/duvidas/[categoria]`, com o `HelpCategoryState.load` lendo `self.router.url.path`, o último segmento. Mostra o nome, “N perguntas sobre …”, o acordeão e “Voltar para dúvidas frequentes”. Um slug desconhecido mostra “Categoria não encontrada” e o link de volta.
- **Quantidades:** os cartões mostram `len(questions)`, nunca um número fixo, e um teste confere que o total bate.
- **Conteúdo:** as perguntas do Figma ficam na categoria certa. As que faltam (para chegar perto das 27) e as respostas não desenhadas são escritas a partir dos fatos do Contexto. A tarefa de revisão do grupo vem antes do merge.

### 3. Contato

- **`CONTACT_EMAIL = ""`.** Com ele vazio:
  - “Fale com a gente” (Central de ajuda) e “Clique aqui para falar conosco” (rodapé) levam a `/contato`;
  - a página `/contato` (título “Fale com a gente”) diz que o canal de contato do projeto ainda vai ser publicado e aponta para a Central de ajuda e para a Privacidade.
- **Com o e-mail preenchido:** os mesmos lugares mostram `mailto:<e-mail>`.
- O rodapé já aponta para `/contato`, e não muda.

### 4. Segurança

- **Layout do Figma:**
  - etiqueta, título e texto à esquerda, e a imagem à direita (placeholder em degradê, com a mesma regra `image: None` / foto própria da landing);
  - abaixo, o painel cinza com os 4 benefícios em 2 × 2 (ícone em círculo verde `#168447`, título em Bold e texto em 13 px) e, ao lado, os 2 cartões brancos de validação;
  - em telas estreitas, tudo vira uma coluna.
- **Textos:** os do Figma, trocando só o que é falso (decisão 9).

### 5. Termos e Privacidade

- **Layout do Figma:** um bloco de texto corrido com título (Bold) e seções. Na implementação, um `<h1>` e seções com `<h2>` numerados (“1. Sobre o DoaFácil”…), largura de leitura de até 860 px, 16 px e altura de linha 1.6.
- **A Privacidade** mantém a tabela do Figma, em `rx.table`, com as colunas Dado, Para que usamos, Onde fica e Quem vê, e as linhas dos dados do Contexto. Em telas estreitas, a tabela rola dentro do contêiner, nunca a página.
- **Rascunho das seções dos Termos:**
  1. Sobre o DoaFácil (projeto acadêmico, doação de objetos, sem dinheiro);
  2. Cadastro e conta (nome, e-mail confirmado por código, cidade e UF; uma conta por pessoa; manter a senha em sigilo);
  3. Publicação de doações (objetos próprios, fotos e descrição verdadeiras, até 5 fotos, categorias permitidas, sem itens proibidos);
  4. Combinação e entrega (direto entre as pessoas; o DoaFácil não intermedeia nem garante a entrega);
  5. Conversas e conduta (respeito, sem dados sensíveis no chat);
  6. Responsabilidades e limites;
  7. Alterações e contato (pendência).
- **Rascunho das seções da Privacidade:**
  1. Quem somos;
  2. Dados que tratamos (a tabela);
  3. Para que usamos;
  4. O que é público;
  5. Com quem compartilhamos (Xano para guardar os dados, SendGrid para o e-mail do código e Google Fonts, que recebe o IP do navegador ao carregar a fonte; ninguém mais);
  6. Por quanto tempo guardamos (a doação apagada leva as conversas, mas o `donations_DELETE` não apaga os arquivos das fotos no Xano);
  7. Seus direitos (LGPD), com o pedido pelo canal de contato (pendência);
  8. Segurança (senha com hash, código com validade, fotos sem metadados);
  9. Alterações.
- **Ligação:** os Termos linkam a Privacidade, e vice-versa.
- **Aviso:** logo abaixo do título de cada uma, a linha visível “Documento de projeto acadêmico, sem valor jurídico.” (decisão do Higor).
- **Revisão:** os textos novos são revisados pelo Higor antes do merge (tarefa 4.3).

### 6. Quem somos

- **Layout do Figma:**
  - a frase de missão em Bold de cerca de 56 px (responsiva, `clamp`), com o traço oval verde em volta de “doar” (um `rx.el.span` com borda arredondada em `#168447`, decorativo);
  - à direita, a imagem (placeholder) e o bloco verde decorativo;
  - abaixo, os 3 blocos verdes em escada e a seção “COMO FOI” / “O início do DoaFácil”;
  - em 360 px, uma coluna, e os blocos decorativos escondidos (`aria-hidden`).
- **Texto:** “O início do DoaFácil” passa a contar o projeto acadêmico (decisão 9).

### 7. “Como funciona”

- O item do menu passa a ser um link para `/#como-funciona`.
- A seção institucional da home (“Doar no DoaFácil é simples e seguro”) ganha `id="como-funciona"`.
- Não há página nova: é a solução mais simples, e o conteúdo da seção (Solidariedade, Segurança, Nossa missão e Passo a passo) é o “como funciona” do site.

### 8. Testes

- **`tests/test_institucional.py`:**
  - cada rota registrada, com o `on_load` do chat;
  - o cabeçalho, “Voltar ao início”, o rodapé e o botão do chat em cada página;
  - um único `h1` e nenhum salto de nível;
  - o acordeão (tipo `single`, recolhível);
  - a busca (sem acento e em minúsculas, os atalhos, o vazio e a contagem);
  - as quantidades iguais ao número de perguntas;
  - o slug desconhecido;
  - o contato com e sem e-mail;
  - a ausência das palavras proibidas (Pix, cartão de crédito, CPF, CNPJ, `doafacil.com.br`, 2019, Osasco) em todo o conteúdo;
  - a tabela da Privacidade com os dados reais;
  - nenhuma largura fixa maior que 360 px.
- **Ajustes:**
  - `tests/test_public_home.py`: o “Como funciona” vira âncora, e o `FUTURE_ROUTES` sai;
  - `tests/test_chat.py`: o botão nas páginas institucionais.

### 9. Diferenças em relação ao Figma

| Tela | No Figma | Na implementação | Motivo |
|---|---|---|---|
| Termos | vaquinha em dinheiro: Pix, cartão, BCB, saques, CPF, telefone, endereço, CNPJ, foro, URLs | textos novos para a doação de objetos, num projeto acadêmico | o domínio não é financeiro; nada de empresa ou dado inventado |
| Privacidade | o mesmo, com o e-mail `lgpd@doafacil.com.br`, cookies e geolocalização | textos novos e a tabela com os dados reais | idem; o site não coleta geolocalização nem usa analytics |
| Central de ajuda | `contato@doafacil.com.br` | “Fale com a gente” → `/contato` (pendência) | o e-mail não existe |
| Central de ajuda | “Esta resposta ajudou? Sim / Não” | removido | sem onde guardar o voto (fora do escopo) |
| Central de ajuda | só 2 respostas e 2 listas de perguntas | as perguntas e respostas que faltam, escritas a partir do site | o conteúdo não existe no Figma |
| Central de ajuda | “Nenhuma resposta para “boleto”” com o texto sobre boletos | o texto genérico: “Tente outra palavra ou escolha uma categoria.” | a frase sobre boleto só vale para essa palavra |
| Segurança | “Criptografamos todas as informações… transações” | “A senha é guardada com hash, o e-mail é confirmado por código e as fotos saem sem metadados.” | não há criptografia de tudo nem transações |
| Segurança | “após sua conta ser verificada e o email e CPF’s validados” | “a doação aparece em Explorar assim que é publicada”, com o que dá para fazer em Minhas doações | não há CPF nem validação manual, e o `publish_POST` não confere o `email_verified` |
| Segurança | “Nosso trabalho de validação… item doado está correto” | a combinação é feita entre as pessoas, com dicas de segurança | o site não valida itens |
| Segurança | “SAIBA MAIS SOIBRE NOSSA” | “SAIBA MAIS SOBRE NOSSA” | erro de digitação |
| Sobre nós | “A ideia nasceu em 2019… Hoje, já são milhares de doações…” | o projeto acadêmico do grupo, sem data inventada nem números | não é verdade |
| Segurança, Sobre nós | fotos de banco de imagens | placeholder em degradê | direitos de imagem, como na landing |
| todas | “Voltar ao inicio” | “Voltar ao início” | acento |
| todas | cabeçalho só com o logotipo | o mesmo (`logo_header`), mais o rodapé da home em todas | navegação consistente |

### 10. Tema claro fixo em todo o app (decisão do Higor, roteiro 5.4)

- **Problema:** o app não fixava o tema, e o Radix seguia o modo escuro do sistema. No roteiro, o item aberto do acordeão virou uma faixa preta, a tabela da Privacidade ficou com texto claro sobre fundo claro e o “Voltar ao início” da `/explorar` ficou azul.
- **Decisão:** `rx.plugins.RadixThemesPlugin(theme=rx.theme(appearance="light", accent_color="blue"))` no `rxconfig.py`. Na 0.9.12, o `theme` do `rx.App` é um atalho legado; o plugin é o lugar atual. O acento azul é o padrão do Reflex, então nada além do modo de cor muda.
- **Efeito:** o Reflex compila o modo padrão como `light` e, na primeira visita depois do deploy, troca o modo salvo no navegador. O site inteiro fica claro, como no Figma, em qualquer sistema.
- **Cores fixas mantidas:** o acordeão, a busca e a tabela da Privacidade continuam com as cores explícitas da seção 6 do `tasks.md`, uma segunda proteção caso o tema mude.
- **Alternativa descartada:** um modo escuro de verdade. Não existe desenho para ele, e seria uma change própria.

## Risks / Trade-offs

- **[Textos novos com afirmações imprecisas]** → cada frase sai do Contexto (o que o site faz), e há uma tarefa de revisão do grupo antes do merge. O teste das palavras proibidas pega as regressões mais óbvias.
- **[Textos jurídicos amadores]** → declarado como projeto acadêmico. Nenhuma promessa além do que o site faz.
- **[Mover o rodapé quebrar a home]** → mudança só de lugar. Os testes do rodapé continuam valendo e passam a importar de `rodape.py`.
- **[Busca por caractere enviando eventos demais]** → `debounce_timeout` no campo.
- **[Rota dinâmica `/duvidas/[categoria]` conflitar com `/duvidas`]** → o Reflex trata as duas como rotas distintas. Confere no `reflex compile` e no teste de registro.

## Migration Plan

1. `rodape.py` e `logo_header()`, sem mudança visual (com os testes da home).
2. A Central de ajuda e as categorias, Segurança, Quem somos e Contato.
3. Termos e Privacidade (rascunhos) e a revisão do grupo.
4. Docs, os testes e o roteiro em 1512 px e 360 px.
5. **Rollback:** reverter pelo `git`. Não há dados nem Xano envolvidos.
