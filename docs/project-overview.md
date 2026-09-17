# Project Overview — DoaFácil

## 1. Visão geral

O DoaFácil é uma plataforma web que conecta pessoas que desejam doar itens (roupas, alimentos, móveis, livros, etc.) a pessoas ou instituições que precisam deles. O objetivo é facilitar o processo de doação, tornando-o simples, rápido e acessível.

## 2. Problema

Muitas pessoas têm itens em bom estado que não usam mais, mas não sabem como ou para quem doar. Ao mesmo tempo, muitas pessoas ou instituições que precisam desses itens não têm um canal direto para encontrá-los. O DoaFácil resolve esse descompasso conectando doadores e interessados diretamente.

## 3. Objetivos

- Permitir que qualquer pessoa cadastre doações disponíveis.
- Permitir que interessados encontrem doações relevantes por categoria e localização.
- Facilitar a comunicação entre doador e interessado.
- Construir confiança na plataforma através de um sistema de avaliações.

## 4. Público-alvo / usuários

- Doadores: pessoas físicas que têm itens para doar.
- Interessados: pessoas físicas ou instituições que buscam itens doados.

## 5. Escopo

O sistema cobre o ciclo completo de uma doação: cadastro do item, demonstração de interesse, comunicação entre as partes, e avaliação após a doação ser concluída. Não cobre logística de entrega/transporte nem processamento de pagamentos (o DoaFácil trata apenas de doações, não de vendas).

## 6. Principais funcionalidades

- Cadastro e autenticação de usuários.
- Cadastro de doações, associadas a uma categoria e localização.
- Busca e filtro de doações por categoria e localização.
- Demonstração de interesse em uma doação.
- Troca de mensagens entre doador e interessado.
- Avaliação após a conclusão da doação.

## 7. Requisitos e restrições importantes

- O sistema deve funcionar via API completa (backend desacoplado do frontend).
- Regras de autorização (quem pode editar/excluir o quê) devem ser aplicadas no backend.
- A localização é usada para aproximar doador e interessado geograficamente.

## 8. Arquitetura tecnológica

- Backend: Xano (banco de dados, lógica de negócio e APIs).
- Frontend: Reflex (interface web em Python).
- Desenvolvimento apoiado por agentes de IA, utilizando OpenSpec para gerenciar mudanças.

## 9. Princípios de desenvolvimento

- Desenvolvimento incremental, com mudanças pequenas e verificáveis via OpenSpec.
- Reutilização de componentes e evitar duplicação de lógica.

## 10. Segurança e integridade

- Toda regra de autorização deve ser validada no backend (Xano), nunca apenas no frontend.
- Dados de contato entre usuários devem ser protegidos (não expostos publicamente).

## 11. Estratégia de desenvolvimento

O projeto será desenvolvido em mudanças (changes) incrementais via OpenSpec, começando pelo cadastro de usuários e doações, seguido por busca/interesse, mensagens e avaliações.

## 12. Fonte de verdade e documentação

Este documento e o `docs/domain-model.md` são a fonte de verdade sobre o domínio do projeto. Regras operacionais para os agentes de IA estão em `AGENTS.md`.
