# Proposal

## Why

A página de detalhe da doação já expõe o conteúdo público do item, mas ainda não atende ao fluxo de contato doador. O topo do card precisa mostrar ações que respeitem as decisões do produto e a segurança de dados: o contato por e-mail deve exigir login e nunca aparecer na resposta pública, enquanto o chat deve informar a preferência do doador sem revelar e-mail.

## What Changes

- Modificar o requisito de detalhe da doação para permitir os botões novos do topo do card (`Outros meios de comunicação` e `Chat`) sem permitir acesso ao perfil do doador, mantendo em vigor o restante dos cenários vigentes.
- Definir a regra de negócio para o endpoint autenticado de e-mail do doador no grupo Catalog: só responde quando a doação existe, está disponível e a preferência de contato é `E-mail`; caso contrário, retorna 404 genérico; sem login, 401.
- Definir o comportamento do frontend para a ação de `Outros meios de comunicação`: quando o usuário está logado e a preferência é `E-mail`, chama o endpoint com o token, abre `mailto:` com o e-mail codificado e assunto simples; quando a preferência é `Chat do DoaFácil`, exibe a mensagem informativa sem chamar o endpoint.
- Definir o comportamento do botão `Chat`: exibe a mensagem “O chat ainda não está disponível.” e não navega, com mensagens simples de erro para falha de rede ou 404.
- Garantir que a resposta pública do detalhe continue sem e-mail, usando o campo `contact_preference` já entregue pela API pública.
- Adicionar o aviso no passo 5 do cadastro de doação quando a preferência escolhida é `E-mail`: “Seu e-mail ficará disponível para pessoas logadas que quiserem falar com você.”
- Incluir testes `unittest` cobrindo redirect sem login, chamadas autenticadas, cenários de 401/404/erro de rede, ausência de e-mail no estado e preservação da resposta pública sem e-mail.

## Capabilities

### New Capabilities

- Nenhuma capability nova. Esta change modifica comportamentos já cobertos pelas specs existentes.

### Modified Capabilities

- `donation-detail`: ajuste do topo do detalhe da doação para permitir contato do doador por e-mail ou chat e restringir o acesso a perfil e a dados privados.
- `donation-creation`: aviso no passo 5 do cadastro quando a preferência de contato escolhida é `E-mail`.

## Impact

- **Xano / Catalog:** novo endpoint autenticado para retorno do e-mail do doador, com regra de disponibilidade e preferência; sem login retorna 401; sem e-mail disponível ou com preferência diferente retorna 404 genérico; só o e-mail do doador é devolvido, nunca nome, título, token, nem dados da conta em resposta pública.
- **Reflex / frontend:** página `/doacao/<id>` com topo de card ajustado conforme Figma; botão `Outros meios de comunicação` com fluxo de login/endpoint/mailto; botão `Chat` informativo; mensagens de erro consistentes com o site; e-mail não persistido no estado após o redirecionamento.
- **Testes:** novos testes `unittest` para fluxo autenticado, erro de rede, 401, 404, ausência de e-mail em estado e preservação da resposta pública sem e-mail.
- **Fora do escopo:** login, home, perfil público do doador, avaliações, histórico, presença online, verificação, mensagens funcionais e qualquer alteração em outras rotas do Catalog.

Este batch cria apenas os artifacts da change. A implementação do endpoint e da interface será feita na fase de apply, com pull do Xano somente após confirmação explícita do usuário, revisão do dry-run, aviso ao grupo e autorização antes de qualquer push real.
