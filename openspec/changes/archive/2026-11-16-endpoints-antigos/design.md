# Design

## Context

O motivo está no `proposal.md` (Why). Estado atual, levantado no `xano/` e no código:

| Arquivo | Rota | `auth` | O que faz hoje |
|---|---|---|---|
| `xano/api/catalog/catalog/donations_GET.xs` | `GET catalog/donations` | nenhum | lista todas as doações (qualquer status), com `id`, datas, `category_id`, título, descrição e status; filtros opcionais `search` e `category_id`; sem paginação |
| `xano/api/catalog/catalog/donations_POST.xs` | `POST catalog/donations` | `user` | cria uma doação `disponível` com `category_id`, título e descrição, sem foto, cidade, UF, condição, entrega nem contato |

- **Mesmo caminho, outros métodos:** o `PATCH catalog/donations` (`donations_PATCH.xs`, editar) e o `DELETE catalog/donations` (`donations_DELETE.xs`, apagar) ficam. O front os usa em `doafacil/minhas_doacoes.py` (`client.patch` e `client.delete` com `DONATION_PATH`), e os scripts reais também (`teste_minhas_doacoes_real.py`, `teste_chat_real.py`, `teste_fotos_formulario_real.py` e `limpeza_dados_teste.py`).
- **Quem usa o GET e o POST:** ninguém. Uma busca em `doafacil/`, `scripts/` e `tests/` só achou PATCH e DELETE nesse caminho. Os outros endpoints de doação têm sufixo (`/publish`, `/search`, `/recent`, `/count`, `/detail`, `/donor`, `/mine`, `/status`, `/contact-email`).
- **Contato:**
  - `CONTACT_EMAIL = ""` em `doafacil/rodape.py`;
  - o `contact_href()` devolve `/contato` com o e-mail vazio, ou `mailto:` com ele preenchido;
  - os textos “o canal de contato ainda vai ser publicado” estão em `doafacil/institucional.py`: o `CONTACT_PENDING_TEXT` (na página `/contato` e na caixa da Central de ajuda), a seção 7 dos Termos e a seção 7 da Privacidade.
- **Spec do rodapé:** a `public-home-content` exige que “Clique aqui para falar conosco” leve a `/contato`.

## Goals / Non-Goals

**Goals:**
- O GET e o POST saem do workspace; o PATCH e o DELETE do mesmo caminho ficam intactos.
- Nenhum push ao Xano. O `xano/` local fica igual ao workspace nesses dois objetos.
- O e-mail `solucaothn@gmail.com` aparece onde o contato era “pendente”, escrito e com `mailto:`.

**Non-Goals:**
- Desativar os endpoints mantendo os arquivos (descartado na `endpoints-publicos`, pelo mesmo motivo).
- As pendências do Xano já anotadas no guia (Alimentos no backend, arquivos das fotos) e os outros itens da auditoria.
- Formulário de contato ou mudança nas respostas da Central de ajuda além da caixa de contato.

## Decisions

### 1. Apagar só o GET e o POST pelo painel, sem push

O mesmo caminho da `endpoints-publicos`: o Higor faz tudo o que envolve o painel e os comandos `git` e `xano`, e o agente só edita arquivos.

| Objeto no painel | Onde fica | Arquivo local |
|---|---|---|
| `GET /catalog/donations` | API Group **Catalog** | `xano/api/catalog/catalog/donations_GET.xs` |
| `POST /catalog/donations` | API Group **Catalog** | `xano/api/catalog/catalog/donations_POST.xs` |

- **Atenção no painel:** o grupo Catalog tem quatro endpoints com o caminho `catalog/donations`. Só o **GET** e o **POST** saem; o **PATCH** e o **DELETE** ficam. O script (decisão 2) confere os dois que ficam.
- **Ordem:**
  1. **Antes:** o Higor roda o script com `--antes`. O GET e o POST ainda existem.
  2. **Painel:** o Higor apaga os dois e avisa.
  3. **Arquivos:** o agente apaga só os dois `.xs`, sem restore, stash nem checkout.
  4. **Pull:** o Higor roda `xano workspace pull -d ./xano` e o `git status`. Os dois arquivos não voltam, e o PATCH e o DELETE continuam no `xano/`.
  5. **Depois:** o Higor roda o script sem `--antes`.
