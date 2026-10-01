## 1. Estado e dados demonstrativos

- [x] 1.1 Criar estado tipado de campanhas e fixtures identificadas como demonstração; validar tipos e filtragem por título/categoria.
- [x] 1.2 Adicionar seleção de campanha e estado de checkout para valores, anonimato, mensagem e método; verificar setters/handlers sem afirmar sucesso financeiro.

## 2. Componentes e páginas

- [x] 2.1 Criar cabeçalho Reflex com busca, filtro, CTA ligado ao formulário de itens existente e acesso de login; verificar compilação.
- [x] 2.2 Criar feed com hero, categorias, cards e progresso usando apenas fixtures marcadas; verificar filtro e navegação.
- [x] 2.3 Criar detalhe com imagem ilustrativa, criador, selo, abas e painel sticky; verificar conteúdo por campanha.
- [x] 2.4 Criar checkout visual com opções de valor, anonimato, mensagem, PIX e cartão sem processamento; verificar que nenhuma ação informa pagamento aprovado.
- [x] 2.5 Registrar rotas novas preservando a rota e os fluxos do catálogo atual; verificar navegação entre feed, detalhe e checkout.

## 3. Integração preparada e validação

- [x] 3.1 Deixar comentários nos pontos de integração GET/POST do Xano, sem chamar endpoints inexistentes; verificar ausência de escrita ou cobrança.
- [x] 3.2 Executar `reflex compile --dry` e corrigir erros de import, tipagem e componentes.
- [x] 3.3 Executar `openspec validate vaquinhas-online --strict` e conferir que todos os cenários correspondem ao escopo demonstrativo.
