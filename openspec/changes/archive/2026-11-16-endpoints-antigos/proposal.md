# Proposal

## Why

A auditoria do site achou dois endpoints antigos no grupo Catalog do Xano. O site não usa nenhum dos dois, e eles contornam regras que o projeto já adotou:

- **`GET catalog/donations` (público):** devolve todas as doações, de qualquer status (inclusive as reservadas e as concluídas), sem paginação. A Política de privacidade afirma que as doações só ficam visíveis enquanto estão disponíveis.
- **`POST catalog/donations` (com sessão):** cria uma doação já `disponível` só com categoria, título e descrição, sem foto, cidade, UF, condição, entrega nem contato, fora das validações do `publish`.

O grupo também definiu o e-mail de contato do projeto, que as páginas institucionais ainda tratam como pendente.

## What Changes

- **BREAKING (sem consumidores conhecidos):** remover do Xano o `GET catalog/donations` e o `POST catalog/donations`, que passam a responder “não encontrado”.
  - O `PATCH catalog/donations` (editar) e o `DELETE catalog/donations` (apagar), no mesmo caminho, ficam como estão.
  - A busca confirmou que nada em `doafacil/`, `scripts/` e `tests/` chama o GET ou o POST desse caminho. O front usa só o PATCH e o DELETE ([minhas_doacoes.py](../../../doafacil/minhas_doacoes.py)), e os scripts reais também.
- A remoção segue o caminho da change `endpoints-publicos`:
  - um script real confere o estado antes (as rotas existem) e depois (404);
  - o Higor apaga os dois endpoints pelo painel;
  - o agente apaga só os dois `.xs`;
  - o Higor faz o pull, e conferimos que eles não voltaram.
  - Nenhum push ao Xano.
- **E-mail de contato:** `CONTACT_EMAIL = "solucaothn@gmail.com"` em `doafacil/rodape.py`.
  - Os convites “Fale com a gente” e “Clique aqui para falar conosco” continuam levando a `/contato`, que passa a mostrar o e-mail escrito e com link `mailto:`.
  - Os textos que diziam “o canal de contato ainda vai ser publicado” passam a citar o e-mail:
  - a página `/contato`;
  - a caixa “Não encontrou o que procurava?” da Central de ajuda;
  - a seção 7 dos Termos;
  - a seção 7 da Privacidade.
- **Testes:**
  - um teste novo confere que o front não chama o GET nem o POST do caminho, e que os dois `.xs` não existem depois da remoção;
  - os testes do contato passam a conferir o e-mail real, e o teste de e-mail inventado aceita só esse endereço.
- **Documentação:**
  - no `docs/guia-do-colaborador.md`, a pendência do e-mail fica resolvida, a nota do “`GET /catalog/donations` antigo” sai e o script novo fica documentado;
  - no `docs/design/README.md`, a linha do contato da tabela de diferenças do Figma.

## Capabilities

### New Capabilities

Nenhuma.

### Modified Capabilities

- `public-donation-discovery`: requisito novo. Nenhum endpoint público lista doações fora das regras da busca pública, ou seja, nenhuma doação reservada, concluída ou fora das listagens previstas.
- `donation-creation`: requisito novo. Uma doação só é criada pela publicação com as regras do `publish` (fotos, cidade e UF do perfil, condição, entrega e contato).
- `institutional-pages`: o requisito “Conteúdo verdadeiro” muda. O contato do projeto é `solucaothn@gmail.com`; o cenário “Contato definido” passa a valer (convites para `/contato`, o e-mail escrito e com `mailto:`, e nenhum “ainda vai ser publicado”), e um cenário novo cobre os textos da Central de ajuda, dos Termos e da Privacidade. O cenário “Contato ainda não definido” fica como reserva, para o caso de o e-mail voltar a ficar vazio.

## Impact

- **Xano:** dois endpoints removidos pelo painel, sem push. Nenhuma tabela, função ou outro endpoint muda. O `xano/` local perde `api/catalog/catalog/donations_GET.xs` e `api/catalog/catalog/donations_POST.xs`.
- **Frontend (Reflex):** `doafacil/rodape.py` (o e-mail) e `doafacil/institucional.py` (os textos). As rotas do site não mudam: `/contato` continua no ar e mostra o e-mail.
- **Testes, scripts e docs:**
  - testes: `tests/test_endpoints_antigos.py` (novo) e `tests/test_institucional.py`;
  - script: `scripts/teste_endpoints_antigos_real.py` (novo);
  - docs: `docs/guia-do-colaborador.md` e `docs/design/README.md`.
- **Fora do escopo:**
  - as pendências do Xano já anotadas no guia (Alimentos no backend e os arquivos das fotos de doações apagadas);
  - os outros itens da auditoria (menu no celular, volta depois do login, página 404, títulos das abas e favicon);
  - as diferenças de esquema e de formatação conhecidas do `xano/`.
