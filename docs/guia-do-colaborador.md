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

- Antes de editar o Xano: `xano pull` com a árvore do Git limpa (commitada).
- Escreva ou altere o XanoScript e valide pelo Xano Developer MCP.
- Rode o dry-run e leia o que ele vai criar, alterar ou apagar. Só então faça o push real.
- Avise o grupo antes do push real.
- Depois do push, commite os arquivos sincronizados.

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
