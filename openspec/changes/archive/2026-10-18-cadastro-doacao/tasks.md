## 1. Preparação e contrato do Xano

- [x] 1.1 Salvar as imagens de referência em `docs/design/` e conferir as cinco telas do fluxo
- [x] 1.2 Atualizar a proposta para refletir os cinco passos, a condição no passo 2 e as decisões de escopo
- [x] 1.3 Executar `xano workspace pull -d ./xano` e consultar a documentação do Xano para confirmar os formatos, limites e fluxo de upload nativo de imagens antes de alterar XanoScript
- [x] 1.4 Atualizar o modelo de doação e criar a operação autenticada de publicação completa, preservando o contrato existente, a foto de capa e registros legados; validar as alterações `.xs` e cenários de categoria, autorização, condição, entrega, preferência, localização do perfil e limite de cinco fotos
- [x] 1.5 Executar `xano workspace push -d ./xano --dry-run`, revisar as alterações propostas e registrar o resultado sem fazer push real nesta tarefa

## 2. Wizard em Reflex

- [x] 2.1 Criar `doafacil/cadastro_doacao.py` com estado e componentes para as cinco etapas; verificar que o progresso indica “Passo X de 5”, que os botões avançar/voltar preservam os valores e que campos obrigatórios bloqueiam avanço
- [x] 2.2 Integrar a rota `/cadastro-doacao` e o botão “Quero Doar” da página inicial em `doafacil/doafacil.py`; verificar que a sessão autenticada é exigida e que uma sessão ausente segue para o login
- [x] 2.3 Carregar categorias do endpoint existente e cidade/UF pelo endpoint autenticado `/auth/profile`; integrar a publicação ao novo contrato Xano e verificar que o backend determina o responsável e copia cidade/UF do perfil, enquanto erros preservam os dados sem confirmação falsa
- [x] 2.4 Implementar seleção, remoção e progresso de até cinco imagens; verificar recusa de PDF/formatos não aceitos, tratamento de falha e ausência de publicação parcial
- [x] 2.5 Reproduzir a hierarquia visual das referências e aplicar `auth-card-enter` com suporte a `prefers-reduced-motion`; conferir layout responsivo e contraste dos estados de erro, carregamento e publicação

## 3. Verificação integrada

- [x] 3.1 Adicionar testes automatizados para validação por etapa, navegação, carregamento de categorias, limites de fotos, erros do serviço e tratamento da resposta de publicação; executar os testes direcionados
- [x] 3.2 Testar no navegador o fluxo completo com uma sessão autenticada e ambiente Xano de teste, verificando criação, campos persistidos, localização do perfil, capa da foto e mensagem de sucesso
- [x] 3.3 Testar acesso sem autenticação e falhas de categoria, upload e publicação; confirmar que nenhuma falha exibe sucesso e que o formulário permite corrigir e tentar novamente
