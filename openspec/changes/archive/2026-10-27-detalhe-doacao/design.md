# Design

## Context

Veja `proposal.md` para a motivação e as specs desta change para os comportamentos observáveis. A home consome a lista pública de `/catalog/donations/recent`; o botão “Acessar” ainda não navega. O grupo Catalog já possui rotas estáticas para `/catalog/donations/recent`, `/catalog/donations/count` e `/catalog/donations/status`. As tabelas `donation`, `donation_photo`, `category` e `user` contêm os dados necessários, mas não existe consulta pública que os reúna para uma doação.

O cadastro de doação define cidade e estado na própria doação. A tabela `user` contém também nome e e-mail, mas não há perfil público. Reflex já tem chamadas HTTP simuláveis com `httpx.MockTransport` nos testes da home. Não foi encontrado padrão de página Reflex dinâmica neste projeto.

## Goals / Non-Goals

**Goals:**

- Buscar uma doação específica disponível e os dados necessários à tela em uma única chamada pública.
- Limitar no Xano os dados do doador retornados ao primeiro nome; reutilizar cidade/UF persistidas na doação.
- Implementar a página de detalhe e ligar a ela o botão “Acessar” da home.
- Descrever no README de design uma única página, com as imagens 14 e 15 identificadas corretamente.

**Non-Goals:**

- Criar ou alterar campos/tabelas, rotas existentes ou estados da doação.
- Criar chat, perfil público, avaliações, histórico, presença, verificação de conta ou novos meios de contato.
- Alterar o comportamento público da home além da navegação do botão “Acessar”.

## Decisions

### Endpoint estático no grupo Catalog

Criar `GET /catalog/donations/detail` com entrada obrigatória `donation_id`. O endpoint exige que a doação exista e tenha status “disponível”; os casos inexistente e indisponível usam a mesma resposta HTTP 404 e o mesmo erro público de não encontrada. O frontend continua usando a base `XANO_API_URL` já adotada pela home.

**Alternativas consideradas:** usar uma rota com ID no caminho, como `/catalog/donations/{id}`, ou ampliar `/catalog/donations`. A rota estática com ID como entrada evita depender de roteamento dinâmico no Xano e não conflita com os caminhos estáticos `recent`, `count` e `status`; ampliar a listagem poderia alterar seu contrato para os consumidores atuais.

### Resposta por lista permitida

O endpoint compõe a resposta usando uma lista explícita de campos: identificador e título da doação; descrição, condição e modalidade/preferência de contato; nome da categoria; cidade/UF da doação; URLs públicas das fotos; e primeiro nome de quem doa. O primeiro nome é derivado do campo `user.name` no backend. A localização exibida no cartão de quem doa reutiliza cidade/UF da doação, evitando expor ou consultar localização adicional da conta.

A resposta não inclui o registro da conta nem os campos `email`, sobrenome, `owner_id`, endereço, bairro ou CEP. Não retorna estado da doação, pois somente registros disponíveis podem ser consultados.

**Alternativa considerada:** retornar o objeto completo de `user` ou `donation` e filtrar no Reflex. Rejeitada: o cliente não é limite de segurança, e uma mudança futura nos campos poderia expor dados pessoais.

### Composição e ordem da galeria

Quando a capa existe, ela é a primeira foto; em seguida vêm os registros de `donation_photo` ordenados por `position` crescente. A publicação atual grava a primeira imagem tanto em `donation.photo` quanto em `donation_photo` na posição 1. Portanto, a resposta do detalhe ou o mapeamento do cliente deve deduplicar referências à mesma imagem (comparando a identidade/caminho estável do arquivo), mantendo a capa uma única vez e preservando a ordem das demais fotos. Cada caminho de imagem é convertido em URL pública conforme o padrão já usado pelo endpoint de doações recentes. Se nenhuma foto existir, o frontend usa o recurso genérico já utilizado na home.

### Rota e estado Reflex

Registrar a rota Reflex dinâmica `/doacao/[id]`, correspondente à URL pública `/doacao/<id>`, e obter o identificador dos parâmetros da página pelo mecanismo da versão Reflex instalada. Antes de formar a requisição, validar que o segmento consiste somente em dígitos e representa um inteiro maior que zero; caso contrário, apresentar “Doação não encontrada” sem chamar o Xano. O estado carrega a resposta pelo endpoint de detalhe e mantém estados separados de carregamento, não encontrada e falha de rede/resposta inválida. Respostas são validadas e mapeadas para campos de apresentação permitidos; campos extras recebidos por engano não são armazenados no estado nem renderizados. IDs válidos sem resultado, como `999999`, seguem para o Xano e usam a resposta de não encontrada.

