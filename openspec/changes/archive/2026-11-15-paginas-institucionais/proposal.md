# Proposal

## Why

O rodapé e o menu da home levam a cinco páginas que ainda dão “não encontrada” (Dúvidas, Segurança, Termos, Privacidade e Quem somos). O Figma tem essas telas, mas parte do texto não vale para o DoaFácil. Os Termos e a Privacidade foram copiados de uma plataforma de doações em dinheiro, e há datas, números, CPF e e-mails que não existem. É preciso publicá-las com o layout do Figma e textos verdadeiros.

## What Changes

- **Páginas novas, estáticas e sem Xano**, com as referências em `docs/design/19-*.png` a `23-*.png`:

  | Rota | Tela do Figma | Conteúdo |
  |---|---|---|
  | `/duvidas` | 479:2738, 621:2648, 621:2752 | “Central de ajuda”: busca nas perguntas, atalhos, 6 categorias, “Mais perguntadas” em acordeão, caixa “Não encontrou o que procurava?” |
  | `/duvidas/<categoria>` | 621:2530 | as perguntas de uma categoria, com “Voltar para dúvidas frequentes” |
  | `/seguranca` | 406:1243 | “Segurança e Transparência”, os 4 benefícios e os 2 cartões de validação |
  | `/termos` | 399:1608, 400:1674 | Termos de uso **reescritos** para o DoaFácil |
  | `/privacidade` | 396:1040, 390:926 | Política de privacidade **reescrita**, com a tabela dos dados que o site realmente trata |
  | `/quem-somos` | 354:851 | “Sobre nós”: a frase de missão e “O início do DoaFácil” |
  | `/contato` | (sem tela) | “Fale com a gente”: página curta enquanto o e-mail do projeto não existe |

- **“Como funciona”** (menu da home) passa a levar à seção institucional da home, “Doar no DoaFácil é simples e seguro”, pela âncora `/#como-funciona`, sem página nova.
- **Contato:** não há e-mail do projeto no código, e o do Figma (`contato@doafacil.com.br`) não existe. Uma constante `CONTACT_EMAIL` fica vazia:
  - “Fale com a gente” e “Clique aqui para falar conosco” levam a `/contato`, que avisa que o canal ainda vai ser publicado e aponta para a Central de ajuda;
  - quando o grupo definir o e-mail, basta preencher a constante, e os botões viram `mailto:`.
- **Conteúdo verdadeiro:**
  - os Termos e a Privacidade são rascunhos novos, que o grupo revisa antes do merge;
  - nas outras telas, só as frases falsas trocam;
  - as perguntas que faltam na Central de ajuda são escritas com base no que o site faz hoje, também para revisão;
  - as fotos de banco de imagens viram placeholder em degradê.
- **Estrutura comum:**
  - o cabeçalho do Figma (o logotipo centralizado) vem de `cabecalho.py`;
  - o rodapé da home sai de `doafacil.py` para `rodape.py` e passa a aparecer em todas as páginas;
  - todas têm “Voltar ao início”, o botão flutuante do chat, a animação de entrada, títulos em ordem e nenhuma rolagem horizontal em 360 px.
- **As rotas futuras acabam:** `/duvidas`, `/seguranca`, `/termos`, `/privacidade`, `/quem-somos` e `/contato` passam a existir, e o `FUTURE_ROUTES` deixa de ser necessário.

Diferenças em relação ao Figma, detalhadas na decisão 9 do `design.md`:

| No Figma | Na implementação |
|---|---|
| Termos e Privacidade de vaquinha em dinheiro (Pix, cartão, Banco Central, CPF, CNPJ e foro fictícios) | textos novos para a doação de objetos, num projeto acadêmico |
| `contato@doafacil.com.br` e `lgpd@doafacil.com.br` | pendência: página `/contato` e a constante `CONTACT_EMAIL` vazia |
| “A ideia nasceu em 2019… milhares de doações” | o projeto acadêmico, sem números inventados |
| “Criptografamos todas as informações”; “e-mail e CPF validados” | o que o site faz: senha com hash, e-mail confirmado por código, sem CPF |
| fotos de banco de imagens (Segurança e Sobre nós) | placeholder em degradê |
| “Esta resposta ajudou? Sim / Não” | removido: não há onde guardar o voto |
| 27 perguntas, só 2 com resposta no Figma | as perguntas do Figma e as que faltam, escritas para revisão |
| “Voltar ao inicio”, “SAIBA MAIS SOIBRE NOSSA” | “Voltar ao início”, “SAIBA MAIS SOBRE NOSSA” |

## Capabilities

### New Capabilities

- `institutional-pages`: as páginas Central de ajuda (e as categorias), Segurança, Termos, Privacidade, Quem somos e Contato, com a estrutura comum e a regra de conteúdo verdadeiro.

### Modified Capabilities

- `public-home`: “Como funciona” leva à seção institucional da home (`/#como-funciona`).
- `donation-chat-interface`: o botão flutuante passa a aparecer também nas páginas institucionais, como no Figma.

## Impact

- **Frontend:**
  - módulo novo `doafacil/institucional.py`, com as páginas e o conteúdo, e um estado simples para a busca da Central de ajuda;
  - módulo novo `doafacil/rodape.py`, com o rodapé e as rotas dele, movidos de `doafacil.py`;
  - em `doafacil/cabecalho.py`, o cabeçalho com o logotipo centralizado;
  - em `doafacil/doafacil.py`, as rotas e a âncora `como-funciona`.
- **Testes:** `tests/test_institucional.py` (novo), mais ajustes em `tests/test_public_home.py` e `tests/test_chat.py`.
- **Docs:** `docs/design/README.md` (as telas 19 a 23 e as diferenças) e `docs/guia-do-colaborador.md`.
- **Xano:** nada.
- **Fora do escopo:**
  - o e-mail de contato (pendência do grupo);
  - um formulário de contato;
  - o voto “Esta resposta ajudou?”;
  - a exclusão de conta pelo site.
