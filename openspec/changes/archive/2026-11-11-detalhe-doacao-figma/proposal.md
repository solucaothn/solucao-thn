# Proposta

## Por quê

A página `/doacao/<id>` mostra os dados certos, mas com um layout diferente do Figma:
- a descrição e os detalhes aparecem como uma lista de rótulos e textos;
- a galeria não segue a grade de fotos do desenho;
- a localização não tem destaque.

O grupo quer a página visualmente igual aos frames `detalhes-doacao-inteira` e `detalhes-doacao-1`, usando **só os dados que o detalhe já devolve**, sem mexer no Xano.

## O que muda

Só no frontend (Reflex). Nada muda em `xano/` nem nos endpoints.

- **Galeria como no Figma:** capa grande à esquerda e até 4 miniaturas numa grade 2x2 ao lado, no computador. A doação tem no máximo 5 fotos. No celular, a capa vem em cima e as miniaturas abaixo.
- **Resumo à direita**, num cartão branco com sombra, como no Figma:
  - o título grande;
  - “Condição: …”;
  - os botões “Outros meios de comunicação” e “Chat” e a mensagem de retorno do contato.

  O botão principal passa ao verde `#007A42`. O `#00A859` atual não tem contraste AA com o texto branco.
- **Título e descrição logo abaixo da galeria:** título em negrito e descrição em texto corrido.
- **Seção “Detalhes”** em grade, em que cada item tem um ícone verde, um rótulo pequeno e o valor: Categoria, Condição, Forma de entrega e Preferência de contato.
- **Seção “Localização”** em cartão com ícone, mostrando só “Cidade, UF”.
- **Cartão “Quem doa”** com o visual do cartão do Figma (borda clara e ícone de local), ainda só com o primeiro nome e “Cidade, UF”.
- **Continuam como estão:**
  - as fotos (ordem, sem repetição e imagem genérica);
  - o link de volta à home, agora como “Voltar ao início” na linha do logotipo, igual ao chat;
  - os estados de carregamento, não encontrada e erro;
  - o fluxo de contato (Chat e E-mail);
  - a animação de entrada `page-fade-enter` sem animar dados do Xano;
  - o contraste AA e o layout de celular.

### Decisão do grupo: o que não entra

O Figma mostra itens que o DoaFácil não tem ou que expõem dados privados. Eles **não serão criados nem aparecerão como “Em breve”**:
- **Atributos do Figma:** Cor, Material e Tipo, que não existem no cadastro.
- **Localização detalhada:** bairro, zona e CEP. Por privacidade, a localização pública é só cidade e UF.
- **Itens do cartão do anunciante:** foto, “Online”, “No DoaFácil desde…”, avaliações, histórico, informações verificadas e o botão de perfil.

## Fora do escopo

- Qualquer mudança no Xano, em endpoints ou em dados devolvidos.
- Novos campos de doação e a página de perfil de quem doa.
- “NOVO” e status no detalhe: o detalhe não recebe a data de criação, e só mostra doações disponíveis. Decisão do Higor: não aparecem.

## Capacidades

### Novas capacidades

Nenhuma.

### Capacidades modificadas

- `donation-detail`: “Conteúdo do detalhe da doação” passa a descrever:
  - a disposição da galeria e do resumo;
  - o título e a descrição abaixo da galeria;
  - a grade “Detalhes” com ícone, rótulo e valor;
  - o cartão “Localização” só com cidade e UF;
  - o contraste do botão principal.
- `donation-detail`: “Botão Voltar do detalhe” passa para a linha do logotipo como “Voltar ao início”, igual ao chat e ao Figma (decisão do Higor).

## Impacto

- **Código:** `doafacil/detalhe_doacao.py` (componentes da página; o estado e o cliente não mudam) e `doafacil/chat.py`, onde o cabeçalho com “Voltar ao início” vira `back_home_header()` para ser reaproveitado.
- **Recursos:** dois ícones do Figma em `assets/`: o ícone de atributo e a ilustração de localização.
- **Testes:** `tests/test_donation_detail.py`.
- **Documentação:** seção “Detalhe da doação” em `docs/design/README.md`, que prevalece sobre o Figma.
- **Carga no Xano:** nenhuma mudança; a página continua com uma consulta ao abrir.
