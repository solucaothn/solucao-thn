# Design

## Contexto

Situação observada no código antes da mudança:

- **Seta de retorno.** Em `donation_creation_page()` (`doafacil/cadastro_doacao.py`), a seta `chevron-left` fica num `rx.box` com `max_width="1000px"`, `margin="0 auto"` e `padding="0 1.25rem"`. Em janelas mais largas que 1000 px, ela acompanha a borda de uma faixa centralizada e aparece solta, longe do canto. O wizard tem 360 px de largura e fica centralizado. A seta está fora do wizard e não muda entre as etapas; o problema é só de posição. No Figma (`docs/design/06-cadastro-de-doacao.png`), ela fica junto à borda esquerda, logo abaixo do cabeçalho.
- **Cor do texto digitado.**
  - Os campos “Nome do item” (`#donation-title`) e “Descrição” (`#donation-description`) recebem `color="#333333"` como estilo do componente.
  - O placeholder é forçado para `#333333` com opacidade 1 por regras globais em `rx.App(style=...)`, como exige a spec atual. Com isso, placeholder e texto digitado têm a mesma cor nominal.
  - Os dois campos são controlados (`value` + `on_change`), e por isso o Reflex os renderiza como `DebounceInput`, que envolve o campo do Radix. Os testes atuais confirmam esse tipo de componente.
  - No CSS do Radix Themes instalado, a cor do texto vem do elemento raiz (`.rt-TextFieldRoot` / `.rt-TextAreaRoot`, `color: var(--gray-12)`) e é herdada pelo `<input>` / `<textarea>`. Não existe regra própria de cor no elemento de texto, exceto em `:disabled` / `:read-only` (`--gray-a11`) e no preenchimento automático (`-webkit-text-fill-color: var(--gray-12)`).
  - A causa do texto “quase transparente” **não foi reproduzida** só lendo o código. As hipóteses, em ordem de probabilidade:
    1. Dentro do `DebounceInput`, o estilo `color` não chega ao elemento do Radix, e o texto herda `--gray-12` do tema. Se o tema seguir o modo escuro do sistema, esse cinza fica claro sobre o fundo branco.
    2. A cor chega ao elemento raiz, mas outra regra do tema vence a herança no elemento de texto.
  - As regras globais por `id` já funcionam para o placeholder (`#donation-title::placeholder`). Isso mostra que o `id` está no `<input>` / `<textarea>` real.

## Objetivos / Fora do escopo

**Objetivos:**
- Seta no canto superior esquerdo, logo abaixo do cabeçalho, igual nas cinco etapas e em qualquer largura.
- Texto digitado e colado escuro e opaco nos dois campos de texto do cadastro, qualquer que seja a causa entre as hipóteses acima.
- Lista dos outros formulários com o mesmo risco, para uma change futura.

**Fora do escopo:**
- Corrigir login, cadastro de conta, recuperação de senha e busca da home.
- Mudar o destino da seta ou os botões do rodapé do wizard.
- Mudar a cor dos prompts dos Selects e das preferências de contato. Só o placeholder dos dois campos de texto muda (decisão 4).

## Decisões

1. **Seta numa faixa de largura total, alinhada à esquerda.** Trocar o contêiner da seta por um `rx.box` com `width="100%"`, sem `max_width` e sem `margin="0 auto"`, com `padding="0.75rem 1.25rem 0"`. O recuo lateral de 1,25 rem (20 px) é o mesmo da área do wizard e cumpre a margem mínima de 16 px no celular. A seta continua fora do wizard, então não anima e não muda entre etapas, conforme o AGENTS.md (só o cartão central anima). `href="/"` e `aria_label="Voltar ao início"` ficam como estão.
   - *Alternativa descartada:* `position: absolute` / `fixed`. Pode sobrepor a barra de progresso em telas estreitas e tira a seta do fluxo de leitura.
   - *Alternativa descartada:* reaproveitar o `_back_link()` do detalhe da doação. Ele tem o mesmo defeito, com faixa centralizada de 1200 px, e mexer nele está fora do escopo.
2. **Cor do texto aplicada direto no elemento de texto, por `id`.** Acrescentar em `rx.App(style=...)` uma regra para `#donation-title, #donation-description` com `color: #1F1F1F`, `-webkit-text-fill-color: #1F1F1F` e `opacity: 1`. O seletor por `id` atinge o `<input>` / `<textarea>` real, como já acontece no placeholder, sem depender de o estilo do componente atravessar o `DebounceInput` ou de vencer a herança do tema. `-webkit-text-fill-color` cobre navegadores WebKit/Blink, onde essa propriedade pode se sobrepor a `color`. `#1F1F1F` é mais escuro que o placeholder (`#333333`), o que mantém a diferença entre texto digitado e exemplo sem mudar a regra dos placeholders. Manter também `color="#333333"` no componente, sem prejuízo.
   - *Alternativa descartada:* tirar `value`/`on_change` para fugir do `DebounceInput`. Mudaria o comportamento de estado do wizard (preservar valores entre etapas e reiniciar a cada entrada) e aumentaria o risco.
   - *Alternativa descartada:* fixar o tema do app em claro (`appearance="light"`). Seria uma mudança global, fora do escopo.
