# Tarefas

Páginas estáticas, sem Xano. Os comandos `git` são rodados pelo Higor.

## 1. Estrutura compartilhada

- [x] 1.1 Criar `doafacil/rodape.py`, movendo de `doafacil.py` o `public_home_footer`, o `FOOTER_LINK_GROUPS`, o `_footer_link` e o `FOOTER_FOCUS_RING`, sem mudança visual. Trocar o `FUTURE_ROUTES` por `INSTITUTIONAL_ROUTES`, `CONTACT_ROUTE` e `CONTACT_EMAIL = ""` (decisões 1 e 3). Verificação: os testes do rodapé e da home passam, ajustados só no import e no nome das rotas.
- [x] 1.2 Em `doafacil/cabecalho.py`, criar o `logo_header()`, e em `doafacil/institucional.py` o `institutional_shell()`: cabeçalho, “Voltar ao início”, conteúdo com `page-fade-enter`, rodapé, `chat_fab()` e o espaço do botão (decisão 1). Verificação: um teste com uma página mínima confere cada parte e o 360 px.
- [x] 1.3 Dar `id="como-funciona"` à seção institucional da home e apontar o item “Como funciona” do menu para `/#como-funciona` (decisão 7). Verificação: teste do `href` e do `id` em `tests/test_public_home.py`.

## 2. Central de ajuda

- [x] 2.1 Levantar no Figma (`get_design_context`) os textos da Central de ajuda e as respostas que existirem, e escrever o `HELP_CATEGORIES` e o `MOST_ASKED` completos, com as perguntas e respostas que faltam a partir dos fatos do site (decisão 2). Verificação: um teste confere que cada categoria tem perguntas, que as quantidades são calculadas e que nenhuma resposta tem as palavras proibidas.
- [x] 2.2 Criar a página `/duvidas`: o título, o subtítulo, a busca com o `HelpState` (sem acento e em minúsculas, com debounce), os atalhos, os cartões de categoria, “Mais perguntadas” em `rx.accordion` (`single`, recolhível) e a caixa de contato. Verificação: testes da busca (resultados, contagem, vazio, atalhos e limpar), do acordeão e dos `href` dos cartões.
- [x] 2.3 Criar a página `/duvidas/[categoria]` com o `HelpCategoryState`: o nome, “N perguntas sobre …”, o acordeão, “Voltar para dúvidas frequentes” e a categoria não encontrada. Verificação: testes de um slug válido, de um desconhecido e do link de volta.

## 3. Segurança, Quem somos e Contato

- [x] 3.1 Criar `/seguranca` (decisão 4), com os textos do Figma corrigidos (decisão 9) e o placeholder no lugar da foto. Verificação: teste dos títulos, dos 4 benefícios, dos 2 cartões, da ordem dos títulos e da ausência de “CPF” e “criptografamos”.
- [x] 3.2 Criar `/quem-somos` (decisão 6): a frase de missão com o destaque em “doar”, “COMO FOI” / “O início do DoaFácil” com o texto do projeto acadêmico, os blocos verdes decorativos (`aria-hidden`) e o placeholder. Verificação: teste do texto, do destaque, da ausência de “2019” e “milhares” e do 360 px.
- [x] 3.3 Criar `/contato` e ligar “Fale com a gente” e o rodapé conforme o `CONTACT_EMAIL` (decisão 3). Verificação: testes com o e-mail vazio (aviso e link para `/duvidas`, sem `mailto`) e preenchido (`mailto:`).

## 4. Termos e Privacidade

- [x] 4.1 Escrever `/termos` com as seções da decisão 5, a partir dos fatos do site, o link para a Privacidade e a linha “Documento de projeto acadêmico, sem valor jurídico.” logo abaixo do título (também na Privacidade). Verificação: teste do `h1`, do aviso, dos `h2` numerados, do link e da ausência das palavras proibidas.
- [x] 4.2 Escrever `/privacidade` com as seções e a tabela da decisão 5 (rolagem só dentro do contêiner em 360 px) e o link para os Termos. Verificação: teste das linhas da tabela (só os dados reais), do que é público, do link e das palavras proibidas.
- [x] 4.3 (manual, Higor) Revisar os textos novos de Termos, Privacidade, Segurança, Quem somos e das respostas da Central de ajuda antes do merge. Verificação: o OK do Higor, ou os ajustes pedidos aplicados, anotados aqui.
  - OK do Higor: tabela de comprovação aprovada, com as 13 correções.
  - Conferência afirmação → código (pedido do Higor): cada fato dos textos foi comparado com o front e com `xano/`. Corrigidos 13 trechos sem comprovação: contato (chat ou e-mail, conforme a escolha de quem doa); reservada (marcação manual; segue no chat); edição de mensagem (também exige doação não concluída); chat (fecha na doação concluída); selo; perfil público (selo só se verificado); cancelar e retenção (os arquivos das fotos podem ficar no Xano); “Transparência total” (o detalhe público só mostra disponíveis); cartão “Criei uma doação” (o `publish_POST` não confere `email_verified`); tabela (doações visíveis só enquanto disponíveis; registros de uso guardam o `user_id` e a própria pessoa os lê); “O que é público” (doações disponíveis); e “Com quem compartilhamos” (Google Fonts recebe o IP).

## 5. Rotas, documentação e verificação

