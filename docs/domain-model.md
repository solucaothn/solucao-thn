# Domain Model — DoaFácil

## Usuário

Representa uma pessoa cadastrada na plataforma, que pode atuar como doador e/ou interessado.

### Principais informações
- nome;
- e-mail;
- localização associada.

### Relacionamentos
Um usuário pode cadastrar várias doações.
Um usuário pode demonstrar interesse em várias doações.
Um usuário pode trocar mensagens com outros usuários.
Um usuário pode receber e enviar avaliações.

## Doação

Representa um item oferecido por um usuário para doação.

### Principais informações
- título;
- descrição;
- categoria;
- localização;
- status (disponível, reservada, concluída).

### Relacionamentos
Uma doação pertence a um único usuário (doador).
Uma doação pertence a uma categoria.
Uma doação pode receber vários interesses.

## Categoria

Representa o tipo de item sendo doado (ex: roupas, alimentos, móveis).

### Principais informações
- nome.

### Relacionamentos
Uma categoria pode estar associada a várias doações.

## Interesse

Representa a manifestação de um usuário sobre uma doação específica.

### Principais informações
- usuário interessado;
- doação relacionada;
- data da manifestação.

### Relacionamentos
Um interesse pertence a um único usuário e a uma única doação.

## Mensagem

Representa uma comunicação trocada entre dois usuários a respeito de uma doação.

### Principais informações
- remetente;
- destinatário;
- conteúdo;
- doação relacionada.

### Relacionamentos
Uma mensagem pertence a dois usuários (remetente e destinatário) e, geralmente, a uma doação.

## Localização

Representa a localização geográfica de um usuário ou de uma doação, usada para aproximar doador e interessado.

### Principais informações
- cidade;
- estado/região.

### Relacionamentos
Uma localização pode estar associada a um usuário ou a uma doação.

## Avaliação

Representa a avaliação feita por um usuário sobre outro, após a conclusão de uma doação.

### Principais informações
- usuário avaliador;
- usuário avaliado;
- doação relacionada;
- nota e comentário.

### Relacionamentos
Uma avaliação está associada a dois usuários (avaliador e avaliado) e a uma doação.

> **Nota:** os relacionamentos e atributos acima são um ponto de partida com base nas 7 tabelas já definidas. Ajuste conforme o grupo detalhar melhor as regras (ex: se uma doação pode ter vários interesses simultâneos ou só um após ser "reservada").
