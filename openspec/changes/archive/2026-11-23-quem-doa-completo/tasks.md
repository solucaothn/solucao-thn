# Tarefas

Os comandos `git` e `xano` são do Higor. Esta change não toca no Xano. Arquive a `galeria-detalhe` antes desta (as duas modificam o mesmo requisito).

## 1. “Desde” vindo do perfil público

- [x] 1.1 Acrescentar `donor_member_since` ao `DonationDetailState`, zerado em `load_donation`, e o helper `_fetch_donor_member_since` (import tardio de `perfil_doador`, `fetch_donor_profile` com página 1 e `member_since_label`) que devolve `""` em qualquer falha do perfil (decisões 1 a 3). Verificação: testes com `httpx.MockTransport` conferem “outubro de 2020” para `member_since: "2020-10"` e `""` para 404, 429, 500, erro de rede e `member_since` inválido.
- [x] 1.2 Criar o evento `load_donor_since`, devolvido por `load_donation` só quando o detalhe carrega, que grava o texto apenas se `donation_id` não mudou (decisão 1). Verificação: testes conferem que `load_donation` devolve o evento no sucesso e nada no erro, que o evento grava o texto e que ele não grava com a doação trocada; e um teste confere que duas leituras dentro de 60 s fazem um pedido só ao perfil.

## 2. Cartão em seções

- [x] 2.1 Reescrever `_donor_card` e `_donor_card_content`: `rx.box` no lugar do link; topo com avatar de 48 px, nome, “No DoaFácil desde …” com `calendar` (só com o texto) e “Cidade, UF” com `map-pin`; botão contornado “Ver perfil de quem doa” como link para `/doacao/<id>/quem-doa`, largura toda, 44 px e `aria-label` “Ver perfil de quem doa, <nome>”; divisor e seção “Doações” com “Doações” e “Doações realizadas” (os rótulos do perfil público, no singular com 1); divisor e seção “Informações verificadas” com “E-mail” e `circle-check`, só com o e-mail verificado (decisões 4 e 5). Verificação: os testes do cartão em `tests/test_donation_detail.py` e `tests/test_profile_photo.py` são ajustados e conferem os textos, os ícones, o `rx.cond` das duas partes opcionais, o link único com o id da doação, os 44 px, o foco visível, a ausência de e-mail, avaliações, online, canceladas e CPF, e que o cartão não é mais um `Link`.

## 3. Documentação e verificação

- [x] 3.1 Atualizar em `docs/design/README.md` a descrição do cartão “Quem doa” e o item “Cartão ‘Quem doa’ como link”. Verificação: o texto bate com a delta.
- [x] 3.2 Rodar a suíte inteira e compilar o app. Verificação: `python -m unittest discover -s tests` passa e `reflex compile` termina sem erro.
- [ ] 3.3 Roteiro manual (para o Higor): abrir uma doação de alguém com e-mail verificado e outra sem, conferir as seções, o “desde”, o botão levando ao perfil e, em 360 px, a ausência de rolagem horizontal; com o Xano fora do ar só para o perfil (ou com 429), conferir que a linha “desde” some e o resto aparece.
