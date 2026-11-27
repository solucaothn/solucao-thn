# Tarefas

Os comandos `git` e `xano` são do Higor. Esta change não mexe em `xano/` nem em chamadas ao Xano. Para as capturas com dados reais, `XANO_API_URL` e `XANO_AUTH_API_URL` ficam só no ambiente da sessão. As capturas de “antes” são as da auditoria de 27/11/2026.

## 1. Detalhe da doação

- [x] 1.1 Conferir que o ajuste já feito em `doafacil/detalhe_doacao.py` bate com as specs desta change (decisão 1): título só no cartão, em até 3 linhas; “Descrição”; “Outros contatos”; botões de 48 px; espaçamentos de 28, 8, 24 e 12 px. Verificação: os testes de `tests/test_donation_detail.py` passam.

## 2. Correções da auditoria

- [x] 2.1 Tabela da Privacidade sem palavras partidas (decisão 2), em `doafacil/institucional.py`. Verificação: teste em `tests/test_institucional.py`.
- [x] 2.2 Seletor “Estado” do cadastro com 48 px (decisão 3), em `doafacil/cadastro.py`. Verificação: teste em `tests/test_acabamento_visual.py`.
- [x] 2.3 Botão do chat acima do selo e espaço livre maior (decisão 4), em `doafacil/chat.py`. Verificação: testes em `tests/test_chat.py` e `tests/test_acabamento_visual.py`.
  - Revertido em 27/11/2026: o selo só aparece em --env prod; no modo dev o botão volta ao canto.
- [x] 2.4 Espaçamentos do rodapé (decisão 5), em `doafacil/rodape.py`. Verificação: testes em `tests/test_public_home.py` e `tests/test_acabamento_visual.py`.
- [x] 2.5 Altura de linha das perguntas (decisão 6), em `doafacil/institucional.py`. Verificação: teste em `tests/test_acabamento_visual.py`.
- [x] 2.6 “Entrar” com o formato do “Quero Doar” (decisão 7), em `doafacil/cabecalho.py`. Verificação: teste em `tests/test_acabamento_visual.py`.
- [x] 2.7 Título de Explorar em negrito (decisão 8), em `doafacil/explorar.py`. Verificação: teste em `tests/test_acabamento_visual.py`.
- [x] 2.8 “Boas-vindas” no login (decisão 9), em `doafacil/login.py`, com o `docs/design/README.md` atualizado. Verificação: teste em `tests/test_login.py`.
- [x] 2.9 “Pessoas alcançadas” escondida enquanto for 0 (decisão 10), em `doafacil/doafacil.py`. Verificação: teste em `tests/test_acabamento_visual.py`.

## 3. Conferência

- [x] 3.1 Rodar a suíte completa. Verificação: todos os testes passam.
- [x] 3.2 Com o app em modo de produção, capturar em 1280 e 360 px as páginas afetadas e comparar com as capturas da auditoria. Verificação: os resultados ficam anotados aqui. As páginas são home, `/explorar`, o detalhe, `/duvidas/primeiros-passos`, `/privacidade`, `/contato`, `/login` e `/cadastro`.
  - Resultados (27/11/2026, Edge headless pelo DevTools, `reflex run --env prod`, Xano real só no ambiente da sessão):
    - **Geral:** nenhuma das 8 páginas, nas duas larguras, tem rolagem horizontal, elemento fora da tela, texto cortado ou imagem distorcida. O único registro do console é o 404 conhecido do documento nas rotas com parâmetro (`/doacao/<id>` e `/duvidas/<categoria>`).
    - **Botão do chat:** fica a 72 px da borda inferior e 24 px da direita (1280 px), e a 60 px e 16 px (360 px). O selo vai até 54 px e 46 px da borda inferior. Não há sobreposição nas duas larguras, e o selo continua visível.
    - **Cabeçalho:** “Entrar” e “Quero Doar” têm 44 px de altura e cantos de 6 px em 1280 px. Em 360 px, “Entrar” tem 44 px e 6 px.
    - **Home:** “Pessoas alcançadas” não aparece com 0 doações concluídas, e “Doações em circulação!” (21) continua.
    - **Cadastro:** o seletor “Estado” tem 48 px de altura, como “Cidade”, com borda `#C8C8C8`, nas duas larguras. Antes tinha cerca de 32 px.
    - **Central de ajuda (360 px):** as perguntas usam altura de linha de 21,6 px (1,35 × 16 px). “O DoaFácil cobra alguma taxa?” e “Preciso pagar para publicar uma doação?” ficam em duas linhas sem encostar.
    - **Privacidade (360 px):** a primeira coluna tem 146 px, e “Mensagens do chat”, “Registros de uso” e “Foto de perfil e texto Sobre” quebram só entre palavras. As outras colunas rolam dentro da tabela.
    - **Rodapé (360 px):** 16 px entre “Clique aqui para falar conosco” e “Links rápidos”. As colunas de links têm 12 px entre si, e as linhas de grupos diferentes ficam com o mesmo espaço.
    - **Explorar:** “Adicionadas recentemente” tem peso 700.
    - **Login:** o cartão mostra “Boas-vindas”.
    - **Detalhe:** o título fica só no cartão, em até 3 linhas, com reticências quando passa (conferido com um título longo injetado só no navegador). “Descrição” usa o estilo de “Detalhes”, e “Outros contatos” e “Chat” têm 48 px.
- [x] 3.3 Rodar `openspec validate acabamento-visual --strict`. Verificação: sem erros.