3. **Confirmação da causa no navegador antes de corrigir.** Uma pessoa reproduz o problema e anota a cor calculada (`color` e `-webkit-text-fill-color`) do `<input>` no DevTools, antes e depois da correção. Isso confirma ou descarta as hipóteses e valida a correção.

## Levantamento: outros formulários com o mesmo padrão (sem correção nesta change)

Pelo código, todos estes campos usam o mesmo padrão: `color="#333333"` no componente e nenhuma regra de cor no elemento de texto. O placeholder deles é `#6b6b6b`, então o texto digitado afetado seria até mais claro que o placeholder.

| Formulário | Campos (`id`) | Controlado (`DebounceInput`)? | Risco | Confirmado no navegador |
|---|---|---|---|---|
| Recuperação de senha, etapa de e-mail | `recovery-email` | Sim (`value` + `on_change`) | **Alto:** mesmo padrão do wizard | Não |
| Recuperação de senha, código e nova senha | `recovery-code`, `recovery-password`, `recovery-password-confirmation` | Não | Médio, se a hipótese 2 se confirmar | Não |
| Login | `login-email`, `login-password` | Não (só `on_change`) | Médio, se a hipótese 2 se confirmar | Não |
| Cadastro de conta | `signup-name`, `signup-email`, `signup-city`, `signup-password`, `signup-confirm-password` | Não | Médio, se a hipótese 2 se confirmar | Não |
| Home, busca (somente visual) | `public-home-search` | Não | Médio, se a hipótese 2 se confirmar | Não |

Resultado da tarefa 1.2: nenhum desses formulários mostrou texto claro no navegador. Não há correção pendente para eles.

## Ajuste posterior: placeholder

Depois da primeira verificação manual, surgiram dois pontos:

- **O placeholder herda o `-webkit-text-fill-color` do campo.** Um teste em Chrome headless, com uma página estática que reproduz as regras, mediu o `::placeholder` com `color` `rgb(51, 51, 51)`, mas `-webkit-text-fill-color` `rgb(31, 31, 31)`. Essa propriedade é herdada e vence o `color` na pintura, então o placeholder era desenhado na cor do texto digitado. Com `-webkit-text-fill-color` definido no próprio `::placeholder`, a medida passou a `rgb(107, 107, 107)` nas duas propriedades.
- **Decisão do grupo:** o placeholder dos dois campos de texto passa de `#333333` para `#6B6B6B`, igual aos outros formulários, para não parecer texto digitado. O contraste sobre branco é de cerca de 5,3:1, acima do mínimo AA (4,5:1). Os prompts dos Selects e as preferências de contato continuam `#333333`.

**Decisão 4:** as regras `#donation-title::placeholder` e `#donation-description::placeholder` passam a ter `color` e `-webkit-text-fill-color` em `#6B6B6B` e `opacity: 1`.

**Placeholder que não volta ao apagar:** na página estática, o placeholder volta normalmente depois de digitar e apagar, mesmo com a regra do `-webkit-text-fill-color`. Então essa regra sozinha não deixa o campo vazio. O JSX compilado do campo também está correto: com o estado vazio, `value` vira `""`. O que se confirmou é que o placeholder era pintado na cor do texto. Se o campo continuar vazio na tarefa 5.3, a suspeita restante é o `DebounceInput` com valor controlado: um valor antigo do estado chegando depois do apagamento, ou o componente sem repassar o valor vazio. Isso pede investigação com o React DevTools.

## Riscos / Trade-offs

- **Causa não confirmada.** Se a causa for outra, por exemplo uma regra de `opacity` no contêiner, a regra por `id` pode não bastar. A verificação manual com DevTools (tarefas 1.1 e 3.2) detecta isso antes de concluir.
- **Regras globais por `id`.** Elas dependem de os `id`s continuarem únicos. Hoje são, e os testes já checam esses `id`s.
- **Diferença entre placeholder e texto.** Resolvida pela decisão 4: `#6B6B6B` no placeholder contra `#1F1F1F` no texto.
- **Causa do campo vazio sem placeholder não reproduzida.** A correção da decisão 4 trata o efeito confirmado (placeholder com a cor do texto). Se o sintoma continuar, a tarefa 5.3 registra e a investigação segue pelo `DebounceInput`.
