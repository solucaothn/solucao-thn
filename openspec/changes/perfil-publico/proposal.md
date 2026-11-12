# Proposta

## Por quê

No detalhe da doação, quem tem interesse vê só o primeiro nome e a cidade de quem doa. Não há como ver as outras doações disponíveis da mesma pessoa, o que ajudaria a combinar mais de um item numa só retirada. O Figma já tem a tela do perfil público, nos frames `perfil-doador-02` (sem doações) e `perfil-doador-01` (com 6 doações, dentro do grupo `Group 8`).

## O que muda

- **Nova rota `/doacao/<id>/quem-doa`:** o perfil é aberto a partir de uma doação.
  - A spec do detalhe proíbe o frontend de receber `owner_id`, então a doação é a chave do perfil.
  - O cartão “Quem doa” do detalhe vira um link para essa rota.
- **Novo endpoint público no Xano**, sem login, por `donation_id`:
  - devolve só o primeiro nome, a cidade e a UF, “membro desde” (mês e ano) e as doações **disponíveis** dessa pessoa, paginadas de 12 em 12;
  - nunca devolve e-mail, sobrenome ou identificadores de usuário;
  - responde com o 404 genérico para doação inexistente ou indisponível;
  - faz uma requisição por página.
- **Página do perfil** (frames do Figma):
  - “Voltar à doação” na linha do logotipo, em `#007A42`;
  - faixa branca com um círculo com a inicial, o primeiro nome, “Cidade, UF” e “No DoaFácil desde <mês> de <ano>”;
  - “Doações disponíveis”, com o contador “N itens” e os mesmos cards da home (foto, título, condição, NOVO, Acessar);
  - paginação quando houver mais de 12;
  - estado vazio com “Nenhuma doação disponível no momento” e o link “Explorar outras doações”, que leva à home por enquanto;
  - animação de entrada, contraste AA e layout de celular.
- **Apply em duas partes:** primeiro o Xano, com teste real em script; depois o frontend.

### Do Figma, o que não entra

- A foto de perfil: fica só o círculo com a inicial.
- O selo “E-mail verificado”.
- O botão de chat e as avaliações.

## Fora do escopo

- Perfil por usuário (`/perfil/<id>`) e qualquer forma de o frontend receber o id de quem doa.
- Doações reservadas ou concluídas no perfil.
- Busca e filtros dentro do perfil.
- Uma página “Explorar doações”: o link vai para a home até ela existir.

## Capacidades

### Novas capacidades

- `donor-public-profile`: a consulta pública do perfil de quem doa a partir de uma doação, com os dados permitidos e as doações disponíveis paginadas, e a página `/doacao/<id>/quem-doa`.

### Capacidades modificadas

- `donation-detail`: o requisito “Conteúdo do detalhe da doação” deixa de proibir o acesso ao perfil. O cartão “Quem doa” passa a ser um link para o perfil público; os demais itens proibidos continuam proibidos.

## Impacto

- **Xano:** um endpoint novo, `xano/api/catalog/catalog/donations/donor_GET.xs`, no grupo Catalog. Não muda nenhuma tabela.
- **Frontend:**
  - um módulo novo, `doafacil/perfil_doador.py`, com o cliente, o estado e a página;
  - a rota nova em `doafacil/doafacil.py`;
  - o cartão “Quem doa” em `doafacil/detalhe_doacao.py`;
  - um cabeçalho com voltar configurável em `doafacil/chat.py`, a partir do `back_home_header()`;
  - o `donation_card` e a regra do NOVO da home, reutilizados.
- **Script:** `scripts/teste_perfil_real.py`, para o teste real do endpoint.
- **Testes:** `tests/test_donor_profile.py` e ajustes em `tests/test_donation_detail.py`.
- **Documentação:** `docs/design/README.md`, com uma seção nova sobre o perfil público.
