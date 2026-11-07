# Guia do colaborador — DoaFácil

Este guia explica como trabalhar no DoaFácil sem quebrar o que já funciona. Leia inteiro antes de mexer em qualquer coisa. Ele vale para pessoas e para agentes de código (Copilot etc.).

Última atualização: 21/10/2026.

## 1. O que é o projeto

O DoaFácil é uma plataforma web (projeto acadêmico em grupo) que conecta quem quer doar objetos físicos a quem precisa.

Fora do escopo: dinheiro, vaquinha, marketplace, rede social genérica e alimentos.

Fora do MVP: "Pessoas alcançadas" e "Desapego em grupo".

## 2. Tecnologias

- **Frontend:** Reflex (Python). Só Reflex, sem outro framework.
- **Backend:** Xano (plano gratuito). Regras de negócio, autenticação e validação ficam no Xano.
- **Especificação:** OpenSpec.
- **E-mail:** SendGrid, chamado pelo Xano.
- **Versionamento:** Git e GitHub (repositório público: `solucaothn/solucao-thn`).

## 3. Regras de ouro

1. **O repositório é público.** Nunca coloque senha, token, chave de API ou endereço de ambiente em arquivo, commit, chat ou print.
2. **Segredos vivem só em variáveis do workspace do Xano** (por exemplo `SENDGRID_API_KEY` e `SENDGRID_FROM_EMAIL`).
3. **O Xano é compartilhado.** O que você publica lá afeta o grupo todo. Antes de qualquer push ao Xano: pull com a árvore commitada, dry-run revisado e aviso ao grupo.
4. **Um ciclo do OpenSpec por vez** (explore, propose, review, apply, archive).
5. **Nada de force push**, de apagar branches ou de mexer no histórico da `main`.
6. **Conferir sempre** com `git status -sb` antes de commitar. Agentes de código às vezes afirmam o que não verificaram.

## 4. Preparando o ambiente

Pasta do projeto: `Solução-THN` (com hífen). Cuidado com pastas parecidas.

No PowerShell, na raiz do projeto:

```
.venv/Scripts/Activate.ps1
```

Dependências ficam em `requirements.txt`. Ferramentas globais: Xano CLI e OpenSpec.

Para ver o site, a cada terminal novo, defina as duas variáveis de ambiente com os endereços base dos grupos de API do Xano (peça ao grupo; não são segredos, mas **nunca** vão para arquivo ou Git):

- `XANO_API_URL` (grupo Catalog)
- `XANO_AUTH_API_URL` (grupo Authentication)

Depois:

```
reflex run
```

e abra `http://localhost:3000`. Se a porta estiver ocupada, o Reflex usa outra.

Rodar os testes:

```
python -m unittest discover -s tests -v
```

## 5. Estrutura do repositório

- `doafacil/`: código do frontend (`doafacil.py`, `login.py`, `cadastro.py`, `cadastro_doacao.py`, `recuperacao_senha.py`).
- `assets/`: CSS de animação, logo, imagens e favicon.
- `tests/`: testes com `unittest`.
- `docs/`: visão geral, modelo de domínio, este guia e `design/` (telas em PNG + README).
- `openspec/`: specs principais e changes (ativas e arquivadas).
- `xano/`: cópia local do workspace do Xano.
- `AGENTS.md`: regras para agentes de código.

## 6. O que já está pronto (na `main`)

- Home pública (carrossel, contagem de doações, "Comece por aqui", seção institucional, rodapé).
- Login (`/login`) e cadastro (`/cadastro`).
- Cabeçalho logado ("Olá, nome" e "Sair").
- Animação de entrada nas páginas.
- Recuperação de senha por código: API no Xano e as três telas (`/recuperar-senha`, `/verificar-email`, `/nova-senha`).
- Cadastro de doação em 5 etapas (`/cadastro-doacao`) e endpoint `catalog/donations/publish`.

## 7. O que ainda falta

- Explorar Doações (ainda sem design).
- Detalhe da doação e Minhas doações.
- Interesse, mensagens, avaliações e administração (sem tabelas ainda).
- Páginas "Como funciona" e "Categorias".
- Botões e links da home que ainda não levam a lugar nenhum.

Em aberto com o grupo: status e transições da doação, mensagens entre usuários, avaliações, moderação e o destino dos 3 endpoints antigos do modelo do Xano (`request_reset_link`, `magic-link-login` e `update_password`).

## 8. Decisões já tomadas (não reabrir sem o grupo)

