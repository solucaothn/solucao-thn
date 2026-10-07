# Tasks

## 1. Decisões de design

- [x] 1.1 Atualizar `docs/design/README.md` com os textos, cartões, controles sem navegação, comportamento responsivo e conteúdo aprovado do rodapé; verificar que a lista não inclui os elementos removidos do Vakinha.

## 2. Seção Comece por aqui

- [x] 2.1 Implementar a seção Reflex após a ilustração das pessoas, com etiqueta, título, textos e três cartões aprovados; verificar que os dois primeiros mostram seta decorativa e que “Desapego em grupo” mostra “Em breve” sem seta, busca ou navegação.
- [x] 2.2 Adicionar verificações focadas do conteúdo e dos controles da seção; executar `python -m unittest discover -s tests -v` e confirmar que os três cartões e seus textos estão presentes sem busca ou destino navegável.

## 3. Seção institucional

- [x] 3.1 Implementar título, frase e quatro cartões institucionais com ícones, categorias, títulos e “Saiba mais”, em degradês verde e cinza e sem fotos ou vídeos; verificar os textos aprovados e que “Saiba mais” não navega.
- [x] 3.2 Adicionar verificações focadas dos quatro cartões e executar `python -m unittest discover -s tests -v`, confirmando o conteúdo e a ausência de destinos navegáveis.

## 4. Rodapé e responsividade

- [x] 4.1 Implementar o rodapé escuro com logotipo, título, oito links rápidos e identificação acadêmica; verificar visualmente o conteúdo e a ausência de selo, CNPJ, cidade, horário, “Busca por recibo” e “Verificação de links”.
- [x] 4.2 Verificar em tela estreita que os cartões de “Comece por aqui” e da seção institucional formam colunas legíveis; confirmar que setas e links continuam sem navegação.
- [x] 4.3 Executar `python -m unittest discover -s tests -v` e revisar a home completa para confirmar a ordem das seções, a preservação da home existente e a ausência de alterações no Xano.
