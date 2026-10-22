# Proposal

## Why

Os cartões da home já apresentam doações disponíveis, mas o botão “Acessar” não leva a uma página com informações suficientes para conhecer o item. O Xano ainda não oferece uma consulta pública de detalhe por identificador que reúna os dados da doação, as fotos ordenadas, a categoria e uma identificação pública mínima de quem doa.

## What Changes

- Criar uma consulta pública no grupo Catalog para obter, por `donation_id`, somente doações existentes com status “disponível”.
- Retornar os dados aprovados para o detalhe: título, descrição, condição, nome da categoria, cidade/UF, forma de entrega, preferência de contato em texto, galeria em ordem e primeiro nome e cidade/UF de quem doa.
- Rejeitar localmente IDs de rota que não sejam inteiros positivos, sem chamar o Xano, e evitar imagens duplicadas na galeria quando a capa também estiver em `donation_photo`.
- Limitar a resposta do endpoint aos dados públicos necessários. Nunca retornar e-mail, sobrenome, `owner_id` ou endereço.
- Criar no Reflex a página `/doacao/<id>` com galeria, conteúdo do item e cartão mínimo de quem doa, incluindo estados de carregamento e erro para doação não encontrada ou indisponível.
- Fazer o botão “Acessar” dos cartões da home navegar para o detalhe da doação correspondente.
- Atualizar a documentação de design para descrever a página única, identificar as imagens 14 e 15 como página inteira e topo, respectivamente, e registrar os elementos omitidos.
- Incluir testes `unittest` para contrato e interpretação segura da resposta, ID inválido sem chamada ao Xano, deduplicação da galeria, estados da página e navegação da home, incluindo verificações de ausência de dados privados; prever verificação manual no painel e no navegador após publicação.

## Capabilities

### New Capabilities

- `donation-detail`: consulta pública segura e apresentação dos detalhes de uma doação disponível.

### Modified Capabilities

- `public-home`: o botão “Acessar” dos cartões passa a navegar para a página de detalhe da respectiva doação.

## Impact

- **Xano:** novo endpoint somente de leitura no grupo Catalog, sem autenticação, com entrada `donation_id`; o caminho proposto é `/catalog/donations/detail`. O sufixo estático `detail` evita sobreposição com as rotas existentes `/catalog/donations/recent`, `/catalog/donations/count` e `/catalog/donations/status`, e não altera o endpoint de listagem `/catalog/donations`.
- **Reflex:** página e estado novos para carregar e validar a resposta do endpoint; alteração pontual do botão “Acessar” na home.
- **Testes:** novos testes unitários seguindo `unittest` e os padrões de mocks HTTP já usados pela home.
- **Documentação:** nova seção de detalhe em `docs/design/README.md` e novas/alteradas specs OpenSpec.
- **Fora do escopo:** login obrigatório, mensagens/chat, perfil público completo, avaliações, histórico, novos campos de características, endereço, bairro, CEP, status adicional e qualquer alteração aos endpoints existentes.

Esta etapa cria apenas os artifacts da change. A implementação do endpoint Xano ficará para o apply; antes de qualquer edição de `xano/`, será feito o pull do workspace e, antes de qualquer push real, o dry-run será revisado e o grupo avisado.

Antes de executar `xano workspace pull -d ./xano` ou qualquer push real, o Copilot deve parar e pedir confirmação explícita ao usuário. A saída completa do dry-run deve ser apresentada para revisão.
