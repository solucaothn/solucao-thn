# Design

## Context

Veja `proposal.md` para a motivação e `specs/donation-detail/spec.md` para os requisitos observáveis desta mudança. A página pública do detalhe já deve exibir título, condição, descrição, categoria, cidade/UF, modalidade de entrega, preferência de contato e cartão do doador com somente primeiro nome e cidade/UF. O Xano já expõe a resposta pública e a API de login, e o frontend Reflex já usa estados para lidar com carregamento e erro. O endpoint autenticado para e-mail do doador não existe ainda.

## Goals / Non-Goals

**Goals:**
- Permitir a ação de contato do doador no topo do detalhe conforme o Figma, preservando a resposta pública.
- Implementar o fluxo de login e os casos de 401/404/erro de rede no frontend.
- Definir a rota e os controles do endpoint autenticado de e-mail do doador no grupo Catalog.
- Incluir o aviso do cadastro de doação quando a preferência escolhida for `E-mail`.

**Non-Goals:**
- Exibir o perfil público do doador, chat funcional, histórico, avaliações, presença online ou qualquer dado privado fora do escopo.
- Alterar a rota pública `/catalog/donations/detail`, seu contrato, ou o estado de login da aplicação.

## Decisions

### Endpoint autenticado de e-mail do doador

Adicionar um novo endpoint do grupo Catalog, com rota estática e nome claro, evitando conflito com as rotas `recent`, `count`, `status`, `detail` e `publish`. A rota escolhida é `GET /catalog/donations/contact-email`. O nome deixa explícito que o serviço retorna somente o e-mail de contato de quem doa e não conflita com as rotas existentes. A rota será autenticada, aceitará `donation_id` e responderá com HTTP 401 sem sessão válida. Depois de confirmar que a doação existe e está disponível, responderá com HTTP 403 e uma mensagem própria, sem e-mail, quando pertencer à pessoa autenticada; responderá com HTTP 404 genérico quando a doação não existir, não estiver disponível ou tiver preferência `Chat do DoaFácil`; e responderá com HTTP 200 e somente `{ "email": "..." }` quando a doação disponível pertencer a outra pessoa e a preferência for `E-mail`.

**Alternativas consideradas:** `GET /catalog/donations/contact` e `GET /catalog/donations/email` foram descartadas por serem mais vagas e mais sujeitas a conflitos semânticos com outros endpoints do mesmo grupo; `GET /catalog/donations/contact-email` deixa o objetivo explícito e evita qualquer colisão com as rotas existentes.

### Tratamento da pessoa que clicou na própria doação

A resposta pública do detalhe não contém `owner_id`, e o frontend nunca recebe nem guarda esse campo. Portanto, quando uma pessoa autenticada clica em “Outros meios de comunicação” e a preferência é `E-mail`, o frontend chama o endpoint sem tentar determinar localmente se a doação é própria. Após confirmar no backend que a doação existe e está disponível, o endpoint compara o responsável da doação com a pessoa autenticada. Se forem a mesma pessoa, responde com HTTP 403 e uma mensagem própria, sem devolver e-mail; o frontend traduz o 403 para “Esta é a sua doação.”. Para doação inexistente, indisponível ou com preferência `Chat do DoaFácil`, o endpoint continua respondendo com o mesmo 404 genérico; sem sessão válida, responde 401.

### Frontend do detalhe

No Reflex, a página `/doacao/<id>` manterá a resposta pública em um estado separado do detalhe privado. O botão `Outros meios de comunicação` executará a seguinte lógica:
- sem autenticação → redireciona para `/login` sem chamar a API;
- com autenticação e `contact_preference == "E-mail"` → chama `GET /catalog/donations/contact-email` com o token da sessão, sem enviar nem depender de `owner_id`; ao receber HTTP 403, mostra “Esta é a sua doação.”;
- com autenticação e `contact_preference == "E-mail"` e resposta válida HTTP 200 → abre `mailto:` com o e-mail codificado e assunto simples com o título da doação;
- com autenticação e `contact_preference == "Chat do DoaFácil"` → mostra a mensagem “Quem doa prefere contato pelo chat.”;
- em erro de rede, HTTP 401, HTTP 404 ou resposta inválida → mostra uma mensagem simples de erro, no mesmo estilo visual do site.

O botão `Chat` sempre mostra a mensagem “O chat ainda não está disponível.” e não navega. O e-mail não é persistido em estado após o redirecionamento; o valor temporário usado para compor o `mailto:` é descartado imediatamente após iniciar o redirecionamento.

### Controle de privacidade do payload público

A resposta pública do detalhe continua com o mesmo contrato atual, sem e-mail e sem dados privados, conforme a spec principal. A página usa `contact_preference`, já devolvido pela API pública, para renderizar o texto de preferência de contato. Nenhum campo sensível entra no estado público ou é enviado para a janela `mailto:` quando não autorizado.

### Aviso no cadastro de doação

Na quinta etapa, quando o doador seleciona `E-mail`, o formulário exibe a mensagem curta: “Seu e-mail ficará disponível para pessoas logadas que quiserem falar com você.” O aviso aparece sob a seleção e não modifica o restante do fluxo.

## Risks / Trade-offs

- **[Dados privados vazando por conta do novo endpoint]** → responder no backend somente com `{ "email": "..." }`, sem incluir nome, título, token ou dados adicionais; validar o contrato nos testes antes do push. Depois do push real, conferir no painel e na rota que sem login responde 401, pessoa logada com preferência `E-mail` recebe somente o e-mail, a pessoa dona recebe 403 e doação com preferência `Chat do DoaFácil` responde 404. Se aparecer qualquer dado extra, remover o endpoint novo imediatamente.
- **[Falta de registro dos acessos ao e-mail do doador]** → cada chamada ao endpoint autenticado deve registrar um evento por meio da função de log existente (`xano/function/quick_start/log_event.xs`) com apenas `user_id`, `ação` e `data`.
- **[A interface pode ser contornada para consultar o próprio e-mail]** → verificar no backend se a pessoa autenticada é dona da doação e responder com HTTP 403 e mensagem própria, sem e-mail; a interface traduz o 403 para “Esta é a sua doação.”.
- **[Erro de rede ou resposta inválida sem feedback]** → centralizar a mensagem de erro simples no frontend e reutilizar os padrões visuais do site.

## Migration Plan

- Implementar a especificação, o frontend e o endpoint. Executar os testes automatizados de contrato antes de qualquer push real.
- Fazer o pull do workspace Xano somente após confirmação explícita do usuário. Depois das alterações locais, executar e revisar o dry-run completo, avisar o grupo e obter autorização antes de solicitar confirmação explícita do usuário para o push real.
- Após o push real, conferir no painel e na rota: sem login retorna 401; pessoa autenticada com preferência `E-mail` recebe somente o e-mail; a pessoa dona recebe 403 sem e-mail; e a preferência `Chat do DoaFácil` retorna 404 genérico. Se qualquer dado extra aparecer, remover imediatamente o endpoint novo.
- Testar o fluxo final no navegador.

## Open Questions

Nenhuma. As decisões acima resolvem o comportamento esperado e os limites de segurança exigidos pela mudança.
