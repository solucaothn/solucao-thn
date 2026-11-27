# Design

## Contexto

As duas funções do Xano (`Signup/send_confirmation_code` e `Password Recovery/send_recovery_code`) recebem `recipient` e `code` (seis dígitos, como texto) e montam o corpo do SendGrid com um único conteúdo `text/plain`. O resto da função (o `api.request` e a `precondition` do status) não muda. A validade real do código é de 600 s nos três pontos que o geram: `auth/signup`, `auth/signup_resend` e `reset/request_code`.

O campo de código do site só aceita seis dígitos seguidos (`login.py`, `re.fullmatch(r"\d{6}", …)`). Um “482 913” colado com espaço seria recusado.

## Objetivos / Não objetivos

**Objetivos:** HTML seguro para e-mail que fique igual ao modelo; o mesmo texto em `text/plain`; uma única fonte para o HTML (o `.xs`), com prévias geradas a partir dela.

**Não objetivos:** modo escuro próprio; imagens além do logotipo; qualquer mudança de lógica.

## Decisões

1. **Modelos entre `"""` com marcadores.** O HTML e o texto simples ficam em blocos de texto de várias linhas (`"""…"""`), o mesmo formato que o Xano usa nos arquivos que exporta. O código entra no lugar de marcadores (`{{CODIGO}}`, `{{CODIGO_INICIO}}`, `{{CODIGO_MEIO}}`, `{{CODIGO_FIM}}`) com `|replace`. Assim, o HTML não precisa de aspas escapadas e fica igual ao que se abre no navegador. Alternativas descartadas:
   - concatenar com `~`: o XanoScript não aceita continuar a expressão na linha seguinte (o validador recusa);
   - uma lista de textos com `|join:""`: é válida, mas obriga a escapar todas as aspas do HTML.

2. **3 + 3 dígitos só com CSS.** O código é dividido com `substr` em três partes: os dois primeiros dígitos, o terceiro e os três últimos. O espaço entre os grupos vem de um `letter-spacing` maior só no terceiro dígito (8 px nos outros, 28 px nele). Assim não existe caractere de espaço: copiar dá “482913”, e o `letter-spacing` funciona também no Outlook do Windows, que ignora `padding` e `margin` em `<span>`. Alternativas: espaço normal ou `&nbsp;` (quebra a cópia), duas células de tabela (a cópia ganha uma tabulação) e `padding` no `<span>` (o Outlook ignora).

3. **Texto simples com o código junto.** No `text/plain` não há CSS. Por isso, o código vai sem espaço (“482913”), para colar direto no site. Os demais textos são os mesmos do HTML.

4. **Ordem do conteúdo: `text/plain` e depois `text/html`.** É a ordem que o SendGrid exige quando há as duas versões.

5. **Estrutura do HTML.**
   - Tabela externa com 100% de largura e fundo creme (`#FFF6E8`, o creme do site), também em `bgcolor`. Dentro dela, uma tabela de 600 px com `width="600"` e `max-width:600px; width:100%`, para encolher no celular. O texto fica numa coluna interna de 472 px (`max-width:472px; width:100%`), como no modelo, que deixa margem dos dois lados no computador e usa a largura toda no celular. A coluna é uma tabela, não `padding`, porque o Outlook não respeita `padding` em porcentagem.
   - Todo o estilo é inline, sem `<style>`, porque alguns leitores removem o bloco.
   - Fontes `Helvetica, Arial, sans-serif`.
   - Título `#0B5A2E`, código `#168447` (o verde do cabeçalho) e cartão `#F1F3F2` com borda `#8E9490`.
   - Os cantos arredondados ficam de enfeite: o Outlook do Windows mostra cantos retos.
   - Um texto de pré-visualização (preheader) oculto, “O código expira em 10 minutos.”, aparece na lista de mensagens. Ele não leva o código.

6. **Logotipo por URL absoluta.** O `<img>` usa `src="https://raw.githubusercontent.com/solucaothn/solucao-thn/main/assets/email/logo-email.png"`, `width="160"`, `height="58"`, `alt="DoaFácil"` e `display:block; border:0`. O arquivo tem 320 × 116, o dobro de 160 × 58, para ficar nítido em telas de alta densidade. O texto alternativo vai em verde e negrito, para quando o leitor bloqueia imagens. O payload não leva anexos. Alternativas descartadas:
   - logotipo embutido por `cid:` (anexo inline): foi testado e voltou atrás, porque no Gmail aparecia quebrado na primeira visualização e ainda aparecia como anexo no fim da mensagem;
   - `data:` URI no `src`: o Gmail e o Outlook não mostram.

7. **Prévias geradas a partir dos `.xs`.** O script `scripts/gerar_previas_emails.py` lê o HTML do `.xs`, troca as partes do código por um exemplo (“482913”) e a URL do logotipo pelo arquivo local (para mostrar a versão atual, mesmo antes de ela chegar à `main`) e grava `docs/emails/confirmacao-cadastro.html` e `docs/emails/redefinicao-senha.html`. Um teste confere que as prévias estão iguais ao que o script gera. Assim, a prévia não fica diferente do e-mail real.

## Riscos / Compromissos

- [A `main` ainda tem o logotipo antigo (480 × 174)] → Até a versão nova chegar à `main`, o e-mail mostra a antiga, reduzida para 160 × 58 (mesma proporção). O envio é do Higor.
- [O leitor bloqueia imagens externas até a pessoa liberar] → O texto alternativo “DoaFácil”, em verde e negrito, ocupa o lugar do logotipo.
- [O Gmail corta mensagens grandes (“[Mensagem cortada]”)] → O HTML tem cerca de 3,5 KB, e um teste garante que ele fica abaixo de 20 KB. O corte visto no Gmail não vem do tamanho do HTML.
- [O modo escuro do Gmail e do Outlook pode inverter as cores] → As cores têm contraste suficiente nos dois sentidos. Um tema escuro próprio fica de fora.
- [O texto pode sair diferente do HTML] → Um teste confere que os textos do modelo estão nas duas versões das duas funções.

## Migração

O Higor envia os `.xs` ao Xano pelo fluxo de sempre (`push --dry-run` e depois `push`). Para voltar atrás, basta enviar as versões anteriores das duas funções. Não há dados a migrar.
