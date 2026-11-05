# Design

## Contexto

O fluxo atual em `doafacil/login.py` envia o cadastro a `auth/signup` e espera `authToken` e `user_id`. A tela compartilhada `/verificar-email` e os handlers de `reset/request_code` e `reset/verify_code` pertencem à recuperação de senha; seus contratos devem permanecer separados e intactos. A pasta `xano/` já contém alterações locais não relacionadas; elas não fazem parte desta change.

## Objetivos / Não objetivos

**Objetivos:**

- Confirmar o controle do e-mail antes de criar a conta, sem emitir sessão.
- Reutilizar a tela de código sem misturar estado, mensagens ou endpoints de cadastro e recuperação.
- Guardar a senha somente no estado transitório Reflex durante a confirmação, nunca na tabela pendente.
- Manter neutras as respostas relacionadas à existência da conta.

**Não objetivos:**

- Alterar login, recuperação de senha, sessão existente ou `send_welcome_email_POST`.
- Armazenar senha na pendência, reutilizar `password_reset_code` ou `send_recovery_code`.
- Alterar tabelas ou endpoints de doação.

## Decisões

### Fluxo e contratos dos endpoints

- `POST /auth/signup` recebe nome, e-mail, senha, cidade e estado. O Xano normaliza o e-mail, valida a senha e inicia uma pendência sem armazenar a senha. A interface valida também antes de enviar.
- `POST /auth/signup_resend` recebe o e-mail do fluxo e aplica novamente os limites. `POST /auth/signup_verify` recebe e-mail, código e senha; valida a senha outra vez e cria a conta somente após validar o código.
- As respostas de início e reenvio usam o mesmo status e corpo neutros para e-mail já cadastrado, envio aceito, limite atingido ou falha do SendGrid. O início não cria pendência nem envia código quando já existe uma conta. A verificação não diferencia pendência ausente, expirada, código inválido ou bloqueado.
- A resposta de verificação bem-sucedida confirma a criação, mas não contém token nem cria sessão. A pessoa segue para `/login`.
- Os nomes e caminhos seguem as decisões aprovadas; não se altera `send_welcome_email_POST`.

### Dados pendentes e limites

- Criar uma tabela independente da recuperação, com e-mail normalizado e índice único, nome, cidade, estado, hash do código, expiração do código, contador de tentativas, timestamps suficientes para o limite móvel de cinco envios por hora, e expiração da pendência.
- Gerar código de seis dígitos, armazenar apenas hash não reversível, expirar em 10 minutos e invalidar após cinco tentativas incorretas. Um reenvio permitido só ocorre após 30 segundos, invalida o código anterior e reinicia as tentativas do novo código.
- Se `auth/signup` for repetido para uma pendência existente, atualizar os dados e emitir novo código apenas quando cooldown e cota permitirem; preservar os timestamps da janela horária. Se estiver bloqueado, não alterar a pendência nem zerar limites. Só um envio permitido renova as 24 horas da pendência.
- A pendência expira 24 horas depois do último envio permitido. A limpeza é sob demanda: operações que acessam uma pendência expirada a removem e retornam resultado neutro; não há tarefa periódica.
- A verificação e a criação da conta devem tratar concorrência e e-mail já utilizado sem criar duplicatas. A exclusão da pendência acompanha a criação bem-sucedida. A sintaxe das operações, dos índices e do hash será confirmada no Xano Developer MCP durante o apply, antes de escrever XanoScript.

### Senha e estado Reflex

- A senha é enviada no pedido inicial para o Xano validar suas regras, mas não é gravada em tabela. Após a resposta neutra que permite prosseguir, o frontend a mantém no estado Reflex transitório e a envia novamente com e-mail e código na verificação.
- O valor de Confirmar senha não é armazenado no estado. O código é recebido apenas como dado transitório do formulário. Nenhum deles é registrado pelo frontend.
- Em “Usar outro e-mail”, sucesso de verificação ou abandono do fluxo, limpar e-mail, senha e estado de confirmação. Sem e-mail no estado, `/verificar-email` redireciona para `/recuperar-senha`, como atualmente; `/cadastro` só é destino quando o indicador de fluxo for cadastro e a pessoa acionar “Usar outro e-mail”.

