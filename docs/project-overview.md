# Project Overview — DoaFácil

## 1. Visão geral

O DoaFácil é uma plataforma web que conecta pessoas que querem doar objetos físicos a pessoas que precisam ou têm interesse nesses itens. Ela facilita todo o caminho da doação: anunciar, encontrar, demonstrar interesse e combinar a entrega ou retirada.

Ideia central: um objeto que deixou de ser útil para uma pessoa pode continuar sendo útil para outra. O DoaFácil existe para criar essa ponte.

## 2. Problema

Muitas pessoas têm objetos em bom estado que não usam mais, enquanto outras poderiam precisar ou querer esses mesmos itens. Sem uma plataforma específica, é difícil:

- encontrar quem precisa do item;
- encontrar um determinado tipo de doação;
- divulgar o objeto de forma organizada;
- entrar em contato com os interessados;
- acompanhar o andamento da doação.

Como consequência, itens ainda úteis são descartados ou ficam esquecidos.

## 3. Objetivos

- Tornar a doação de objetos simples, organizada e acessível.
- Centralizar em uma única plataforma o anúncio, a busca e o acompanhamento das doações.
- Estimular reutilização, circulação e aproveitamento de objetos, reduzindo o desperdício.
- Ter impacto social e de sustentabilidade, indo além de um simples catálogo de itens.

## 4. Público-alvo / usuários

- **Doador:** pessoa que possui um objeto que não usa mais e quer disponibilizá-lo.
- **Interessado:** pessoa que procura determinado item e quer recebê-lo.

Uma mesma pessoa pode atuar nos dois papéis em momentos diferentes.

## 5. Escopo

### Dentro do escopo

- Doação de **objetos físicos**.
- Categorias planejadas: roupas, móveis, livros, eletrônicos, brinquedos e outros.
- Cadastro de usuários e autenticação.
- Cadastro, listagem, busca e acompanhamento de doações.
- Demonstração de interesse em uma doação.
- Comunicação entre doador e interessado.
- Associação da doação a uma localização/região.
- Avaliação da experiência entre usuários.

### Fora do escopo

O DoaFácil **não é**:

- plataforma de doações financeiras, vaquinhas ou arrecadação de dinheiro;
- marketplace de compra e venda ou loja virtual;
- plataforma de doação de alimentos (não é categoria do sistema);
- rede social genérica.

## 6. Principais funcionalidades

**Para quem quer doar**

- Criar conta e entrar na plataforma.
- Cadastrar o objeto com título, descrição, categoria, localização e características.
- Disponibilizar a doação e acompanhar seu status.
- Receber contato de pessoas interessadas.

**Para quem procura uma doação**

- Explorar as doações disponíveis.
- Pesquisar por itens e filtrar por categoria.
- Ver os detalhes de uma doação.
- Demonstrar interesse e entrar em contato com o responsável.

**Comuns**

- Troca de mensagens entre usuários ligados a uma doação.
- Avaliação após uma interação ou doação.

## 7. Requisitos e restrições importantes

- O foco é exclusivamente em bens e objetos físicos.
- Não há movimentação financeira dentro da plataforma.
- A plataforma deve ser simples de usar tanto para quem doa quanto para quem recebe.
- O projeto é acadêmico e será desenvolvido de forma incremental por um grupo.

## 8. Arquitetura tecnológica

| Camada | Tecnologia | Responsabilidade |
|---|---|---|
| Frontend | Reflex (Python) | Interface, páginas, navegação, formulários, catálogo e interação com o usuário |
| Backend | Xano | Usuários, autenticação, banco de dados, regras de negócio e APIs |
| Especificação | OpenSpec | Organizar o desenvolvimento em mudanças planejadas, especificações e tarefas |
| Versionamento | Git + GitHub | Histórico, branches, colaboração e recuperação de versões |

Reflex será utilizado como tecnologia exclusiva para implementação do frontend da aplicação.

O frontend consome as APIs do backend. As regras de negócio e a persistência ficam no Xano.

## 9. Princípios de desenvolvimento

- Especificar antes de implementar, usando OpenSpec.
- Evoluir em mudanças pequenas e verificáveis, não construir tudo de uma vez.
- Manter o modelo conceitual global (`docs/domain-model.md`) como referência, mesmo que a implementação seja incremental.
- Reutilizar o que já existe e evitar duplicação.
- Não introduzir tecnologias alternativas sem justificativa.

## 10. Segurança e integridade

- Regras de autorização e validação devem ser aplicadas no **backend (Xano)**; o frontend não é mecanismo de segurança.
- Credenciais, tokens e chaves não devem ser versionados no Git.
- Dados pessoais dos usuários devem ser tratados com cuidado; a comunicação entre usuários só deve existir no contexto de uma doação.

## 11. Estratégia de desenvolvimento

O projeto segue o ciclo do OpenSpec:

```text
Explore → Propose → Review → Apply → Archive → próxima change
```

1. O grupo prepara o contexto (este documento, o modelo de domínio e o `AGENTS.md`).
2. Faz um Explore geral para decompor o projeto em mudanças incrementais.
3. Cada mudança é proposta, revisada pelo grupo, implementada e arquivada.

A IA propõe, o grupo analisa e aprova, e só então a IA implementa.

## 12. Fonte de verdade e documentação

| Documento | Função |
|---|---|
| `docs/project-overview.md` | O que é o projeto (este arquivo) |
| `docs/domain-model.md` | Conceitos do domínio e seus relacionamentos |
| `AGENTS.md` | Como os agentes de IA devem trabalhar no projeto |
| `openspec/config.yaml` | Contexto e regras injetados nos workflows do OpenSpec |
| `openspec/specs/` | Comportamento consolidado do sistema |
| `openspec/changes/` | Mudanças em andamento e histórico (`archive/`) |

Em caso de conflito sobre o comportamento do sistema, as specs em `openspec/specs/` prevalecem sobre este documento de visão geral.
