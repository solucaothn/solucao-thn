# Proposta

## Por quê

Hoje a pessoa aparece no site só com um círculo com a inicial do primeiro nome. A change editar-perfil deixou a foto de fora de propósito, para uma change própria. O Figma (`Group 7`) já tem a seção “Foto”, com “Alterar foto” e “Remover foto”. Uma foto ajuda quem recebe a doação a reconhecer quem doa, e vice-versa, sem expor nenhum dado privado.

## O que muda

- **Xano:**
  - campo novo de imagem opcional na tabela `user`;
  - **dois endpoints novos, com login, só para a própria pessoa:** enviar a foto e remover a foto. Aceitam os formatos das fotos de doação (JPG, PNG, GIF e WEBP), com limite de tamanho (dúvida 1), e respondem 400 com mensagem clara para formato ou tamanho inválidos;
  - **os endpoints que já devolvem dados da pessoa passam a devolver também a URL pública da foto, ou nulo:**
    - `GET auth/profile`;
    - `GET catalog/donations/mine`, para a própria pessoa;
    - `GET catalog/donations/donor`, para quem doa;
    - `GET catalog/donations/detail`, para quem doa;
    - `GET catalog/chat/conversations` e `GET catalog/chat/messages`, com a foto da **outra** pessoa.

    Nunca e-mail nem ids. A foto vem nas respostas que já existem, sem nenhuma requisição a mais, por causa do limite de 10 requisições a cada 20 s.
- **`/perfil/editar`:**
  - seção “Foto”, como no Figma, com “Alterar foto”, “Remover foto” e o aviso “Sua foto aparece para outras pessoas.”;
  - a foto é salva na hora, sem depender de “Salvar alterações”, e a prévia é atualizada.
- **A foto no lugar do círculo da inicial,** no mesmo tamanho, redonda, com `object-fit: cover` e texto alternativo com o primeiro nome:
  - na prévia da edição do perfil;
  - no cartão da pessoa em `/minhas-doacoes`;
  - no perfil público;
  - no cartão “Quem doa” do detalhe (dúvida 5);
  - no chat, na lista de conversas e no cabeçalho da conversa (dúvida 5).

  Sem foto, continua a inicial.
- **Scripts de teste real:** os que conferem chaves exatas passam a aceitar o campo da foto, e entra um script novo para a foto.
- **Apply em duas partes:** primeiro o Xano, com teste real; depois o frontend.

## Fora do escopo

- Recorte, zoom ou edição da imagem no navegador.
- Moderação automática do conteúdo da foto.
- Foto no cabeçalho da home (“Olá, <primeiro nome>”).
- Mudar o upload das fotos de doação, inclusive o limite de tamanho delas (dúvida 1).

## Capacidades

### Novas capacidades

Nenhuma. A foto é parte do perfil (`user-account`) e da identificação pública que já está nas outras capacidades.

### Capacidades modificadas

- `user-account`:
  - a consulta do perfil devolve a foto;
  - entra o requisito novo de enviar e remover a foto;
  - a página `/perfil/editar` ganha a seção “Foto” e deixa de proibi-la.
- `donor-public-profile`: a resposta e o cartão de identificação passam a ter a foto.
- `donation-management`: a listagem e o cartão da pessoa passam a ter a foto, que hoje é proibida.
- `donation-detail`: a resposta pública e o cartão “Quem doa” passam a ter a foto de quem doa, que hoje está na lista de itens ocultos.
- `donation-chat`: a listagem das conversas e a leitura das mensagens passam a devolver a foto da outra pessoa. A listagem hoje identifica a outra pessoa “somente pelo primeiro nome”.
- `donation-chat-interface`: a lista de conversas, que hoje proíbe foto, e o cabeçalho da conversa passam a mostrar a foto da outra pessoa.

## Impacto

- **Xano:**
  - a tabela `user`;
  - endpoints novos de foto no grupo Authentication;
  - os seis endpoints de leitura citados acima;
  - nenhum endpoint de envio ou edição de mensagens muda.
- **Frontend:**
  - um componente único de avatar (foto ou inicial), usado em seis lugares;
  - a seção “Foto” em `doafacil/editar_perfil.py`, com `rx.upload` (um arquivo, os formatos aceitos e o `max_size`);
  - os parsers e estados de `perfil_doador.py`, `minhas_doacoes.py`, `detalhe_doacao.py`, `chat.py` e `editar_perfil.py`.
- **Scripts:**
  - `scripts/teste_foto_perfil_real.py`, que é novo;
  - ajustes nas chaves exatas do `teste_perfil_real.py` (PP1), do `teste_minhas_doacoes_real.py` (MD2) e do `teste_editar_perfil_real.py` (EP2, EP3 e EP11);
  - o `teste_chat_real.py` não confere as chaves das conversas nem das mensagens e não muda.
- **Testes:** um arquivo novo para a foto e ajustes nos testes que conferem chaves exatas ou proíbem foto.
- **Documentação:** `docs/design/README.md` e `docs/guia-do-colaborador.md`.
