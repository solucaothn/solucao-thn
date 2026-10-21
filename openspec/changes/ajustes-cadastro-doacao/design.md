# Design

## Context

Consulte [proposal.md](./proposal.md) para o objetivo e a [delta da capability `donation-creation`](./specs/donation-creation/spec.md) para os requisitos. O wizard Reflex está concentrado em `doafacil/cadastro_doacao.py`: carrega as categorias do endpoint de catálogo, deriva as opções por `category_options`, mantém as constantes das condições, entrega e contato, valida por etapa e envia `delivery_method` em `POST catalog/donations/publish`.

O endpoint local `xano/api/catalog/catalog/donations/publish_POST.xs` declara `delivery_method` como enum com “Retirada”, “Entrega” e “A combinar”. O valor solicitado já é aceito pelo Xano, então esta proposta não requer mudança de backend. Os testes existentes estão em `tests/test_donation_creation.py`.

## Goals / Non-Goals

**Goals:**
- Manter o filtro de categorias, as opções de entrega e os ajustes de cor no escopo da interface de cadastro de doação.
- Confirmar por testes que os valores permitidos pelo frontend e enviados na publicação correspondem ao contrato atual.

**Non-Goals:**
- Excluir ou alterar categorias, endpoints, tabelas ou validações no Xano.
- Mudar as preferências de contato, as demais etapas ou o formato do payload da publicação.
- Criar novas páginas, rotas, dependências ou lógica fora do wizard existente.

## Decisions

### Filtrar categorias no limite do frontend

Excluir “Alimentos” e “Móveis” das opções apresentadas usando o resultado carregado pelo frontend, mantendo intactos o endpoint e os registros do catálogo. A lista usada pela seleção e pela validação local deve refletir as mesmas categorias visíveis, para que uma opção ocultada não permaneça elegível no estado do wizard. O Xano continua responsável por validar a existência da categoria na publicação.

Alternativa considerada: excluir categorias no Xano. Rejeitada porque o pedido limita o ajuste ao frontend e exige preservar os dados e o catálogo do backend.

### Usar uma única modalidade na interface sem mudar o contrato

Manter “A combinar” como único item da lista de entrega do wizard e como único valor local válido para avançar/publicar. Preservar o envio do campo `delivery_method`: o endpoint existente aceita “A combinar”, embora ainda permita também os valores legados “Retirada” e “Entrega”. A seleção continuará obrigatória e não será pré-selecionada automaticamente, mantendo o fluxo de validação atual.

Alternativa considerada: retirar a validação da modalidade por haver uma única opção. Rejeitada porque o passo hoje exige escolha explícita e sua validação evita publicar estado vazio ou inesperado.

### Escurecer somente os textos de exemplo e seleção

Aplicar uma cor de primeiro plano escura consistente aos placeholders, prompts/valores dos selects e opções de preferência de contato do quinto passo. Não redesenhar as mensagens explicativas, cabeçalho, cartões ou os demais elementos visuais dos passos. Os testes estruturais devem inspecionar os componentes e estilos referentes aos cinco passos, incluindo placeholder do campo, prompts de categoria/condição/entrega/contato e opções de contato.

Alternativa considerada: mudar a paleta global de cores da aplicação ou todos os textos auxiliares. Rejeitada para manter o ajuste cirúrgico aos textos descritos.

## Risks / Trade-offs

- [O catálogo pode acrescentar categorias novas ou variar capitalização] → Filtrar os nomes explicitamente solicitados, sem reconstruir ou congelar a lista de categorias; cobrir o filtro e a preservação das demais categorias por teste.
- [O componente Radix pode aplicar estilo visual próprio ao placeholder] → Validar os estilos dos prompts e textos selecionados no componente e ajustar o estilo local do select, sem depender de mudar o tema global.
- [O Xano ainda aceitará “Retirada” e “Entrega” em requisições fora deste frontend] → Isso é intencional nesta change, que restringe somente as opções da interface; nenhuma garantia de segurança ou regra do backend será presumida.

## Migration Plan

Não há migração nem publicação ao Xano. A implementação deverá alterar somente o frontend e seus testes; verificar por teste que o payload segue enviando “A combinar” e depois executar as verificações do projeto definidas nas tasks.
