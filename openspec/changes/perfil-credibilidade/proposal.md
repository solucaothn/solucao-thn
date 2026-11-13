# Proposta: perfil-credibilidade

## Por quê

Quem vai buscar uma doação hoje vê, de quem doa, só o primeiro nome, a foto, a cidade e o Sobre. Não dá para saber se a pessoa já doou antes nem se o e-mail dela foi confirmado. Os contadores de doações já existem, mas só em “Minhas doações”, e a confirmação de e-mail no cadastro, publicada em novembro de 2026, ainda não deixa nenhum registro na conta.

Mostrar quantas doações a pessoa tem e já concluiu e um selo “E-mail verificado” verdadeiro dá mais confiança para pedir um item, sem expor dados privados.

## O que muda

- **Campo novo `email_verified` (bool) na tabela `user`.** O `signup_verify` passa a criar a conta já com o campo verdadeiro. Sem caminho para voltar a falso: o e-mail não pode ser trocado.
- **Marcação inicial das contas existentes,** feita uma vez só, de forma idempotente e auditável. Ficam verdadeiras só as contas criadas pela confirmação de e-mail, publicada em 2026-11-04. As anteriores ficam falsas e não ganham selo.
- **Contadores e selo nas respostas que já existem,** sem requisição a mais:
  - `GET auth/profile`, para a prévia de `/perfil/editar`;
  - `GET catalog/donations/mine`, que já tem os contadores e passa a trazer o e-mail da própria pessoa;
  - `GET catalog/donations/donor`, para o perfil público;
  - `GET catalog/donations/detail`, para o cartão “Quem doa”.
- **“Doações” e “Doações realizadas”:**
  - “Doações” soma as disponíveis e as reservadas, e “Doações realizadas” conta as concluídas;
  - passam a aparecer na prévia, no perfil público e no “Quem doa”;
  - “Minhas doações” continua com os mesmos dois números.
- **Selo “E-mail verificado”:**
  - tem ícone de verificado, texto “E-mail verificado” e contraste AA;
  - aparece em “Minhas doações”, na prévia, no perfil público e no “Quem doa”;
  - com o campo falso, não aparece nada: nunca “não verificado”.
- **E-mail no cartão de “Minhas doações”,** que só a própria pessoa vê, como no frame `Group 6` do Figma.
- **O e-mail continua fora** da prévia, do perfil público, do detalhe e de qualquer resposta pública.
- **Divisão do apply em duas partes:**
  - **Parte A:** o Xano, com o campo, o `signup_verify`, as quatro respostas, a marcação inicial e o teste real;
  - **Parte B:** o frontend, com os testes e a documentação.

### Fora do escopo

- Verificar depois o e-mail de contas antigas (reenviar código para quem se cadastrou antes da confirmação).
- Trocar o e-mail ou a senha pela tela de perfil.
- Avaliações, “Compartilhar link do perfil”, selo de telefone ou documento e indicador “Online”.
- Selo ou contadores no chat, nos cartões da home ou na lista de conversas.

## Capacidades

### Capacidades novas

Nenhuma. Os comportamentos novos cabem nas capacidades que já existem.

### Capacidades modificadas

- `user-account`:
  - a conta guarda se o e-mail foi verificado, e a verificação do cadastro marca esse campo;
  - a consulta do perfil devolve o selo e os contadores;
  - a prévia de `/perfil/editar` passa a mostrar os contadores e o selo, mas continua sem o e-mail.
- `donor-public-profile`:
  - a resposta pública traz os contadores e o selo;
  - a página passa a mostrá-los;
  - sai a proibição do selo.
- `donation-management`:
  - a listagem traz o e-mail da própria pessoa e o selo;
  - o cartão da pessoa mostra o e-mail e o selo;
  - sai a proibição dos dois.
- `donation-detail`:
  - a resposta pública traz os contadores e o selo de quem doa;
  - o cartão “Quem doa” mostra os dois;
  - sai a proibição do e-mail verificado.

## Impacto

- **Xano (`xano/`):**
  - `table/user.xs`;
  - `api/authentication/auth/signup_verify_POST.xs` e `profile_GET.xs`;
  - `api/catalog/catalog/donations/mine_GET.xs`, `donor_GET.xs` e `detail_GET.xs`;
  - uma task nova e temporária para a marcação inicial, que é a primeira task do projeto.
- **Banco:** um `ADD_FIELD` em `user` e a atualização única das contas confirmadas. Duas contagens novas por resposta no perfil, no perfil público e no detalhe.
- **Frontend (Reflex):**
  - `doafacil/editar_perfil.py`, `minhas_doacoes.py`, `perfil_doador.py`, `detalhe_doacao.py` e `perfil_publico.py`, que ganha o componente do selo e o dos contadores, compartilhados;
  - os testes dessas telas.
- **Scripts de teste real:** um novo para esta change e ajustes nas chaves esperadas de `teste_perfil_real.py`, `teste_minhas_doacoes_real.py` e `teste_editar_perfil_real.py`.
- **Documentação:** `docs/design/README.md` e `docs/guia-do-colaborador.md`.
- **Privacidade:**
  - o selo e os contadores ficam públicos (o perfil público e o detalhe não pedem login);
  - o número de doações reservadas passa a entrar, somado, no “Doações” público;
  - nenhum identificador nem e-mail novo sai em resposta pública.
