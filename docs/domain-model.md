Domain Model — DoaFácil
Este documento descreve os conceitos do domínio do DoaFácil e como eles se relacionam. É um modelo conceitual: não define tabelas, tipos de dados nem endpoints. A implementação física acontece de forma incremental, por meio das changes do OpenSpec.
Visão geral dos conceitos
```text
Usuário
   │
   ├── cadastra ───────► Doação ◄──── pertence a ──── Categoria
   │                        │
   │                        └── está em ──► Localização
   │
   ├── demonstra ──────► Interesse ───► (em uma Doação)
   │
   ├── envia ──────────► Mensagem ────► (no contexto de uma Doação)
   │
   └── faz / recebe ───► Avaliação ───► (entre usuários, após uma doação)
```
Uma pessoa pode atuar como doador (quem cadastra a doação) ou como interessado (quem demonstra interesse). Não existem dois tipos de conta: o papel depende da relação do usuário com cada doação.
---
Usuário
Representa uma pessoa que utiliza a plataforma.
Principais informações
nome;
e-mail e credenciais de acesso;
localização (cidade e estado);
papel no sistema, quando necessário (por exemplo, administração).
Relacionamentos
Um usuário pode cadastrar várias doações.
Um usuário pode demonstrar interesse em várias doações.
Um usuário pode enviar e receber várias mensagens.
Um usuário pode fazer e receber várias avaliações.
---
Doação
Representa um objeto físico disponibilizado por um usuário para ser doado. É o conceito central do sistema.
Principais informações
título;
descrição e características do item;
categoria;
localização;
status;
responsável (o doador).
Relacionamentos
Pertence a um doador (usuário).
Pertence a uma categoria.
Pode receber vários interesses.
Pode ter várias mensagens associadas.
Pode originar avaliações.
Regras estruturais
Só objetos físicos podem ser doados; não há doação de dinheiro nem de alimentos.
Toda doação possui um doador e uma categoria.
---
Categoria
Organiza as doações para facilitar a navegação e a busca.
Categorias planejadas
Roupas, Móveis, Livros, Eletrônicos, Brinquedos e Outros.
Relacionamentos
Uma categoria agrupa várias doações.
Uma doação pertence a uma única categoria.
---
Interesse
Representa o momento em que um usuário demonstra querer receber determinada doação.
Relacionamentos
Liga um usuário interessado a uma doação.
Uma doação pode ter vários interesses.
Um usuário pode ter interesse em várias doações.
---
Mensagem
Permite a comunicação entre usuários envolvidos em uma doação, para combinar detalhes como entrega ou retirada.
Relacionamentos
É enviada por um usuário e destinada a outro.
Está associada a uma doação.
---
Localização
Relaciona a doação (e o usuário) a uma região, facilitando a combinação entre as pessoas e a busca por itens próximos.
Modelagem adotada por enquanto
A localização é tratada como informação da doação e do usuário (cidade e estado), e não como uma entidade própria. Veja os pontos em aberto abaixo.
---
Avaliação
Registra a experiência entre usuários após uma interação ou doação.
Relacionamentos
É feita por um usuário sobre outro usuário.
Está associada a uma doação.
---
Pontos em aberto
Itens que o grupo ainda precisa decidir. Devem ser resolvidos durante o Explore ou nas changes correspondentes, e não adivinhados pelo agente.
Localização: entidade própria ou apenas campos (cidade e estado) na doação e no usuário. Por ora, campos.
Status da doação: quais estados existem (por exemplo, disponível, reservada, concluída) e como a doação muda de um para outro.
Interesse e doador: se o doador escolhe um interessado e como isso aparece no sistema.
Mensagens: se são livres entre quaisquer usuários ou só entre doador e interessado de uma mesma doação.
Avaliação: quem pode avaliar quem e em que momento (por exemplo, só depois de a doação ser concluída).
Papéis: se haverá administração (moderação de doações e usuários) além do usuário comum.
Primeiras fatias de implementação sugeridas
O modelo é global, mas a implementação é incremental. A ordem natural de dependência é:
```text
Usuário e autenticação → Categoria → Doação → Interesse → Mensagem → Avaliação
```
Essa ordem é apenas uma sugestão de partida. A decomposição final em changes deve sair do Explore.