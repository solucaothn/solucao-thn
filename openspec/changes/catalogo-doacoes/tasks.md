## 1. Modelagem e preparação do Xano

- [ ] 1.1 Criar tabela de categorias com nome único, campos obrigatórios e índices; verificar a estrutura no export Xano.
- [ ] 1.2 Criar tabela de doações com proprietário, categoria, campos obrigatórios, status fechado e índices; verificar a referência ao usuário autenticado.
- [ ] 1.3 Popular categorias iniciais diretamente no workspace Xano por operação humana e verificar que não há duplicidade.

## 2. APIs e regras de negócio no Xano

- [ ] 2.1 Implementar endpoint autenticado de criação de doação usando o proprietário do token; verificar cadastro sem `user_id` confiável no payload.
- [ ] 2.2 Implementar endpoints autenticados de edição e exclusão com checagem de posse no backend; verificar bloqueio para doações de terceiros.
- [ ] 2.3 Implementar endpoint de alteração de status com conjunto fechado e transições válidas; verificar rejeição de status inválido.
- [ ] 2.4 Implementar endpoint de listagem básica com categoria e status e resposta sem dados privados do proprietário; verificar lista vazia e doações excluídas.
- [ ] 2.5 Implementar endpoint de leitura de categorias para o catálogo; verificar que o Reflex consegue selecionar somente categorias existentes.

## 3. Interface Reflex

- [ ] 3.1 Criar estado e cliente de API para listagem e categorias sem persistência local de dados sensíveis; verificar tratamento de erros do Xano.
- [ ] 3.2 Criar formulário de cadastro e edição de doação consumindo o backend; verificar mensagens de validação e atualização após resposta da API.
- [ ] 3.3 Criar fluxo de exclusão com confirmação e atualização da listagem; verificar que a UI não decide posse localmente.
- [ ] 3.4 Exibir status, categoria e dados públicos na listagem; verificar que campos privados do proprietário não são renderizados.

## 4. Segurança e integração

- [ ] 4.1 Validar cada endpoint protegido com token válido, ausente, expirado e pertencente a outro usuário; verificar respostas de autenticação e autorização.
- [ ] 4.2 Executar fluxo end-to-end de cadastro, edição, mudança de status, listagem e exclusão; verificar persistência e integridade no Xano.
- [ ] 4.3 Executar build/testes do Reflex e validar que a interface usa somente endpoints do Xano para decisões de acesso.
