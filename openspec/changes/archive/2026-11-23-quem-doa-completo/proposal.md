# Proposta: cartão “Quem doa” mais completo no detalhe

## Why

No detalhe da doação, o cartão “Quem doa” mostra os dados de quem doa (foto, nome, cidade, contadores e selo) numa lista corrida, e o acesso ao perfil é o cartão inteiro, com um “Ver perfil” discreto. A proposta é organizar o cartão em seções separadas por linhas e acrescentar há quanto tempo a pessoa está no site, usando só dados que o site já tem, para que quem se interessa pela doação tenha mais confiança em quem doa.

## What Changes

- **Topo:** a foto (ou a inicial) e o primeiro nome. Abaixo, “No DoaFácil desde <mês de ano>” com ícone de calendário e “Cidade, UF” com ícone de local.
- **Botão contornado “Ver perfil de quem doa”**, na largura toda do cartão, que leva ao perfil público. **Muda** o acesso ao perfil: antes o cartão inteiro era o link; agora o link é esse botão.
- **Divisor e seção “Doações”:** dois números com ícone, “Doações” (contador de ativas, que inclui as reservadas) e “Doações realizadas” (contador de concluídas), com os mesmos rótulos e o mesmo singular do perfil público e de Minhas doações.
- **Divisor e seção “Informações verificadas”:** “E-mail” com ícone de check verde, só quando o e-mail de quem doa está verificado. Sem verificação, a seção e o divisor não aparecem.
- **“Desde” sem mexer no Xano:** o detalhe não devolve a data de cadastro. A página lê o `member_since` do endpoint público do perfil de quem doa (`catalog/donations/donor`), que já passa pelo cache público de 60 s. Se esse pedido falhar, a linha “desde” some e o resto do cartão aparece normalmente. O detalhe não espera por esse pedido.
- Continuam fora: presença online, estrelas ou avaliações, doações canceladas, CPF e o e-mail de quem doa.

## Capabilities

### New Capabilities

(nenhuma)

### Modified Capabilities

- `donation-detail`: o requisito “Conteúdo do detalhe da doação” muda o conteúdo e o acesso do cartão “Quem doa”, e entra o requisito do “desde” vindo do perfil público, com o caso de falha.

## Impact

- `doafacil/detalhe_doacao.py`: o cartão `_donor_card` e o estado (`donor_member_since` e um evento que o carrega depois do detalhe).
- Reaproveita, sem mudança, `fetch_donor_profile` e `member_since_label` de `doafacil/perfil_doador.py` e o cache público (`cache_publico.DONOR`).
- `tests/test_donation_detail.py` e `tests/test_profile_photo.py`: os testes do cartão.
- `docs/design/README.md`: a descrição do cartão “Quem doa”.
- Sem mudança no Xano nem nas APIs. Quando o cache do perfil está vazio, abrir o detalhe faz um pedido a mais ao Xano. O mesmo pedido fica guardado para quem abrir o perfil em seguida.

## Fora do escopo

- A página do perfil público e seus componentes compartilhados (contadores e selo continuam como estão lá).
- Qualquer outra parte do detalhe, incluindo a galeria (change `galeria-detalhe`).
