# Proposta: Cadastro de Doação

## Por quê

O fluxo de criação precisa refletir os cinco passos aprovados, corrigir a indicação legada de oito passos e manter os dados do doador até a publicação. Hoje o endpoint existente do Xano persiste somente categoria, título e descrição, e a doação possui apenas uma foto; por isso o fluxo visual não conseguiria publicar com todos os dados solicitados.

## O que muda

- Criar o wizard autenticado de cadastro em `/cadastro-doacao`, usando as telas em `docs/design/06-cadastro-de-doacao.png` a `docs/design/10-formas -de-contato.png` como referência visual e adaptando o indicador para cinco passos.
- Conectar o botão “Quero Doar” da página inicial ao fluxo autenticado de cadastro.
- Organizar os campos:
  1. título/nome do objeto a doar;
  2. descrição, categoria e condição (Ótimo, Bom ou Regular);
  3. seleção de até cinco fotos;
  4. modalidade de entrega (Retirada, Entrega ou A combinar) e localização copiada da cidade e UF do perfil;
  5. preferência de contato (WhatsApp, E-mail ou Chat do DoaFácil) e publicação.
- Implementar navegação com validação por etapa, preservação dos valores ao voltar e indicação de progresso dos arquivos selecionados.
- Persistir no Xano os dados do cadastro, a localização do perfil no momento da publicação, a modalidade de entrega, a preferência de contato e as fotos. A identidade do doador será derivada da sessão autenticada; nenhum dado pessoal de contato será coletado nesta change.
- Manter compatibilidade do endpoint de criação existente, introduzindo um contrato autenticado próprio para a publicação completa do wizard.
- Exibir confirmação somente após a publicação ter sido aceita pelo Xano e apresentar erros sem descartar os dados preenchidos.

Fora de escopo: cadastro de telefone ou outros dados de contato, envio de mensagens, edição/detalhe da doação e alterações no fluxo de descoberta além do necessário para preservar a foto de capa já consumida pela home.

## Capacidades

### Novas capacidades

- `donation-creation`: fluxo autenticado de cadastro e publicação de doação, incluindo validação, fotos e persistência dos dados.

### Capacidades modificadas

- Nenhuma.

## Impacto

- Frontend Reflex: novo módulo `doafacil/cadastro_doacao.py`, registro da rota em `doafacil/doafacil.py` e testes correspondentes.
- Xano: modelo de doação e armazenamento relacionado às fotos; novo endpoint autenticado de publicação completa. A listagem de categorias existente será consumida pelo wizard, e a foto de capa usada pela home deverá permanecer compatível.
- Não há previsão de nova dependência ou de publicação automática no workspace compartilhado do Xano.