- Login só por e-mail (sem CPF).
- Cadastro: nome, e-mail, cidade, estado, senha e confirmar senha (sem telefone).
- Senha: mínimo de 8 caracteres, com letra e dígito. E-mail em minúsculas e único.
- Localização da doação = cidade e estado do perfil de quem doa.
- Etiqueta NOVO = doação criada nos últimos 7 dias.
- Condição da doação: Ótimo, Bom ou Regular.
- A home mostra só doações disponíveis.
- Sessão: o token fica só no estado do Reflex. Recarregar a mesma aba mantém o login; abrir outra aba ou reiniciar o servidor desloga.
- Logs de evento guardam só `user_id`, ação e data. Nunca e-mail, nome, código, token ou senha.
- Recuperação de senha: código de 6 dígitos, válido por 10 minutos, 5 tentativas por código, reenvio após 30 segundos, no máximo 5 envios por hora. As respostas são neutras (não revelam se a conta existe). Trocar a senha não cria sessão: a pessoa volta ao login com um aviso verde.
- Toda página nova tem animação de entrada, conforme o `AGENTS.md`.

### Confirmação de e-mail no cadastro

A conta só é criada depois que a pessoa confirma o código enviado ao e-mail. O fluxo usa:

- `POST /auth/signup`: valida os dados e inicia ou atualiza a pendência. Não cria conta nem sessão e não devolve token de autenticação.
- `POST /auth/signup_resend`: solicita outro código para o e-mail da pendência.
- `POST /auth/signup_verify`: recebe e-mail, código e senha; cria a conta somente se o código e a senha forem válidos. A resposta não cria sessão nem contém token.
- Tabela `signup_pending`: mantém os dados necessários ao cadastro pendente, o hash do código, tentativas, horários de envio e expiração. Não armazena a senha.
- Função `Signup/send_confirmation_code`: envia o código de cadastro pelo SendGrid; não reutiliza o envio de recuperação de senha.

O código tem seis dígitos, vale por 10 minutos e pode ser tentado até cinco vezes. Um novo envio só é permitido após 30 segundos e há no máximo cinco envios por hora. A pendência expira 24 horas depois do último envio permitido e só é removida quando acessada após expirar. Os limites e a validação são aplicados no Xano.

As respostas de `auth/signup` são neutras mesmo quando o e-mail já pertence a uma conta: o status e o corpo não revelam essa condição, embora o tempo de resposta possa diferir. E-mail existente não deve gerar pendência nem envio de código.

A senha é enviada ao Xano para validação no início e novamente na verificação, mas nunca é gravada no Xano. Após o início aceito, fica somente no estado transitório do Reflex até a verificação, e é apagada ao concluir ou ao usar “Usar outro e-mail”. O valor de “Confirmar senha” chega transitoriamente ao servidor Reflex junto ao envio do formulário, mas não é guardado no estado nem enviado ao Xano. O código também não fica no estado Reflex.

O estado de cadastro pendente é transitório no servidor Reflex: reiniciar o servidor ou abrir outra aba pode perdê-lo. Se a guarda da tela `/verificar-email` não encontrar o e-mail no estado, redireciona para `/recuperar-senha`; iniciar novamente o cadastro permite obter um novo estado de fluxo. No fluxo de cadastro, “Usar outro e-mail” limpa e-mail e senha e retorna a `/cadastro`.

Nas validações Xano desse fluxo, e-mail e código usam verificações de comprimento com `strlen` em vez de padrões de regex com barra invertida. A senha segue as regras da conta: mínimo de oito caracteres, com letra e dígito.

### Fotos obrigatórias na publicação de doações

A foto da doação é obrigatória tanto no wizard quanto no backend. O endpoint `POST /catalog/donations/publish` recusa `photos` ausente, nulo ou vazio com erro `inputerror` (HTTP 400) e a mensagem “Adicione pelo menos uma foto para continuar.”. Essa validação ocorre antes de qualquer upload ou gravação. O limite continua sendo de cinco fotos.

O corpo do erro contém os campos `code` (`ERROR_CODE_INPUT_ERROR`), `message` e `payload`. O site procura a mensagem “Adicione pelo menos uma foto para continuar.” em qualquer campo textual do JSON de erro e, quando a encontra, mostra a mesma mensagem sem limpar os dados do formulário nem marcar a doação como publicada. Outros erros continuam usando o tratamento genérico.

O campo `donation_photo.photo` é obrigatório. A auditoria confirmou que não havia linhas dessa tabela sem foto antes da alteração. Doações antigas com `donation.photo` vazio não foram alteradas.

