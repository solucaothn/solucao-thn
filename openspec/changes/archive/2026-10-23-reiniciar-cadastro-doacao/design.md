# Design

## Context

Consulte `proposal.md` para a motivação e `specs/donation-creation/spec.md` para os comportamentos exigidos. `DonationCreateState.load_initial_data` é executado no `on_load` da rota `/cadastro-doacao` e atualmente atualiza dados remotos, mas não reinicia os campos locais. Os arquivos selecionados são mantidos pelo componente Reflex `rx.upload`, fora dos campos do estado Python.

## Goals / Non-Goals

**Goals:**

- Garantir que cada execução de `load_initial_data` comece uma visita nova e apague valores e estados de publicação anteriores.
- Limpar a seleção do componente de upload junto ao estado do formulário.
- Preservar a confirmação de sucesso e a proteção contra publicação duplicada até o usuário sair ou recarregar a página.
- Continuar carregando categorias e cidade/UF depois do reinício.

**Non-Goals:**

- Alterar login/logout, autenticação, Xano, regras de validação ou conteúdo do cadastro.
- Reiniciar o estado no momento de sucesso da publicação.
- Persistir rascunhos entre visitas.

## Decisions

### Reiniciar no evento de entrada

Colocar a reinicialização no início de `DonationCreateState.load_initial_data`, chamado pelo `on_load` de `/cadastro-doacao`. Assim, tanto uma nova navegação quanto o recarregamento executam o mesmo fluxo; não é necessário acoplar a limpeza ao login ou logout. A limpeza ocorre antes das requisições de categorias e perfil, mantendo os dados carregados pelo fluxo atual.

O reset fica exclusivamente no início de `load_initial_data`, acionado pelo `on_load`; os eventos de avançar (“Continuar”) e voltar (“Voltar”) não reinicializam o formulário. A navegação entre etapas deve preservar os valores já preenchidos, conforme o comportamento existente do wizard.

O reinício cobre passo atual, título, descrição, categoria e seu identificador, condição, entrega, preferência de contato, mensagens de erro e sucesso, flags de publicação/carregamento, progresso de upload e quaisquer outros valores exclusivos do formulário. Categorias e cidade/UF são repostas pelo carregamento normal da visita atual.

### Limpeza do componente de upload

Além de zerar estado Python, emitir a ação Reflex de limpar os arquivos selecionados pelo identificador `PHOTO_UPLOAD_ID` no carregamento da página. O estado do wizard e o estado cliente do `rx.upload` são distintos; limpar apenas os campos Python poderia deixar fotos da visita anterior selecionadas.

### Sucesso permanece até nova entrada

Não alterar o ramo de publicação bem-sucedida. `published` continua bloqueando avanço e nova publicação na visita atual, e `success_message` continua visível. Ao ocorrer a próxima entrada, o reset cria um formulário novo e libera o fluxo novamente.

**Alternativa considerada:** limpar os campos assim que a publicação termina. Rejeitada porque removeria a confirmação e poderia reabilitar o envio duplicado antes de o usuário iniciar explicitamente outra visita.

## Risks / Trade-offs

- **[O estado do upload no navegador não acompanha o reset do estado Python]** → acionar a limpeza do componente `rx.upload` no mesmo carregamento e verificar que o contador/nomes das fotos começam vazios.
- **[O reset apaga dados de um rascunho quando a página é recarregada]** → comportamento intencional desta change: cada entrada inicia um novo cadastro e não há persistência de rascunho aprovada.
- **[Falha ao carregar categorias ou perfil após a limpeza]** → manter o tratamento de erros atual; os campos do novo cadastro permanecem vazios e a interface continua podendo tentar carregar novamente.

## Migration Plan

1. Adicionar a reinicialização no início do carregamento da página e limpar o componente de upload.
2. Testar com unittest o reset, o carregamento de categorias e localização, a validação da primeira etapa e a exigência de foto na etapa 3.
3. Executar `python -m unittest discover -s tests -v` e `.venv\Scripts\reflex.exe compile --dry`.
4. Solicitar o teste manual do fluxo no navegador; o Copilot não marca essa tarefa como concluída.

Rollback: remover a reinicialização e a ação de limpar upload do evento de entrada, restaurando o comportamento anterior sem alterar dados persistidos ou o backend.