- **Por que não o push:** o push parcial não apaga nada, e o `--sync --delete` apagaria tudo o que não estiver na pasta local e reenviaria as diferenças de esquema conhecidas.
- **Por que não o Xano MCP Server:** o `AGENTS.md` não permite.

### 2. Script real, antes e depois, sem efeito colateral

`scripts/teste_endpoints_antigos_real.py`, no padrão do `teste_endpoints_publicos_real.py`: reaproveita `base_url`, `registrar` e `resumo` do `teste_chat_real.py`, usa a variável `XANO_API_URL` (grupo Catalog), não pede login, não leva token, não cria dados e imprime só o cenário, o status HTTP e OK/FALHOU (num 2xx inesperado, só a estrutura).

| Cenário | Pedido | Com `--antes` | Depois |
|---|---|---|---|
| EA1 | `GET catalog/donations?category_id=0` | diferente de 404: a categoria 0 não existe e a `precondition` dá erro de entrada, sem devolver doações | 404 |
| EA2 | `POST catalog/donations` sem token, corpo vazio | diferente de 404 (401, sem criar nada) | 404 |
| EA3 | `PATCH catalog/donations` sem token | diferente de 404 (401) | diferente de 404 (401) |
| EA4 | `DELETE catalog/donations` sem token | diferente de 404 (401) | diferente de 404 (401) |
| EA5 | `POST catalog/donations/publish` sem token | diferente de 404 (401) | diferente de 404 (401) |
| EA6 | `GET catalog/donations/search?page=0` | diferente de 404 (erro de entrada, sem doações) | diferente de 404 |

- **404 ou 405:** o PATCH e o DELETE continuam no caminho, então o Xano pode responder 404 ou 405 a um método que não existe mais. No modo “depois”, EA1 e EA2 aceitam os dois e imprimem qual veio. No “antes”, um 404 ou 405 é falha.

### 3. Contato: `/contato` mostra o e-mail, e os convites levam a ela

- **`CONTACT_EMAIL = "solucaothn@gmail.com"`** em `doafacil/rodape.py`.
- **Convites:** “Fale com a gente” e “Clique aqui para falar conosco” continuam levando a `/contato`. O `contact_href()` passa a devolver sempre `/contato`, e o ramo do `mailto:` sai.
  - **Motivo:** um `mailto:` direto não faz nada visível em quem não tem um programa de e-mail configurado (comum em quem usa só webmail), e o endereço não aparece.
  - A `/contato` mostra o e-mail escrito, que dá para copiar, e com o `mailto:`. Além disso, mantém a regra da `public-home-content` para o rodapé.
- **Textos novos** (substituem os “ainda vai ser publicado”; o e-mail sempre como `_link` com `mailto:`):
  - **`/contato`:** “Escreva para solucaothn@gmail.com.” e, abaixo, “Pelo mesmo e-mail você pode pedir para saber, corrigir ou apagar os seus dados.”, mais os links para a Central de ajuda e a Privacidade (que já existem);
  - **caixa da Central de ajuda:** “Escreva para solucaothn@gmail.com”, com o botão “Fale com a gente” levando a `/contato`;
  - **Termos, seção 7:** “Dúvidas sobre estes Termos: escreva para solucaothn@gmail.com.”;
  - **Privacidade, seção 7:** “Para os outros pedidos, como saber quais dados temos ou apagar a sua conta, escreva para solucaothn@gmail.com.”