O endpoint `publish` foi criado por outro integrante e pode ter outros consumidores. Antes do push real de mudanças nele, avise o grupo, obtenha o OK explícito do grupo e a confirmação necessária para publicar. Revise o dry-run e interrompa a publicação se ele mostrar alterações fora do escopo aprovado.

## 9. Design

- As telas ficam em `docs/design` como PNG. O `README.md` dessa pasta **prevalece sobre as imagens**.
- O agente de código não lê o Figma; ele lê os PNG.
- Fidelidade ao Figma é importante: cor principal verde, fundo creme, cabeçalho branco, rodapé escuro, fonte LINE Seed JP.
- Ao adicionar imagens, confira a numeração para não repetir número de outra pessoa e **não use espaço no nome do arquivo**.

## 10. Fluxo de trabalho com OpenSpec e Git

Uma entrega, do começo ao fim:

1. Criar uma branch própria a partir da `main` (`feat/...`, `docs/...` ou `chore/...`).
2. Propor a change no OpenSpec (`/opsx-propose`; só cria os artifacts).
3. Revisar a proposta, depois implementar (`/opsx-apply <change>`).
4. Rodar os testes e testar no navegador.
5. Commitar marcando arquivo por arquivo ou por pasta. **Nunca `git add .`**.
6. Push da branch.
7. Abrir o pull request no GitHub, conferir a aba **Files changed** e só então mesclar.
8. `git switch main` e `git pull`.
9. Arquivar a change (`/opsx-archive <change>`), commitar e repetir o fluxo de pull request.

Não confunda: **pull** traz do GitHub para o seu PC, **push** leva do seu PC para o GitHub, **pull request** é o pedido para juntar a sua branch na `main`.

## 10.1 Arquivos do Xano que nunca entram em commit

Depois de um `xano pull`, 8 arquivos aparecem como modificados só por causa da quebra de linha (LF/CRLF). Eles **nunca** entram em commit:

- `xano/api/authentication/auth/login_POST.xs`
- `xano/api/authentication/auth/me_GET.xs`
- `xano/api/authentication/auth/signup_POST.xs`
- `xano/api/authentication/message/send_welcome_email_POST.xs`
- `xano/api/authentication/reset/magic_link_login_POST.xs`
- `xano/api/authentication/reset/update_password_POST.xs`
- `xano/function/quick_start/log_event.xs`
- `xano/table/user.xs`

Se a formatação real de algum deles precisar mudar, isso vai num commit separado e combinado com o grupo.

## 11. Trabalhando com o Xano

- Antes de editar o Xano, confira o status e peça confirmação explícita antes de rodar `xano workspace pull -d ./xano`; preserve todas as alterações preexistentes.
- Consulte o Xano Developer MCP antes de escrever XanoScript e valide nele cada arquivo `.xs` alterado ou criado.
- Rode `xano workspace push -d ./xano --dry-run` e revise a saída completa. Se aparecer alteração não aprovada — especialmente em `donation_photo` ou `password_reset_code` — pare e avise o grupo.
- Avise o grupo e obtenha o OK antes de publicar mudanças que afetam consumidores compartilhados. Obtenha a confirmação explícita necessária imediatamente antes do push real.
- Depois da aprovação, faça o push apenas das alterações previstas. Ao preparar commits, revise cada caminho e adicione arquivos individualmente; nunca use `git add .` em `xano/`, pois o workspace contém alterações compartilhadas que podem não pertencer à tarefa.
- Depois do push, confira o estado do workspace e versione somente os arquivos Xano aprovados para a change.

## 12. Dicas para agentes de código

- Ler `docs/`, `AGENTS.md` e as specs antes de agir.
- Escopo pequeno. Não ampliar o que foi pedido.
- Sem commit, push ou force push sem pedido explícito.
- Não mexer em `xano/` sem pedido explícito.
- Responder em português do Brasil.
- No fim de cada tarefa, mostrar o resumo, o `git status` e o `git diff --stat`.
- Teste manual no navegador é feito por uma pessoa, não pelo agente.

## 13. Problemas comuns

- **Porta ocupada:** o Reflex usa outra porta; veja a mensagem no terminal.
- **Comando quebrado na colagem:** use comandos curtos, um por vez.
- **E-mail de recuperação caiu no spam:** é esperado no ambiente de teste.
- **E-mail não chega:** confira se o endereço de teste está digitado certo e veja os registros de e-mail do SendGrid.
- **Acento quebrado no terminal:** use `-Encoding UTF8` ao ler arquivos com `Get-Content`.
