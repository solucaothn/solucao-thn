# Spec Delta

## ADDED Requirements

### Requirement: Reinício do formulário a cada nova entrada
Cada nova entrada em `/cadastro-doacao` MUST iniciar um novo cadastro vazio e habilitado, limpando os dados e estados temporários da visita anterior antes de carregar as categorias e a localização do perfil.

#### Scenario: Nova entrada após publicar uma doação
- **WHEN** a pessoa publica uma doação com sucesso e depois entra novamente em `/cadastro-doacao`
- **THEN** o formulário MUST voltar ao passo 1 com título, descrição, categoria, condição, forma de entrega e preferência de contato vazios
- **AND** MUST limpar mensagens de erro e sucesso, estado de publicação e progresso de upload
- **AND** MUST limpar os arquivos selecionados no componente de upload

#### Scenario: Troca de conta na mesma aba
- **WHEN** a pessoa publica uma doação, sai da conta, entra com outra conta na mesma aba e abre `/cadastro-doacao`
- **THEN** o formulário MUST iniciar vazio no passo 1, sem dados ou estado de publicação da conta anterior
- **AND** MUST carregar categorias e cidade/UF do perfil da conta atualmente autenticada

#### Scenario: Recarregar a página de cadastro
- **WHEN** a pessoa recarrega `/cadastro-doacao`
- **THEN** o formulário MUST iniciar vazio no passo 1, limpando também os arquivos selecionados
- **AND** MUST carregar categorias e cidade/UF do perfil autenticado

#### Scenario: Publicação concluída na visita atual
- **WHEN** a publicação é concluída com sucesso e a pessoa permanece na mesma visita de `/cadastro-doacao`
- **THEN** o formulário MUST manter o aviso de sucesso e o estado que impede uma segunda publicação
- **AND** a reinicialização MUST ocorrer somente na próxima entrada na página

#### Scenario: Navegação entre os passos preserva os dados
- **WHEN** a pessoa usa “Continuar” e “Voltar” para navegar entre os passos dentro de `/cadastro-doacao`
- **THEN** o sistema MUST NOT reiniciar o formulário durante essa navegação
- **AND** os dados preenchidos nos passos anteriores MUST permanecer preenchidos ao retornar a eles
- **AND** o reinício MUST ocorrer somente na entrada da página, inclusive ao recarregá-la
