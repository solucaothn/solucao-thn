# Tasks

## 1. Decisões de design

- [x] 1.1 Atualizar `docs/design/README.md` com os textos, cartões, controles sem navegação, comportamento responsivo e conteúdo aprovado do rodapé; verificar que a lista não inclui os elementos removidos do Vakinha.

## 2. Seção Comece por aqui

- [x] 2.1 Implementar a seção Reflex após a ilustração das pessoas, com etiqueta, título, textos, três cartões e barra de busca apenas visual; verificar que os dois primeiros cartões mostram seta decorativa e que “Desapego em grupo” mostra “Em breve” sem seta ou navegação.
- [x] 2.2 Adicionar verificações focadas do conteúdo e dos controles da seção; executar `python -m unittest discover -s tests -v` e confirmar que os três cartões e a barra visual estão presentes sem busca funcional ou destino navegável.

## 3. Seção institucional

- [x] 3.1 Implementar título, frase e quatro cartões institucionais com ícones, categorias, títulos e “Saiba mais”, em degradês verde e cinza e sem fotos ou vídeos; verificar os textos aprovados e que “Saiba mais” não navega.
- [x] 3.2 Adicionar verificações focadas dos quatro cartões e executar `python -m unittest discover -s tests -v`, confirmando o conteúdo e a ausência de destinos navegáveis.

## 4. Rodapé e responsividade

- [x] 4.1 Implementar o rodapé escuro com logotipo, título, oito links rápidos e identificação acadêmica; verificar visualmente o conteúdo e a ausência de selo, CNPJ, cidade, horário, “Busca por recibo” e “Verificação de links”.
- [x] 4.2 Verificar em tela estreita que os cartões de “Comece por aqui” e da seção institucional formam colunas legíveis; confirmar que setas e links continuam sem navegação.
- [x] 4.3 Executar `python -m unittest discover -s tests -v` e revisar a home completa para confirmar a ordem das seções, a preservação da home existente e a ausência de alterações no Xano.

## 5. Ajustes após revisão visual

- [x] 5.1 Atualizar a spec, o design e `docs/design/README.md` para registrar a ilustração em largura total sem faixa entre seções, a frase de destaque e a barra visual de busca sem ação, além do contato e do layout compacto do rodapé.
- [x] 5.2 Ajustar a ilustração para encostar à base da seção; incluir a frase de apoio e a barra visual com campo, seletores e botão inertes; verificar os textos, a ordem e o empilhamento dos controles em tela estreita.
- [x] 5.3 Acrescentar “Fale conosco” ao rodapé em coluna ao lado dos links rápidos, com tipografia e espaçamento reduzidos e layout empilhado em telas estreitas; atualizar testes e executar `python -m unittest discover -s tests -v`.

## 6. Ajustes de altura da primeira tela e refinamento visual

- [x] 6.1 Atualizar esta change, a spec, o design e `docs/design/README.md` para documentar a primeira tela ocupando no mínimo 100vh com ilustração no limite inferior, os espaçamentos e alinhamento de “Comece por aqui”, os controles de busca com aparência ativa e o logotipo colorido e tipografia menor no rodapé.
- [x] 6.2 Implementar os ajustes visuais em Reflex e ampliar os testes para cobrir a composição de primeira dobra, espaçamentos e alinhamento dos cartões, aparência da busca e tratamento do logotipo/rodapé; executar `python -m unittest discover -s tests -v` e conferir os layouts estreito e largo.

## 7. Refinamento de “Comece por aqui”

- [x] 7.1 Atualizar a spec, o design, as tarefas e `docs/design/README.md` com o padding superior reduzido, line-height dos textos e contraste explícito do placeholder e seletores da busca visual.
- [x] 7.2 Ajustar os estilos da seção e da busca visual, atualizar testes sem modificar a primeira dobra ou comportamento, e executar `python -m unittest discover -s tests -v`.

## 8. Ajustes visuais após verificação no navegador

- [x] 8.1 Atualizar spec, design, tarefas e `docs/design/README.md` com os novos espaçamentos da seção, estilos explícitos do placeholder e tipografia do rodapé.
- [x] 8.2 Aplicar os estilos apenas nas áreas solicitadas, atualizar testes, executar `python -m unittest discover -s tests -v` e confirmar por Playwright os estilos computados e as distâncias em pixels, sem modificar a primeira dobra ou comportamento.
