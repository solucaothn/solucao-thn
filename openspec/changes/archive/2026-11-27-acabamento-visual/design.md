# Design

## Contexto

As causas vêm da auditoria de 27/11/2026 (veja `proposal.md`). Tudo é de visual e de texto: nenhum estado, evento ou chamada ao Xano muda. O ajuste do detalhe da doação já está no código; esta change só alinha as specs com ele.

## Decisões

1. **Detalhe da doação (já feito).**
   - O cartão de resumo usa constantes (`SUMMARY_CARD_PADDING`, `SUMMARY_BUTTON_HEIGHT`, `DONOR_CONTACT_BUTTON_LABEL`) e `spacing="0"` com margens explícitas (8 px e 24 px), para que os valores fiquem no código e não dependam da escala do Radix.
   - O título usa `-webkit-line-clamp: 3`, que corta só no visual: o leitor de tela continua lendo o título inteiro.
   - “Descrição”, “Detalhes” e “Localização” usam o mesmo componente (`_section_heading`).

2. **Tabela da Privacidade.** A palavra quebra porque o `<main>` institucional tem `overflow_wrap="anywhere"`, e a célula de cabeçalho da linha herda isso. A célula passa a ter `overflow_wrap="normal"`, `word_break="normal"` e `min_width="120px"`. A tabela continua com `min_width` de 640 px e rolagem dentro do próprio contêiner. Descartado: tirar o `anywhere` do `<main>`, porque ele protege e-mails e URLs longos nas outras páginas.

3. **Seletor “Estado” do cadastro.**
   - No `rx.select` de alto nível, `height`, fundo, cor e borda ficam no `Select.Root` do Radix, que não vira elemento na página. Por isso eram ignorados, e o gatilho ficava com o visual padrão e cerca de 32 px.
   - O seletor passa a usar `rx.select.root` (com `name="state"`, `required` e `size="3"`, como antes), `rx.select.trigger` com a altura de 48 px, o fundo branco e a borda `#C8C8C8` dos outros campos, e os mesmos 27 itens.
   - O dado enviado pelo formulário não muda: o `name` continua no root.
   - Descartado: estilo por classe CSS, porque o `className` também ficava no root e não chegava à página.

4. **Botão do chat acima do selo.** No modo de produção, o selo “Built with Reflex” ocupa de 16 a 54 px a partir da borda inferior no computador (143 × 38 px) e de 16 a 46 px no celular (30 × 30 px), medido no navegador.
   - O botão sobe para 72 px (computador) e 60 px (celular) da borda inferior, mantendo 24 e 16 px da direita: `CHAT_FAB_BOTTOM` separado do `CHAT_FAB_RIGHT`.
   - O espaço livre no fim das páginas (`CHAT_FAB_CLEARANCE`) passa a ser a distância da borda inferior somada à altura do botão e à margem lateral: 60 + 56 + 16 = 132 px no celular e 72 + 56 + 24 = 152 px no computador.
   - Descartado: tirar o selo, porque o pedido é mantê-lo.

5. **Rodapé.** O `gap="4"` do `rx.flex` vai direto para o CSS sem unidade, e o navegador o ignora. Passa a ser `gap="16px"`. As colunas de links ganham `column_gap="12px"` e passam a ocupar `calc(50% - 6px)` no celular e `calc(25% - 9px)` no computador, para caber com o espaço.

6. **Perguntas em duas linhas.** `.AccordionTrigger` ganha `lineHeight: 1.35`. O botão herdava altura de linha 1 do Radix.

7. **“Entrar” e “Quero Doar”.**
   - “Entrar” passa a ter sempre `min_height="44px"` e `border_radius="6px"`, como o “Quero Doar”. Antes, os 44 px valiam só no celular.
   - O “Quero Doar” já tinha 44 px e 6 px.
   - O parâmetro `touch` de `account_control` fica sem efeito, mas é mantido na assinatura para não mexer nos lugares que o chamam.

8. **Título de Explorar.** `font_weight` passa de 400 para 700.

9. **“Boas-vindas”.** Só o texto do título do cartão de login muda.

10. **“Pessoas alcançadas” com 0.**
    - A estatística entra num `rx.cond` que a mostra quando `count_loading` está ativo, quando há `completed_error` ou quando `completed_count > 0`.
    - Assim ela some só quando o número carregado é 0.
    - O espaço entre as estatísticas vem do `spacing` do contêiner, então nada fica sobrando.

## Riscos / Compromissos

- **[O selo do Reflex mudar de tamanho numa versão nova]** → O botão ficaria embaixo do selo de novo. A medida está anotada aqui e na tarefa de conferência visual.
- **[Título muito longo cortado no cartão]** → Quem enxerga a tela não vê o fim do título. Leitores de tela leem o título inteiro, e a descrição continua completa abaixo da galeria.
- **[O `size="3"` do seletor mudar a fonte]** → Conferido nas capturas de 1280 e 360 px.

## Migração

Nenhuma: só frontend. Para voltar atrás, basta reverter os arquivos.
