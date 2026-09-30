## 1. Navegação e dados de demonstração

- [x] 1.1 Adicionar localidade fictícia às campanhas de exemplo e filtrar por palavra-chave, categoria e localidade; verificar correspondência e resultados vazios.
- [x] 1.2 Atualizar destinos dos links de entrada e criação de doação para `/app`; verificar que os fluxos existentes continuam acessíveis.

## 2. Landing pública

- [x] 2.1 Criar cabeçalho público com âncoras, busca e CTAs distintos.
- [ ] 2.1a Verificar destinos e layout do cabeçalho em viewport desktop e móvel.
- [x] 2.2 Criar hero, bloco de busca/descoberta e cartões demonstrativos; confirmar no registro da rota que `/` não depende de chamadas Xano.
- [x] 2.3 Criar seção institucional de confiança e rodapé com links/canais identificados honestamente.
- [ ] 2.3a Verificar responsividade da landing e conteúdo no navegador.
- [x] 2.4 Mover a tela atual de autenticação/perfil/catálogo para `/app` e adicionar aviso sobre criação financeira indisponível.
- [ ] 2.4a Verificar login, hidratação e âncora de cadastro no navegador.
- [x] 2.5 Registrar `/` como landing pública sem `on_load` de backend, preservando `/vaquinhas`, detalhe e checkout.
- [ ] 2.5a Verificar navegação entre as rotas no navegador.

## 3. Validação

- [x] 3.1 Executar `reflex compile --dry` e corrigir erros de imports, tipagem ou componentes.
- [x] 3.2 Executar `openspec validate landing-page-publica --strict`.
- [ ] 3.2a Revisar a landing e os fluxos preservados no navegador.
