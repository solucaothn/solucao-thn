# Proposal

## Why

A auditoria deixou seis pontos de acabamento que atrapalham o uso e a apresentação, sem mexer no Xano:
- depois do login, a pessoa sempre cai na home;
- o 404 é o padrão do Reflex, em inglês;
- 14 abas mostram títulos como “Doafacil | Index”, e o favicon é o do Reflex;
- uma doação indisponível não oferece caminho;
- o chat vazio não tem saída;
- três páginas têm conteúdo mais largo que o das outras.

## What Changes

1. **Voltar à origem depois do login.** Toda ida ao `/login` a partir de uma página leva junto `?next=<caminho>`, e depois do login a pessoa volta para esse caminho.
   - **De onde se vai ao login:**
     - os redirecionamentos por falta de sessão, como “Chat” e contato no detalhe, “Quero Doar”, Minhas doações, chat e Editar perfil;
     - o “Entrar” do cabeçalho e o do menu do celular;
     - o botão flutuante do chat para quem não tem sessão.
   - **Cadastro de conta:** o link “Criar conta” leva o mesmo `next`, que atravessa a verificação do e-mail e chega ao login.
   - **Proteção contra open redirect:** só caminhos internos são aceitos. O `next` precisa começar com uma `/` só, sem esquema, host, `//`, `\` nem caracteres de controle, e não pode ser uma tela de autenticação. Qualquer outro valor leva à home.
2. **Página 404 própria** (`route="404"`) com o cabeçalho comum:
   - título “Página não encontrada”;
   - uma frase curta;
   - os links “Voltar ao início” e “Explorar doações”;
   - a animação `page-fade-enter`.
3. **Títulos e favicon:**
   - **Títulos:** todas as páginas no formato “Título | DoaFácil”, inclusive as 14 que hoje usam o padrão do Reflex.
   - **Favicon:** gerado do símbolo do `assets/logo.svg` (sem o texto) como `favicon.ico` (16, 32 e 48 px), `favicon-32.png` e `apple-touch-icon.png` (180 px), declarados no `<head>`.
   - **Geração:** o `scripts/gerar_favicon.py` usa o PyMuPDF, listado num `requirements-dev.txt` novo (fora do `requirements.txt`, porque o site não precisa dele). Os arquivos gerados entram prontos no commit.
4. **Doação indisponível.** Para reservada, concluída, apagada ou id inválido, o detalhe continua mostrando “Doação não encontrada” e acrescenta:
   - uma frase explicando que a doação pode ter sido reservada, concluída ou removida;
   - os links “Ver outras doações” (`/explorar`) e “Voltar ao início”.
5. **Chat sem conversas.** O aviso “Você ainda não tem conversas.” ganha o link “Explorar doações”.
6. **Alinhamento.** O conteúdo do perfil de quem doa, do detalhe e do Editar perfil passa para o mesmo contêiner de Minhas doações e da Explorar: 1200 px centralizado, com as margens laterais do cabeçalho da home dentro dele. A galeria e a disposição do detalhe ficam como estão.
- **Fora do escopo:**
  - qualquer mudança no Xano;
  - o cabeçalho com “Voltar” (largura toda, da `navegacao-celular`);
  - persistir o `next` depois de recarregar a página ou entre abas.

## Capabilities

### New Capabilities

- `site-shell`: os títulos das abas, o favicon e a página 404 própria.

### Modified Capabilities

- `user-account`: o “Login bem-sucedido” passa a levar ao caminho interno de origem (`next`) em vez de sempre à home. Novo requisito para o `next` seguro, inclusive no cadastro.
- `donation-detail`: a doação indisponível ganha a explicação e os links “Ver outras doações” e “Voltar ao início”.
- `donation-chat-interface`: a lista vazia ganha o link “Explorar doações”.

## Impact

- **Código:**
  - `doafacil/login.py` (`next` seguro, login e cadastro) e `doafacil/rotas.py` (caminho atual);
  - os pontos de redirecionamento ao login em `cadastro_doacao.py`, `chat.py`, `detalhe_doacao.py`, `editar_perfil.py` e `minhas_doacoes.py`;
  - `cabecalho.py` e `navegacao.py` (“Entrar”) e o `chat_fab`;
  - `cadastro.py` (link do login);
  - `doafacil.py` (títulos, 404 e `head`);
  - um módulo novo para a página 404;
  - `perfil_doador.py`, `detalhe_doacao.py` e `editar_perfil.py` (contêiner);
  - `chat.py` (lista vazia).
- **Arquivos novos:** `scripts/gerar_favicon.py`, `assets/favicon.ico` (substitui o do Reflex), `assets/favicon-32.png` e `assets/apple-touch-icon.png`.
- **Dependência:** `pymupdf` só no `requirements-dev.txt` novo, para gerar o favicon.
- **Testes:** um teste novo e ajustes nos testes que esperam `rx.redirect("/login")` exato.
- **Sem mudanças** no Xano e nas APIs.
