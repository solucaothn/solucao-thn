# Design

## Context

Ver motivação e escopo em `proposal.md` e contratos observáveis em `specs/public-home-content/spec.md`.

A home atual está concentrada em `doafacil/doafacil.py`, usa componentes Reflex, carrega LINE Seed JP por stylesheet e mantém as cores creme `#FFF6E8`, verde `#168447` e cinza escuro `#333333`. A ilustração permanece no local atual, logo após as doações recentes; o conteúdo novo vem depois dela na ordem “Comece por aqui”, seção institucional e rodapé. O README de design e as imagens 02 e 03 fornecem os textos e a composição visual; o texto aprovado neste change prevalece sobre elementos incompatíveis presentes nas capturas. As decisões abaixo substituem a exclusão anterior da busca visual em “Comece por aqui”.

## Goals / Non-Goals

**Goals:**

- Estender a página pública existente com componentes Reflex, preservando identidade visual e responsividade.
- Manter o conteúdo e os controles independentes de páginas e fluxos ainda não implementados.
- Deixar o rodapé claramente distinto da área creme da home, usando fundo escuro e somente informações aprovadas para o DoaFácil.

**Non-Goals:**

- Criar rotas de catálogo, detalhes, cadastro de doação, autenticação, institucional ou políticas.
- Introduzir dependências, novos endpoints, carregamento remoto de imagens/vídeos ou qualquer alteração no Xano.
- Reproduzir conteúdo não aprovado da captura do Vakinha.

## Decisions

1. **Compor as seções na página inicial Reflex existente.** Reutilizar a página, stylesheet e identidade visual atuais reduz duplicação e mantém a home como uma única experiência. Uma página separada ou novos componentes de framework não são necessários para este escopo.

2. **Manter os controles como conteúdo sem navegação.** Os links de rodapé e “Saiba mais” podem preservar a aparência de link, e as setas dos dois primeiros cartões podem ser decorativas, mas nenhum controle recebe destino ou ação até que as respectivas páginas sejam aprovadas. “Desapego em grupo” fica visualmente indisponível com “Em breve” e sem seta.

3. **Usar os textos aprovados no README e na referência.** A primeira seção usa o título “Quer criar uma doação?”, a frase de apoio “Leva só alguns minutos: conte o que você quer doar e a gente conecta você a quem precisa.” e os textos dos cartões da imagem 02. A barra de busca é apenas visual, com campo de texto, seletores e botão inertes; não consulta backend, busca nem navega. Os cartões institucionais usam as categorias e títulos visíveis na imagem 03, inclusive “Conheça histórias de quem doou e quem recebeu” para Solidariedade, confirmado pelo grupo.

4. **Representar cartões institucionais com ícones e degradês, não mídia.** Usar ícones disponíveis por meio dos componentes Reflex, mantendo a paleta verde/cinza, em vez das fotos da captura. Vídeos, imagens dos cartões e dependências de ícones externas foram considerados e ficam fora do escopo aprovado.

5. **Aplicar layout fluido com coluna em telas estreitas.** Em telas amplas os cartões podem ocupar linhas lado a lado conforme a largura; em telas estreitas devem formar coluna, sem corte ou sobreposição. Os campos da barra visual também se empilham em telas estreitas. Isso preserva a leitura sem introduzir uma nova abordagem de frontend.

6. **Construir o rodapé apenas com conteúdo próprio aprovado.** Usar fundo escuro e logotipo; abaixo dele, posicionar “Fale conosco” e “Links rápidos” lado a lado, empilhando-os em telas estreitas. “Fale conosco” contém somente “Clique aqui para falar conosco”, sem navegação. Os links rápidos mantêm a lista exata dos oito links em tamanho reduzido, seguidos da linha acadêmica. Não acrescentar horário, e-mail, telefone, redes sociais ou itens legados do Vakinha removidos pela decisão do grupo.

7. **Manter a ilustração integrada ao fim da seção de doações.** Exibi-la em largura total, como último elemento da seção, sem margem ou faixa creme entre a imagem e “Comece por aqui”.

8. **Compor a primeira dobra como uma área de viewport.** Agrupar cabeçalho, destaque, contagem/doações recentes e ilustração numa coluna com `min-height: 100vh`; o conteúdo central cresce e ocupa o espaço livre e a ilustração permanece no fim da área. Quando o conteúdo excede a viewport, o contêiner cresce naturalmente em vez de aplicar altura fixa ou recortar elementos. “Comece por aqui” é irmão seguinte dessa área e não pode aparecer na primeira tela.

9. **Dar respiro e hierarquia consistentes à seção de entrada.** Usar padding vertical próximo de `5rem`; controlar os espaços entre etiqueta/título (`0.75rem`), título/frase (`1rem`), frase/cartões (`2.5rem`) e cartões/busca (`3rem`). Cartões usam aproximadamente `1.5rem` de gap e `2rem` de padding. O conteúdo (ícone, título e descrição) começa alinhado no topo em cada cartão, e seta/etiqueta é mantida no rodapé por uma composição interna flexível.

10. **Manter a busca visual legível e ativa.** Campo e seletores ficam com fundo branco, borda cinza clara e texto legível; são apenas visuais quanto à busca, sem handler que execute filtro ou navegação.

11. **Preservar o arquivo original do logotipo no rodapé.** Usar `/logo.svg` como no cabeçalho, sem filtro CSS ou recoloração. O contraste no fundo escuro deve ser observado e relatado, não corrigido com mudança de cor não aprovada. Reduzir títulos do rodapé para cerca de `0.95rem`, links e textos para `0.8rem`, com linhas compactas; “Clique aqui para falar conosco” não recebe sublinhado.

## Risks / Trade-offs

- [A imagem de referência contém elementos herdados e diferentes do conteúdo aprovado] → tratar os textos e exclusões registrados no README como fonte normativa e validar os itens visíveis contra a spec.
- [Links com aparência interativa, mas sem destino, podem sugerir navegação] → manter explicitamente os controles inertes nesta versão e não usar hrefs fictícios.
- [A quantidade de cartões e controles pode exceder o espaço em telas estreitas] → verificar disposição em coluna e legibilidade em viewport estreita durante a implementação.

## Migration Plan

1. Acrescentar os componentes das três seções à home existente, sem mudar a integração com Xano.
2. Executar os testes Reflex e verificar responsividade, conteúdo e ausência de navegação.
3. Não há migração de dados nem plano de rollback de backend; a reversão consiste em remover os componentes e estilos introduzidos por esta change.
