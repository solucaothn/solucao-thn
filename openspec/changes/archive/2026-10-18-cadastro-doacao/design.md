## Contexto

Consulte `proposal.md` para a motivação e `specs/donation-creation/spec.md` para o contrato funcional. O Xano já possui um endpoint autenticado de criação em `/catalog/donations`, que recebe categoria, título e descrição. A tabela `donation` armazena uma única foto e a condição do item; a tabela `user` já armazena cidade e UF. O catálogo também oferece consulta de categorias. No Reflex, a sessão e o token ficam em `LoginState`, e as páginas são registradas em `doafacil/doafacil.py`.

As referências visuais estão em `docs/design/06-cadastro-de-doacao.png` a `docs/design/10-formas -de-contato.png`. A documentação geral do design define que a localização da doação é copiada do perfil do doador. O endpoint autenticado `/auth/profile` já retorna cidade e UF para exibição; o endpoint de publicação também deve obter esses dados da identidade autenticada, sem confiar no valor exibido no cliente. As imagens ainda mostram a progressão antiga de oito passos e a condição no passo final; esta change aplica as decisões atualizadas da proposta.

## Objetivos / Não objetivos

**Objetivos:**

- Implementar o fluxo completo de criação em cinco etapas com Reflex e Xano.
- Preservar compatibilidade com a criação e a leitura de doações existentes, incluindo a foto de capa usada pela home.
- Validar e persistir no backend os campos necessários, derivando do token a identidade e a localização do doador.
- Manter a interface próxima das telas fornecidas e usar `auth-card-enter` no cartão do formulário, respeitando `prefers-reduced-motion`.

**Não objetivos:**

- Coletar telefone, endereço específico ou outro dado de contato, nem implementar o envio de mensagens.
- Alterar as regras de descoberta, reserva e conclusão de doações.
- Publicar automaticamente alterações no workspace compartilhado do Xano.

## Decisões

1. **Manter o endpoint atual e criar uma operação de publicação completa separada.** O endpoint existente continua aceitando seu contrato atual. O wizard usa uma nova operação autenticada, evitando tornar obrigatórios os novos campos para clientes existentes.
2. **Derivar no Xano o responsável e a localização.** O Reflex carrega cidade e UF pelo endpoint autenticado `/auth/profile` para exibição no passo de entrega. Na criação, o backend usa a sessão autenticada para obter novamente o usuário e copiar os valores atuais do perfil. O cliente não escolhe nem substitui os valores persistidos.
3. **Preservar a foto singular como capa e relacionar as imagens selecionadas à doação.** Uma estrutura ordenada associada à doação guarda as referências de até cinco fotos; a primeira também alimenta o campo `photo` legado para manter os consumidores existentes, como a home. A forma concreta do campo/tabela e das operações deve ser validada com a documentação atual do Xano antes de editar XanoScript.
4. **Enviar arquivos ao armazenamento nativo do Xano no fluxo de publicação.** A interface limita a seleção a cinco imagens, mostra progresso e envia ao backend apenas formatos aceitos pelo armazenamento. PDF não é tratado como foto. A implementação deve evitar criar uma doação publicável antes de as referências de todas as imagens selecionadas estarem disponíveis.
5. **Persistir localização, modalidade de entrega e preferência de contato junto aos dados da doação.** As novas propriedades devem ser aditivas e compatíveis com registros antigos; a condição existente é reutilizada. Nenhum dado pessoal de contato será adicionado ao perfil ou à doação.
6. **Manter estado do formulário no Reflex até uma resposta definitiva.** Erros de validação, rede ou serviço são mostrados na etapa correspondente, preservando os dados para correção ou nova tentativa. Token e dados pessoais não são escritos em logs.
7. **Usar as categorias fornecidas pelo catálogo do Xano.** O frontend carrega as opções da API existente; o novo endpoint valida a categoria novamente para não confiar na seleção do cliente.

## Riscos / Compensações

- **Falha após enviar arquivos, antes de persistir a doação** → a doação não é confirmada nem fica publicamente disponível; a implementação deve limpar uploads temporários quando possível e permitir nova tentativa sem perder o formulário.
- **Alteração no modelo do Xano compartilhado** → manter mudanças aditivas, iniciar com `xano workspace pull -d ./xano`, revisar o diff e validar o `push --dry-run`; não enviar alterações reais sem a revisão prevista pelo projeto.
- **Registros antigos sem modalidade, localização ou preferência** → preservar compatibilidade com campos opcionais nos registros legados; exigir os novos valores somente na operação usada pelo wizard.
- **Endereço exibido na imagem de referência diverge da decisão documentada** → mostrar a cidade e a UF do perfil, sem pedir endereço, conforme `docs/design/README.md`.

## Plano de migração

1. Atualizar localmente o modelo e a operação de publicação do Xano de forma aditiva, preservando o endpoint atual e o campo de foto de capa.
2. Validar os arquivos XanoScript e revisar `xano workspace push -d ./xano --dry-run`; a sincronização real do workspace fica fora da execução automática desta change.
3. Implementar o wizard Reflex e integrar a publicação completa após o contrato local do backend estar definido.
4. Verificar testes, fluxo visual e persistência com sessão autenticada. Se a alteração local do Xano precisar ser revertida antes da sincronização, reverter apenas as mudanças desta change e manter os contratos antigos.

## Questões em aberto

Nenhuma questão de escopo permanece aberta. Durante a implementação, a documentação do Xano deve ser consultada para determinar a sintaxe e os limites exatos do upload de imagens antes de alterar arquivos `.xs`.
