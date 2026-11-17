# Proposal

## Why

As páginas do site ainda mostram placeholders em degradê onde o Figma tem fotos. O grupo começou a trazer as fotos, e as primeiras são as da `/quem-somos` e da `/seguranca`. A spec atual proíbe fotos de banco de imagens nessas páginas, então a troca precisa mudar os requisitos e exigir o crédito quando a licença pede.

## What Changes

- **`/quem-somos`:** a foto exportada do Figma (nó 354:851, retângulo de 375 × 421) fica no lugar do placeholder ao lado da frase de missão, com o crédito “Foto: Freepik” abaixo.
- **`/seguranca`:** a foto exportada do Figma (nó 406:1243, retângulo “image 16” de 507 × 339) fica no lugar do placeholder ao lado do texto de apresentação, com o crédito “Foto: Freepik” abaixo.
- **As duas fotos:**
  - usam o mesmo componente de foto com crédito;
  - mantêm a proporção do Figma e usam `object-fit: cover`;
  - têm um texto alternativo descritivo em português.
- **Conversão:** as duas fotos são convertidas para JPEG, com qualidade de cerca de 82, sem metadados e com o mesmo tamanho em pixels.
  - Se o PNG tiver os cantos transparentes, eles não vão para o JPEG; os cantos arredondados vêm do CSS (`border-radius`).
  - Só os `.jpg` entram no commit. Os PNGs originais ficam fora dele.
- **Previsto para esta mesma change, mas fora do escopo agora:** as fotos dos blocos verdes do Sobre nós e dos 4 cartões institucionais da home. Elas entram depois, por uma atualização desta change, quando os arquivos existirem.
- **Fora do escopo:** qualquer mudança no Xano.

## Capabilities

### New Capabilities

Nenhuma.

### Modified Capabilities

- `institutional-pages`:
  - o requisito “Quem somos” passa a pedir a foto ao lado da frase de missão;
  - o requisito “Segurança e transparência” passa a pedir a foto ao lado do texto de apresentação;
  - nos dois, a foto tem texto alternativo e crédito visível, no lugar de “placeholder, sem foto de banco de imagens”.

## Impact

- `doafacil/institucional.py`:
  - componente de foto com crédito;
  - `about_page` e `security_page`;
  - o `_placeholder` sai, porque fica sem uso.
- **Arquivos novos:** `assets/sobre/quem-somos.jpg` e `assets/seguranca/seguranca.jpg`, convertidos dos PNGs do Higor.
- `tests/test_institucional.py`: testes das fotos, do `alt`, do crédito e dos JPEGs.
- `docs/design/README.md`: as linhas da Quem somos e da Segurança.
- **Sem mudanças** no Xano, nas APIs nem nas dependências. O Pillow, usado na conversão e nos testes, já está no `requirements.txt`.
