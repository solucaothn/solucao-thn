# Proposta

## Por quê

A auditoria visual de 27/11/2026 (capturas em 1280 e 360 px de todas as páginas públicas) achou detalhes que deixam o site com cara de inacabado:

- palavras quebradas no meio da tabela da Privacidade no celular;
- o seletor “Estado” do cadastro mais baixo que os outros campos;
- o botão do chat embaixo do selo “Built with Reflex”;
- o rodapé sem espaço entre “Fale conosco” e “Links rápidos” no celular;
- perguntas de duas linhas com as linhas coladas na Central de ajuda;
- “Entrar” e “Quero Doar” com alturas diferentes;
- o título de Explorar mais fraco que os das outras páginas;
- “Bem-vindo” no login, quando os outros textos já são neutros;
- a estatística “Pessoas alcançadas” mostrando “0”.

Além disso, o detalhe da doação foi ajustado para ficar mais profissional. Esse ajuste já está no código, mas as specs ainda descrevem o layout antigo:

- o título não fica mais repetido em caixa alta abaixo da galeria;
- o botão “Outros meios de comunicação” passou a se chamar “Outros contatos”;
- o cartão de resumo ganhou tamanhos e espaçamentos novos.

## O que muda

- **Detalhe da doação** (já implementado; as specs passam a descrevê-lo):
  - o título da doação aparece só no cartão de resumo, em semibold, com 28 px no celular e 30 px no computador, no máximo 3 linhas e reticências quando passa;
  - abaixo da galeria, o subtítulo “Descrição” vem no mesmo estilo de “Detalhes” e “Localização”;
  - o botão principal se chama “Outros contatos”;
  - os dois botões têm 48 px de altura e texto numa linha só;
  - o cartão tem 28 px de respiro, 8 px entre o título e a condição, 24 px até os botões e 12 px entre eles.
- **Privacidade:** a primeira coluna da tabela não quebra palavras no meio.
- **Cadastro:** o seletor “Estado” fica com 48 px de altura, como os outros campos.
- **Botão do chat:** fica acima do selo “Built with Reflex”, a 72 px da borda inferior no computador e a 60 px no celular. A distância da borda direita continua 24 px e 16 px. O espaço livre no fim das páginas cresce na mesma medida. O selo continua.
- **Rodapé:** 16 px entre “Fale conosco” e “Links rápidos” no celular e 12 px entre as colunas de links.
- **Central de ajuda:** as perguntas que ocupam duas linhas ganham altura de linha 1,35.
- **Cabeçalho:** “Entrar” e “Quero Doar” ficam com a mesma altura (44 px) e os mesmos cantos (6 px), no computador e no celular.
- **Explorar:** o título da página fica em negrito, como os de Categorias e da Central de ajuda.
- **Login:** “Bem-vindo” vira “Boas-vindas”.
- **Home:** a estatística “Pessoas alcançadas” some enquanto o número for 0. Ela continua aparecendo durante o carregamento, com erro e a partir de 1.

## Fora do escopo

- A marca d’água do Xano nas fotos (item 1 da auditoria): ela vem do armazenamento do Xano, não do site.
- O HTTP 404 do servidor de produção nas rotas com parâmetro (item 2): é comportamento conhecido do Reflex.
- O “Voltar” e o botão “Criar conta” das telas de autenticação (item 9), o título e os retângulos de “Quem somos” (item 11) e o botão “Buscar” preto da home (item 14).
- Lógica, estados e chamadas ao Xano: nada muda neles. As mudanças são só de visual e de texto.

## Capacidades

### Novas capacidades

Nenhuma.

### Capacidades modificadas

- `donation-detail`: título só no cartão de resumo, subtítulo “Descrição”, botão “Outros contatos” e as medidas do cartão.
- `user-account`: “Boas-vindas” no login e o seletor “Estado” com a altura dos outros campos.
- `public-home`: “Pessoas alcançadas” escondida enquanto for 0.
- `donation-chat-interface`: nova posição do botão flutuante, acima do selo.
- `public-home-content`: espaçamentos do rodapé no celular.
- `institutional-pages`: perguntas de duas linhas legíveis e tabela da Privacidade sem palavras partidas.
- `donation-explore`: título da página em negrito.
- `site-navigation`: “Entrar” e “Quero Doar” com o mesmo formato.

## Impacto

- **Código:** `doafacil/detalhe_doacao.py` (já alterado), `doafacil/institucional.py`, `doafacil/cadastro.py`, `doafacil/chat.py`, `doafacil/rodape.py`, `doafacil/cabecalho.py`, `doafacil/explorar.py`, `doafacil/login.py` e `doafacil/doafacil.py`.
- **Testes e documentação:** os testes dessas páginas, `README.md` e `docs/design/README.md`.
- Nenhum endpoint, tabela ou dependência nova.