- **Como o e-mail vira link nos textos:** as seções dos Termos e da Privacidade hoje são só strings. O parágrafo com o e-mail passa a ser montado com o texto e o `_link` do e-mail. A estrutura (títulos `h2` numerados e parágrafos) não muda.
- **O ramo “sem e-mail” fica, como reserva:** se o `CONTACT_EMAIL` voltar a ficar vazio, a `/contato`, a caixa e as seções 7 dos Termos e da Privacidade mostram o `CONTACT_PENDING_TEXT`, como hoje.
  - É a regra do cenário “Contato ainda não definido”, que continua na spec.
  - Evita que um e-mail apagado por engano deixe um texto apontando para lugar nenhum. Os textos das seções 7 passam a depender do `CONTACT_EMAIL`, como a página e a caixa.

### 4. Testes

- **`tests/test_endpoints_antigos.py` (novo):**
  - lê o código de `doafacil/` e confere que o caminho `/catalog/donations` sem sufixo só aparece em chamadas `client.patch` e `client.delete`;
  - nenhum módulo chama `client.get` ou `client.post` nesse caminho;
  - depois da tarefa 3.1, também confere que os dois `.xs` não existem e que o `donations_PATCH.xs` e o `donations_DELETE.xs` continuam.
- **`tests/test_institucional.py`:**
  - o teste de e-mail inventado passa a aceitar só `mailto:solucaothn@gmail.com` e a recusar qualquer outro `@`;
  - os testes do contato conferem que os convites levam a `/contato` e que a `/contato`, a caixa, os Termos e a Privacidade mostram o e-mail com o `mailto:`;
  - com o e-mail definido, nenhum texto diz “ainda vai ser publicado”;
  - com o `CONTACT_EMAIL` vazio (por `patch`), os quatro lugares voltam ao texto pendente, sem `mailto:`.

### 5. Commit só com o que é da change

- **Entram:**
  - a remoção dos dois `.xs`;
  - `openspec/changes/endpoints-antigos/`;
  - `doafacil/rodape.py` e `doafacil/institucional.py`;
  - os dois testes e o script;
  - o `docs/guia-do-colaborador.md` e o `docs/design/README.md`.
- **Não entram:** os outros arquivos do `xano/` que o pull marca como modificados (`user.xs`, `signup_pending.xs`, `donation_photo.xs` e os de formatação). Cada caminho é adicionado um por um.

## Risks / Trade-offs

- **[Apagar o PATCH ou o DELETE por engano no painel]** → a tabela da decisão 1 dá o método exato, e o EA3 e o EA4 pegam o erro na hora. Se acontecer, a restauração é a mesma do incidente da `endpoints-publicos`: um push só desse arquivo (`-i`), com o dry-run revisado antes.
- **[Um dos dois voltar no pull]** → o objeto não foi apagado no painel. Repete o passo 2 para ele.
- **[Consumidor externo desconhecido]** → nenhum no repositório. O papel dos dois já é feito pelo `publish` e pelas consultas com sufixo.
- **[E-mail público recebe spam]** → é o canal escolhido pelo grupo. A página não usa formulário, então não há envio automático pelo site.
- **[Pedidos de dados pelo e-mail]** → a Privacidade passa a oferecer o e-mail para saber, corrigir ou apagar dados, e não existe exclusão de conta pelo site. O grupo precisa atender esses pedidos à mão, pelo painel do Xano. Fica anotado no guia como responsabilidade do grupo.

## Migration Plan

1. O agente escreve o script, os testes, os textos do contato e a documentação.
2. O Higor roda o script com `--antes`, apaga o GET e o POST no painel e avisa.
3. O agente apaga os dois `.xs` e acrescenta a conferência dos arquivos ao teste.
4. O Higor faz o pull, confere o `git status` e roda o script sem `--antes`.
5. **Rollback:**
   - **endpoints:** recriar a partir dos arquivos na `main` com um push parcial só deles (`-i`), revisado no dry-run e aprovado pelo grupo;
   - **contato:** reverter pelo `git`.
