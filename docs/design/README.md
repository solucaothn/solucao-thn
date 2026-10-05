# Design do DoaFácil

Link do Figma: https://www.figma.com/design/l4MoQJUROh7b7gY3vCFTC0/doafacil?node-id=73-105&t=wvbRRiL16TnYnhQA-0

As imagens desta pasta são a referência visual do frontend (Reflex). O texto abaixo descreve cada tela e registra as decisões tomadas. Em caso de dúvida entre a imagem e este texto, vale o texto.

## Identidade visual

- Cor principal: verde. Fundo das páginas: creme claro. Textos em cinza escuro.
- Logotipo "doafácil" (coração com mãos) e ilustração de pessoas no rodapé da home.
- As cores exatas e as fontes devem ser extraídas do Figma ao implementar.

## Telas prontas

### 01-home.png — Tela inicial

- Cabeçalho: logotipo, links **Explorar Doações**, **Como funciona** e **Categorias**, botão **Entrar** e botão **Quero Doar**.
- Frase de destaque: "Doar é fácil. No DoaFácil, o que sobra em você vira recomeço para alguém."
- Estatística: "Doações em circulação".
- Seção **Doações mais recentes**: cartões com foto, etiqueta **NOVO**, título, **Condição** do item (Ótimo, Bom) e botão **Acessar**.
- Ilustração de pessoas na parte de baixo.

### 02-comece-aqui.png — Cartões de entrada e busca

- Etiqueta "COMECE POR AQUI" e título.
- Três cartões:
  - **Para você mesmo** (quem quer receber): escolher um item disponível e receber de alguém que está desapegando. Leva ao catálogo.
  - **Ajude quem precisa** (quem quer doar): cadastrar um objeto que não se usa mais. Leva ao formulário de doação e exige login.
  - **Desapego em grupo**: doar vários itens de uma vez. **Fora do MVP**; exibir como "Em breve" ou omitir.
- Barra de busca: campo de texto "Buscar doações", filtro **Categoria**, filtro **Localização** e botão **Buscar**.

### 03-secao-institucional-e-rodape.png — Seção institucional e rodapé

**Fora da change `home-publica-doacoes-recentes`. Será uma change própria.**

- Título "Doar no DoaFácil é simples e seguro." e frase de apoio.
- Quatro cartões com imagem, ícone, categoria, título e link "Saiba mais": Solidariedade, Segurança, Nossa missão e Passo a passo.
- Desejo do grupo: o carrossel de cartões poderá ter vídeos no futuro. Usar vídeos incorporados de um link (por exemplo, YouTube), sem versionar arquivos de vídeo no Git. Na primeira versão, imagens.
- Os destinos dos "Saiba mais" não existem ainda.
- Rodapé em fundo escuro, com logotipo, "Fale conosco" e colunas de links rápidos.

A confirmar com o grupo antes de implementar (vieram da referência do Vakinha e podem não se aplicar): selo de segurança, CNPJ e cidade, horário de atendimento, "Busca por recibo", "Verificação de links" e o cartão "Conheça histórias de quem doou e quem recebeu".

## Telas ainda sem desenho

Login e cadastro, catálogo (Explorar Doações), detalhe da doação, formulário de cadastro da doação, Como funciona, Categorias.

## Referência de estrutura (Vakinha)

O site do Vakinha serve só de inspiração para a organização das páginas. Não copiar marca nem textos, e não incluir o que não se aplica ao DoaFácil: valores em reais, sorteios, avaliações de loja de aplicativos e botões de download de app (o projeto é uma plataforma web).

Aproveitar a ideia de:
- rodapé em colunas, com links rápidos, contato e redes sociais;
- cartões de escolha com ícone, título e frase curta.

## Decisões tomadas

1. A **localização** da doação é a cidade e o estado do perfil do doador, copiados na hora de cadastrar a doação.
2. A barra de busca pertence à página **Explorar Doações**. A tela "Comece por aqui" é a porta de entrada.
3. A etiqueta **NOVO** vale para doações criadas nos últimos 7 dias.
4. A estatística "Pessoas alcançadas" **não entra** na primeira versão. Só "Doações em circulação".
5. **Desapego em grupo** (vários itens de uma vez) fica fora do MVP.
6. O rótulo do estado do item é **Condição** (Ótimo, Bom, Regular), para não confundir com o estado geográfico nem com o status da doação.

## O que o design exige do backend (Xano) e ainda não existe

- **Foto da doação:** campo de imagem na doação.
- **Condição do item:** campo com os valores Ótimo, Bom e Regular.
- **Localização da doação:** cidade e estado guardados na doação.
- **Contagem de doações em circulação:** endpoint público que retorne a quantidade de doações disponíveis.
- **Listagem pública:** a home e o catálogo devem poder ser vistos sem login. Verificar se o endpoint de listagem atual já permite isso.

## Telas (imagens)

![Tela inicial](01-home.png)

![Comece por aqui](02-comece-aqui.png)

![Seção institucional e rodapé](03-secao-institucional-e-rodape.png)