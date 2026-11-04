# Proposta

## Por quê

O cadastro atual cria imediatamente a conta e emite uma sessão, sem confirmar que a pessoa controla o e-mail informado. A confirmação antes da criação reduz cadastros com endereços não verificados e estabelece um fluxo neutro sem armazenar a senha no Xano.

## O que muda

- **BREAKING:** `POST /auth/signup` passa a iniciar um cadastro pendente e enviar um código; deixa de criar conta e sessão.
- Criar endpoints para reenviar o código e verificar o cadastro. A conta só é criada após validar o código, sem emitir sessão.
- Armazenar cadastros pendentes por e-mail normalizado, com unicidade, validade e limites definidos; a senha não será persistida no Xano.
- Reutilizar `/verificar-email` para cadastro e recuperação, distinguindo os textos e mantendo intacto o fluxo de recuperação.
- Manter a senha somente no estado transitório Reflex durante a confirmação e apagá-la ao concluir ou ao escolher “Usar outro e-mail”.
- Retornar ao login após a confirmação, com aviso verde de cadastro concluído.
- Enviar o código por uma nova função Xano própria de cadastro via SendGrid.
- Atualizar testes, documentação de design e guia do colaborador.
- Manter `send_welcome_email_POST` fora desta mudança.

## Capacidades

### Novas capacidades

Nenhuma. A confirmação de cadastro pertence à capacidade existente de conta de usuário.

### Capacidades modificadas

- `user-account`: alterar o contrato de cadastro imediato, a resposta distinguível para e-mail já cadastrado e a interface de cadastro; acrescentar os requisitos de pendência, código de confirmação, envio, proteção dos dados e conclusão sem sessão.
- `password-recovery`: ajustar somente o requisito da interface compartilhada de verificação de código para distinguir cadastro de recuperação, preservando o fluxo atual de recuperação.

## Impacto

- Frontend Reflex: `doafacil/cadastro.py`, `doafacil/login.py` e a tela compartilhada em `doafacil/recuperacao_senha.py`.
- Xano: alterar `auth/signup`; criar `auth/signup_resend`, `auth/signup_verify`, a tabela de cadastros pendentes e uma função SendGrid específica. Não reutilizar a tabela nem a função de recuperação e não alterar `send_welcome_email_POST`.
- Testes: atualizar `tests/test_signup.py`, adicionar testes do fluxo de confirmação e preservar os testes de recuperação.
- Documentação: registrar o uso da tela 12 também no cadastro em `docs/design/README.md` e atualizar `docs/guia-do-colaborador.md`.
- A publicação do endpoint `auth/signup` afeta consumidores existentes e depende de revisão e autorização do grupo antes do push real.
