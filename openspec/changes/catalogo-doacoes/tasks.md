## 1. Modelagem e preparação do Xano

- [x] 1.1 Criar tabela de categorias com nome único, campos obrigatórios e índices; verificar a estrutura no export Xano.
- [x] 1.2 Criar tabela de doações com proprietário, categoria, campos obrigatórios, status fechado e índices; verificar a referência ao usuário autenticado.
- [x] 1.3 Preparar a tabela de categorias para população manual diretamente no workspace Xano e verificar unicidade por índice; os registros iniciais serão inseridos no workspace remoto pelo operador.

## 2. APIs e regras de negócio no Xano

- [x] 2.1 Implementar endpoint autenticado de criação de doação usando o proprietário do token; verificar cadastro sem `user_id` confiável no payload.
- [x] 2.2 Implementar endpoints autenticados de edição e exclusão com checagem de posse no backend; verificar bloqueio para doações de terceiros.
- [x] 2.3 Implementar endpoint de alteração de status com conjunto fechado e transições válidas; verificar rejeição de status inválido.
- [x] 2.4 Implementar endpoint de listagem básica com categoria e status e resposta sem dados privados do proprietário; verificar lista vazia e doações excluídas.
- [x] 2.5 Implementar endpoint de leitura de categorias para o catálogo; verificar que o Reflex consegue selecionar somente categorias existentes.

## 3. Interface Reflex

- [x] 3.1 Criar estado e cliente de API para listagem e categorias sem persistência local de dados sensíveis; verificar tratamento de erros do Xano.
- [x] 3.2 Criar formulário de cadastro e edição de doação consumindo o backend; verificar mensagens de validação e atualização após resposta da API.
- [x] 3.3 Criar fluxo de exclusão com confirmação e atualização da listagem; verificar que a UI não decide posse localmente.
- [x] 3.4 Exibir status, categoria e dados públicos na listagem; verificar que campos privados do proprietário não são renderizados.

## 4. Segurança e integração

- [ ] 4.1 Validar cada endpoint protegido com token válido, ausente, expirado e pertencente a outro usuário; verificar respostas de autenticação e autorização.
- [ ] 4.2 Executar fluxo end-to-end de cadastro, edição, mudança de status, listagem e exclusão; verificar persistência e integridade no Xano.
- [x] 4.3 Executar build/testes do Reflex e validar que a interface usa somente endpoints do Xano para decisões de acesso.