- [x] 5.1 Registrar as 7 rotas em `doafacil.py`, cada uma com o `on_load` do chat (`LoginState.load_account` e `ChatState.load_unread_total`) e um título de aba, e incluir as páginas institucionais no teste do botão do chat. Verificação: o teste de registro e o do botão em `tests/test_chat.py`.
- [x] 5.2 Atualizar o `docs/design/README.md` (as telas 19 a 23, as referências e a tabela de diferenças da decisão 9) e o `docs/guia-do-colaborador.md` (as páginas, o `rodape.py`, o `CONTACT_EMAIL` como pendência e o fim das rotas futuras). Verificação: o texto bate com as specs delta e o design.
- [x] 5.3 Rodar `python -m unittest discover -s tests`, `reflex compile` e `openspec validate paginas-institucionais --strict`. Verificação: tudo passa, e os resultados ficam anotados aqui.
  - Resultados: 604 testes OK, `reflex compile` OK e `openspec validate --strict` OK.
  - O Figma tem as perguntas de “Mais perguntadas” e “Doar um item” e só 2 respostas (a da taxa e “Como publico uma doação?”); as perguntas fechadas não guardam resposta no componente. As 27 perguntas estão em `HELP_CATEGORIES`, com as quantidades do Figma (4, 6, 5, 4, 5 e 3).
  - Um `mailto:` no `rx.link` vira um `ReactRouterLink` com `to:`, e o Link do React Router trata URLs com esquema como externas (gera um `<a href>`), então funciona sem componente especial.
- [x] 5.4 (manual) No navegador, em 1512 px e 360 px, comparando com `docs/design/19-*.png` a `23-*.png`:
  - cada página, com o cabeçalho, “Voltar ao início”, o rodapé e o botão do chat;
  - o acordeão pelo mouse e pelo teclado (abrir um fecha o outro);
  - a busca (“taxa”, “boleto”, “FOTO”, “doacao” sem acento) e os atalhos;
  - cada categoria e uma inexistente;
  - o “Como funciona” levando à seção da home;
  - o rodapé levando a cada página;
  - “Fale com a gente” e `/contato`;
  - a tabela da Privacidade em 360 px;
  - nenhuma rolagem horizontal.

  Verificação: os itens anotados aqui.
  - Primeira rodada (Higor): seis problemas, corrigidos na seção 6.
  - Segunda rodada, OK do Higor:
    - `/duvidas` com o acordeão legível, aberto e fechado;
    - a tabela da Privacidade legível;
    - o oval centralizado em “doar”;
    - `/contato` com o rodapé no fim;
    - o menu da conta com a foto;
    - o tema claro com o Windows em modo escuro;
    - home, Minhas doações, Editar perfil e chat sem mudança.
- [ ] 5.5 Montar a lista de caminhos para o commit; o Higor roda o `git diff --stat` e confere. Verificação: entram só os módulos, testes e docs desta change, os PNGs 19 a 23 e `openspec/changes/paginas-institucionais/`.

## 6. Ajustes do roteiro 5.4 (pedidos do Higor)

- [x] 6.1 Menu da conta com a foto de perfil no círculo (pedido novo, delta em `specs/public-home`): `LoginState.account_photo`, buscada no `GET auth/profile` uma vez por token no `load_account` (o `auth/me` não traz a foto e não foi alterado); inicial ou ícone sem foto; o Editar perfil atualiza o círculo ao carregar, trocar ou remover a foto. Verificação: `tests/test_cabecalho.py` (ordem foto → inicial → ícone, uma requisição por token, token rejeitado, falhas viram inicial) e `tests/test_edit_profile.py`.
- [x] 6.2 Acordeão de `/duvidas`: item aberto em creme claro (`#FFFAF1`), pergunta `#2A2A2A` e resposta `#555555` fixas em todos os estados, com as variáveis do Radix redefinidas no acordeão; lupa `#4A4A4A` e placeholder `#6B6B6B`. Causa: o app não fixa o tema, e o Radix seguia o modo escuro do sistema. Verificação: testes de contraste AA em `tests/test_institucional.py`.
- [x] 6.3 Tabela da Privacidade: células `#2A2A2A` sobre branco, cabeçalho e primeira coluna em negrito `#1F1F1F`, cores fixas. Verificação: testes de contraste AA.
- [x] 6.4 “Voltar ao início” da `/explorar` e da `/categorias`: o mesmo `back_link` das institucionais (agora em `cabecalho.py`), verde `#166B3B` também visitado e no hover. Verificação: teste que compara os dois.
- [x] 6.5 Oval de “doar” em Quem somos: `inline-block`, sem quebra, centrado na palavra em qualquer largura. Verificação: teste do estilo; conferir no navegador em 1512 e 360 px.
- [x] 6.6 Rodapé no fim nas páginas curtas: a casca vira coluna flex com `min-height: 100vh` e o conteúdo cresce (`flex: 1 0 auto`). Verificação: teste da estrutura; conferir `/contato` no navegador.
- [x] 6.7 Rodar a suíte e o `reflex compile`. Verificação: resultados anotados aqui.
  - Resultados: 623 testes OK, `reflex compile` OK e `openspec validate --strict` OK.
- [x] 6.8 Fixar o tema claro em todo o app (decisão 10 do design, pedido do Higor): `RadixThemesPlugin(theme=rx.theme(appearance="light", accent_color="blue"))` no `rxconfig.py`. Verificação: teste do modo de cor padrão em `tests/test_institucional.py`, a suíte e o `reflex compile`; no navegador, com o sistema em modo escuro, as páginas continuam claras.
  - Resultados: 624 testes OK, `reflex compile` OK (o build gera `defaultColorMode = "light"`) e `openspec validate --strict` OK.
- [x] 6.9 Anotar no guia, em “O que ainda falta”, as duas pendências de Xano para uma change futura: apagar os arquivos das fotos ao apagar uma doação, e recusar “Alimentos” no backend. Verificação: o texto do guia.