O botão “Acessar” recebe a navegação para `/doacao/<id>`. O conteúdo principal aplica `page-fade-enter`; cabeçalho e dados carregados não são animados, e a regra de movimento reduzido existente deve continuar desativando a animação.

### Layout a partir da referência aprovada

Tratar as imagens como duas vistas da mesma página: `14-detalhe-doacao.png` é a página inteira após rolagem e `15-detalhe-doacao-resumido.png` é o topo sem rolar. O layout mantém cabeçalho branco com logo, fundo creme, galeria e resumo do item no topo, seguido por detalhes/localização e cartão mínimo de quem doa. O texto sobre a preferência de contato é informativo, não um botão ou mecanismo de chat.

No README, registrar que Cor, Material, Tipo, bairro, CEP, avaliações, histórico, Online, indicadores de verificação, avatar e ações Chat, Outros meios de comunicação e Acessar perfil ficam ocultos por não terem dados ou funcionalidades aprovados nesta etapa.

### Verificação e implantação do Xano

Antes de editar `xano/`, conferir o estado da árvore e registrar que os oito arquivos Xano preexistentes diferem somente por LF/CRLF do último pull; eles não entram em commit e podem ser reescritos pelo pull. Antes de executar `xano workspace pull -d ./xano`, o Copilot para e pede confirmação explícita ao usuário, prosseguindo somente após a confirmação.

Validar todos os arquivos `.xs` novos no MCP. Executar `xano workspace push -d ./xano --dry-run` e apresentar a saída completa; revisar o escopo, avisar o grupo e obter autorização antes de preparar o push real. Imediatamente antes de qualquer push real, parar e pedir confirmação explícita ao usuário. Após confirmação, publicar somente o endpoint novo; em seguida, conferir no painel e na rota pública a resposta para doação disponível e para inexistente/indisponível. Se qualquer dado privado aparecer, remover o endpoint novo imediatamente como rollback. O Copilot não marca essas verificações manuais como concluídas.

## Risks / Trade-offs

- **[Exposição acidental de dados pessoais na API pública]** → construir a resposta no backend por lista permitida, revisar o JSON no painel do Xano e testar explicitamente que e-mail, sobrenome, `owner_id` e endereço não aparecem.
- **[Uma doação pode deixar de estar disponível entre a listagem da home e a abertura do detalhe]** → o endpoint revalida o status e a página apresenta a mesma mensagem genérica de não encontrada.
- **[Caminho de imagem indisponível ou sem configuração de URL pública]** → seguir o contrato já usado por `/catalog/donations/recent`, expor falha como erro e não inventar fotos.
- **[A capa também é persistida como foto adicional pela publicação atual]** → deduplicar pelo identificador/caminho estável do arquivo antes de montar a galeria e testar o caso em que a capa coincide com a primeira foto adicional.
- **[ID inválido pode provocar consulta desnecessária ou erro de conversão]** → validar inteiro positivo antes de qualquer chamada HTTP e testar que IDs inválidos não acionam o cliente Xano.
- **[Estado Xano da árvore de trabalho já modificado]** → preservar os oito arquivos preexistentes e não fazer pull/push enquanto não houver uma forma segura de manter essas alterações.
- **[Versão Reflex e rota dinâmica]** → confirmar os parâmetros de rota e compilar com a versão instalada antes de concluir a tarefa de frontend.

## Migration Plan

1. Revisar o estado da árvore; antes de executar `xano workspace pull -d ./xano`, pedir confirmação explícita ao usuário e só então fazer o pull.
2. Consultar a documentação no Xano Developer MCP; criar e validar o endpoint público sem modificar tabelas nem endpoints existentes.
3. Executar `xano workspace push -d ./xano --dry-run`, apresentar a saída completa, revisar o escopo, avisar o grupo e obter autorização.
4. Imediatamente antes do push real, pedir confirmação explícita ao usuário; após confirmar, publicar somente o endpoint novo.
5. Conferir manualmente no painel do Xano e na rota pública os resultados para doação disponível, inexistente e indisponível, verificando fotos sem repetição e ausência de dados privados. Se aparecer dado privado, remover o endpoint novo imediatamente. O Copilot não marca tarefas manuais como concluídas.
6. Implementar e testar o estado, a página dinâmica e a navegação da home; executar os testes automatizados e `.venv\Scripts\reflex.exe compile --dry`. Para rollback do frontend, reverter pela change sem alterar dados de doações.

## Open Questions

Nenhuma decisão de produto permanece aberta nesta proposta.
