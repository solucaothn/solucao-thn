# Design

## Context

Ver a motivação e o escopo em `proposal.md` e os contratos observáveis em `specs/public-donation-discovery/spec.md` e `specs/public-home/spec.md`.

O frontend Reflex ainda é a página inicial de exemplo. O Xano local já possui a tabela `donation`, com status, título, categoria e datas, além de uma listagem de catálogo ordenada por criação que aceita busca e categoria. Essa listagem não seleciona apenas doações disponíveis, não tem limite e não retorna foto ou condição. Essa change adiciona os campos e contratos necessários. `assets/` contém o logotipo e a imagem genérica; a ilustração de pessoas não foi entregue.

## Goals / Non-Goals

**Goals:**

- Manter o contrato atual de busca/listagem do catálogo inalterado, oferecendo operações específicas para a home.
- Fazer com que a consulta de cards e a contagem usem o mesmo critério de disponibilidade.
- Preservar a leitura de registros legados sem foto ou condição.
- Manter o frontend desacoplado do formato interno de armazenamento de arquivos do Xano.

**Non-Goals:**

- Implementar fluxo de upload de foto, formulário de doação, catálogo ou detalhe.
- Adicionar localização da doação nesta change.
- Definir fluxos de interesse, mensagem, avaliação ou administração.
- Publicar as mudanças no workspace Xano durante a implementação desta change sem a revisão do dry-run exigida pelo projeto.

## Decisions

1. **Adicionar campos opcionais no schema de doação.** A condição será restrita a Ótimo, Bom e Regular. A foto será armazenada usando o tipo de arquivo nativo do Xano, representada como opcional, após consultar e validar a sintaxe suportada pelo Xano Developer MCP. Não tornar os campos obrigatórios nem migrar registros existentes; assim, dados legados permanecem válidos. Um fluxo de upload e os formulários que preencherão os campos ficam para outra change.

2. **Criar contratos de leitura próprios para a home.** Manter a listagem existente, que já suporta busca e categoria, evita mudar comportamento do catálogo fora desta change. O novo endpoint de recentes será público, retornará somente as quatro doações disponíveis mais recentes, ordenadas por `created_at` decrescente, e incluirá apenas os dados necessários aos cards: identificador, data de criação, título, foto e condição. Foto será exposta como URL consumível pelo navegador ou valor nulo, nunca como detalhe interno do armazenamento. O endpoint de contagem será público e contará todas as doações disponíveis, independentemente do limite da listagem.

3. **Montar URLs públicas no Xano.** Uma foto será armazenada como arquivo público no tipo nativo de imagem do Xano. O endpoint montará sua URL completa com `$env.PUBLIC_BASE_URL` e o caminho persistido, sem expor a estrutura de storage ao Reflex. `PUBLIC_BASE_URL` é uma configuração não secreta que precisa conter apenas a origem da instância Xano; ela não deve ser embutida no código nem ser confundida com a URL base do endpoint de API.

4. **Usar um único critério de status para cards e estatística.** “Em circulação” significa status `disponível`, conforme os status já existentes no schema local. Doações reservadas e concluídas não entram nem na lista nem na contagem. Isso evita que o número mostrado pareça incompatível com os itens que a home oferece.

5. **Consumir ambos os endpoints pela camada de estado do Reflex.** A página carrega contagem e cards sem autenticação. Falha de uma operação não será convertida em zero ou lista vazia: cada seção comunica indisponibilidade sem fabricar conteúdo, permitindo que a outra seção continue utilizável. Lista vazia recebe estado vazio explícito.
   A variável `XANO_API_URL` deve conter a URL base do grupo de API Catalog; a página acrescenta os caminhos dos endpoints `catalog/donations/recent` e `catalog/donations/count`. Essa configuração de endpoint é distinta de `PUBLIC_BASE_URL`, usada pelo Xano para montar URLs das fotos.

6. **Derivar “NOVO” no frontend a partir de `created_at`.** Aplicar a janela de sete dias definida no design sem armazenar uma etiqueta derivada no Xano. A comparação usa o instante atual e não a data de atualização do registro.

7. **Renderizar fallback local para campos opcionais.** Foto ausente usa um recurso genérico local; condição ausente mostra “Condição não informada”. A foto genérica não será armazenada como se fosse a foto real da doação.

8. **Manter “Acessar” visível e sem destino nesta change.** Como não existe ainda tela de detalhe aprovada, o controle será apresentado sem link ou ação de navegação, evitando apontar para rota inexistente. A integração será feita quando catálogo/detalhe entrar no escopo.

9. **Usar os materiais visuais aprovados, sem reproduzir a captura inteira como interface.** A home será construída com componentes Reflex. `assets/logo.svg` e `assets/doacao-generica.svg` são os recursos disponíveis. A ilustração de pessoas ainda não chegou: omiti-la sem substituto e manter um TODO no código. Usar as cores dos recursos e as referências PNG enquanto o Figma não puder ser consultado; não introduzir fontes externas. Nesta sessão, o Figma respondeu HTTP 403, então a escolha exata de fontes fica pendente de acesso. A seção institucional e o rodapé escuro descritos no README são outra change.

## Risks / Trade-offs

- [O workspace Xano compartilhado pode divergir dos arquivos locais ou conter alterações concorrentes] → executar `xano workspace pull -d ./xano`, reconciliar as diferenças sem sobrescrever trabalho alheio e revisar `xano workspace push -d ./xano --dry-run`; não fazer push nesta change sem aprovação.
- [As origens Xano configuradas podem estar ausentes ou incorretas] → documentar `PUBLIC_BASE_URL` como configuração necessária para montar URL de foto e `XANO_API_URL` como URL base do grupo Catalog; não embutir uma origem presumida.
- [O endpoint público expõe conteúdo e imagens de doações] → retornar somente os campos aprovados para os cards, não incluir dados do doador ou identificadores pessoais e verificar que somente doações disponíveis e fotos destinadas à exibição pública são retornadas.
- [A contagem pode mudar entre chamadas concorrentes à lista e à contagem] → tratar os endpoints como leituras independentes; não prometer consistência transacional entre duas requisições distintas.
- [A ilustração de pessoas ainda não foi fornecida e o Figma está inacessível] → omitir a ilustração sem substituto, manter o TODO, usar referências locais sem introduzir dependência externa e ajustar tipografia exata quando o acesso ao Figma for restabelecido.

## Migration Plan

1. Sincronizar e revisar o workspace Xano antes de alterar sua representação local.
2. Adicionar os campos opcionais e os endpoints públicos; registros existentes sem valores devem continuar válidos e legíveis.
3. Validar XanoScript e cenários dos endpoints em ambiente de teste; revisar o plano `--dry-run` antes de qualquer publicação.
4. Implementar e verificar a home Reflex contra os contratos validados e as referências visuais.
5. Se a mudança de schema ou endpoints precisar ser revertida, retirar os endpoints e parar de consumir os campos novos. Não exigir migração destrutiva dos registros existentes; preservar campos e dados opcionais já gravados até uma decisão explícita de retenção.
