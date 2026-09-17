## 1. Preparação da base de usuário

- [ ] 1.1 Definir o modelo de usuário e localização no backend, incluindo campos obrigatórios, unicidade de e-mail e regras mínimas de persistência, e verificar que a estrutura suporta o fluxo de autenticação inicial.
- [ ] 1.2 Definir as entradas e saídas dos endpoints de cadastro e login, incluindo mensagens de erro e comportamento para credenciais inválidas, e verificar que o contrato atende ao spec de identidade/autorização.

## 2. Cadastro e autenticação

- [ ] 2.1 Implementar o endpoint de cadastro de usuário no backend e verificar que o usuário é criado somente com dados válidos e localização associada.
- [ ] 2.2 Implementar o fluxo de autenticação por e-mail e senha e verificar que login com credenciais válidas concede acesso e login inválido é rejeitado sem vazamento de informações sensíveis.
- [ ] 2.3 Validar tratamento de erros para e-mail duplicado, dados obrigatórios ausentes e usuário inexistente, e confirmar que as respostas atendem ao comportamento especificado.

## 3. Perfil e autorização

- [ ] 3.1 Implementar a leitura do próprio perfil e verificar que um usuário autenticado consegue consultar somente seus dados.
- [ ] 3.2 Implementar a edição do próprio perfil e verificar que alterações são persistidas somente para o dono do registro.
- [ ] 3.3 Aplicar a autorização no backend em todas as operações do perfil e verificar que acessos a perfis de terceiros são bloqueados.
- [ ] 3.4 Validar que o frontend em Reflex consome os endpoints corretamente sem depender de regras de segurança na interface.

## 4. Verificação de integração

- [ ] 4.1 Executar a validação end-to-end do fluxo completo de cadastro, login, consulta e atualização do perfil para confirmar a integridade da mudança.
- [ ] 4.2 Revisar a cobertura de segurança e registrar que nenhuma operação de perfil pode ser executada sem validação no backend.