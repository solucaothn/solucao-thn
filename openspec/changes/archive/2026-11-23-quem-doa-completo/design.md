# Design: quem-doa-completo

## Context

O cartão “Quem doa” (`_donor_card` em `doafacil/detalhe_doacao.py`) hoje é um `rx.link` que envolve tudo: avatar e nome, cidade, `donation_counts`, `verified_badge` e um “Ver perfil ›”. Os dados vêm do detalhe (`donor_first_name`, `donor_photo`, `donor_counts`, `donor_email_verified`). A cidade e a UF são as da doação.

O detalhe não traz a data de cadastro. O perfil público (`fetch_donor_profile` em `doafacil/perfil_doador.py`) traz `member_since` (`AAAA-MM`), já passa pelo cache público de 60 s (`cache_publico.DONOR`, chave = endpoint com `page=1`), e `member_since_label` já formata “outubro de 2020”. `perfil_doador` importa de `detalhe_doacao`, então o caminho contrário em nível de módulo criaria um import circular.

## Goals / Non-Goals

**Goals:**
- O cartão em seções, com o botão de perfil e o “desde”, sem mudar o Xano.
- O detalhe aparece assim que o próprio detalhe chega; o “desde” vem depois.

**Non-Goals:**
- Mudar a página do perfil público, `donation_counts` ou `verified_badge` (continuam usados lá).
- Novo endpoint ou campo no Xano.

## Decisions

1. **“Desde” num segundo evento.** Quando o detalhe carrega, `load_donation` devolve o evento `load_donor_since`, e o Reflex o roda em seguida. Esse evento lê o perfil (página 1) e grava `donor_member_since` com o texto pronto (“outubro de 2020”). Antes de gravar, confere se `donation_id` ainda é o mesmo, para não mostrar o “desde” da doação anterior. `load_donation` zera o campo. Alternativa descartada: buscar o perfil dentro de `load_donation`, o que atrasaria a página inteira quando o cache está vazio.

2. **Mesma chave de cache do perfil.** Usar `fetch_donor_profile(client, base_url, donation_id)` com `page=1` reaproveita a mesma entrada do cache que a página do perfil usa. Abrir o perfil logo depois não faz pedido novo.

3. **Falha some em silêncio.** `DonorProfileNotFoundError`, `DonorProfileRateLimitError`, `DonorProfileServiceError`, `httpx.HTTPError` e `ValueError` deixam `donor_member_since = ""`, e a linha não aparece. Não há mensagem nem “Tentar de novo”, porque a linha é complementar. `asyncio.CancelledError` não é capturado (navegação cancelada não é falha). O import de `perfil_doador` fica dentro de um helper (`_fetch_donor_member_since`) para evitar o import circular.

4. **O cartão deixa de ser link; o botão é o link.** Um botão dentro de um link é HTML inválido, então o contêiner vira uma `rx.box` e o link passa a ser o botão contornado “Ver perfil de quem doa”: largura toda, 44 px de altura mínima, borda e texto verdes `#007A42`, foco visível. O `aria-label` é “Ver perfil de quem doa, <primeiro nome>”, que começa pelo texto visível (WCAG 2.5.3) e mantém o nome.

5. **Seções e ícones.** Os divisores são linhas de 1 px `#D9D9D9`. Os títulos das seções são `h3`: “Doações” e “Informações verificadas”. Os ícones vêm do Lucide e são decorativos (`aria-hidden`): `calendar`, `map-pin`, `package` (Doações), `package-check` (Doações realizadas) e `circle-check` verde `#166B3B` (E-mail). Os números usam o verde `#166B3B` dos contadores do perfil, que têm contraste AA sobre o branco. Sem e-mail verificado, o divisor e a seção não são renderizados (`rx.cond`), em vez de mostrar “E-mail não verificado”, como hoje o selo, que só aparece quando verificado.

6. **Rótulos do perfil público.** O detail só tem `donor_counts.active`, que soma disponíveis e reservadas, então “Disponíveis” seria impreciso. Os números usam `ACTIVE_LABELS` e `COMPLETED_LABELS` de `perfil_publico` (“Doações”/“Doação” e “Doações realizadas”/“Doação realizada”), iguais aos do perfil público e de Minhas doações.

## Risks / Trade-offs

- [Um pedido a mais ao Xano quando o cache do perfil está vazio] → Fica guardado 60 s para todos e é o mesmo que o perfil usa. Com 429, a linha some e nada é repetido.
- [A resposta do perfil traz até 12 doações que o detalhe não usa] → A resposta é a mesma do perfil e fica no cache; aceitável para não mexer no Xano.
- [Esta change e a `galeria-detalhe` modificam o mesmo requisito] → A delta daqui parte da versão da `galeria-detalhe`; arquive a `galeria-detalhe` primeiro.