### Envio, neutralidade e registros

- Criar função SendGrid exclusiva para o código de cadastro, com assunto e conteúdo próprios em português; não reaproveitar a função de recuperação.
- A contagem de reenvio é por e-mail normalizado e aplicada no backend. O frontend mostra a contagem de 30 segundos como orientação, não como controle de segurança.
- A mensagem da tela de cadastro deve ser condicional e neutra, por exemplo: “Se for possível confirmar este e-mail, enviaremos um código de 6 dígitos.” Assim, não afirma que todo envio foi realizado nem revela se a conta já existe.
- Usar a função de log existente somente depois de criar a conta, com `user_id` e ação; a data é preenchida pelo logger. Não registrar e-mail, nome, código, senha ou token em eventos, erros ou respostas.
- Como a senha e o código transitam por chamadas Xano, a tarefa manual após um teste real inspecionará o histórico de execução para verificar que nenhum dos dois foi registrado.

### Interface compartilhada e aviso

- Manter um indicador explícito do tipo de fluxo (cadastro ou recuperação) para selecionar texto, endpoint de reenvio/verificação e destino de “Usar outro e-mail”, sem reaproveitar estado de recuperação para cadastro.
- O fluxo de recuperação continua usando seus endpoints e mensagens atuais. A rota e o formulário de código são compartilhados.
- Após criar a conta, preparar um aviso verde transitório no login — “Cadastro confirmado! Você já pode entrar com seu e-mail e senha.” — e limpar o aviso ao digitar, tentar entrar, sair do login ou recarregar. Não definir `auth_token`.

## Riscos / Compensações

- **A senha transita pelo Xano em duas chamadas mesmo sem ser persistida** → validar e não persistir no backend, evitar sua inclusão em mensagens de erro, e inspecionar manualmente o histórico de execução depois do teste real.
- **O código tem apenas seis dígitos** → aplicar no Xano expiração de 10 minutos, limite de cinco tentativas, intervalo de 30 segundos e máximo de cinco envios por hora; armazenar somente hash.
- **A mudança de `auth/signup` quebra consumidores que esperam token** → atualizar e testar o frontend e coordenar a publicação do endpoint alterado com o grupo; não deixar o endpoint criar conta sem confirmação.
- **A tabela ou o dry-run pode incluir alterações Xano alheias** → parar e avisar o grupo se o dry-run apresentar mudanças em `donation_photo` ou `password_reset_code`; não publicar essas alterações.
- **Falha de entrega do SendGrid** → manter a resposta neutra, não permitir verificação com código não entregue e invalidar o código cuja entrega falhou.

## Plano de migração

1. Implementar o frontend e os testes com respostas simuladas, sem alterar arquivos Xano.
2. Antes de qualquer `xano workspace pull -d ./xano`, conferir e mostrar o `git status`; aguardar confirmação explícita do Higor. Preservar todas as alterações preexistentes.
3. Consultar e validar a sintaxe no Xano Developer MCP; só depois do pull editar os arquivos Xano da change e validar o novo XanoScript pelo MCP.
4. Executar `xano workspace push -d ./xano --dry-run`, revisar e mostrar toda a saída. Se aparecer alteração em `donation_photo` ou `password_reset_code`, interromper e avisar.
5. Avisar o grupo, obter seu OK para alterar `auth/signup` e aguardar autorização explícita do Higor antes do push real. Publicar apenas as alterações aprovadas desta change.
6. Coordenar a atualização do frontend com a publicação: a versão antiga espera token e não deve ser tratada como compatível com a nova resposta de `auth/signup`.
7. Após o teste real, conferir o histórico de execução do Xano. Se senha ou código aparecerem, interromper novos testes/publicação e corrigir a exposição antes de prosseguir.

Se for necessário interromper a funcionalidade, desabilitar temporariamente o início de cadastro; não restaurar o comportamento que cria conta sem confirmação. `send_welcome_email_POST` permanece inalterado.
