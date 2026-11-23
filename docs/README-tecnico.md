# DoaFácil — Documentação técnica

Porta de entrada para quem desenvolve o DoaFácil. O manual de uso, para quem usa o site, é o [README da raiz](../README.md).

## Stack

- **Frontend:** [Reflex](https://reflex.dev) (Python), em `doafacil/`. É a única tecnologia de frontend do projeto.
- **Backend:** Xano (plano gratuito), com banco, autenticação, regras de negócio e APIs. A pasta `xano/` é a cópia local do workspace, sincronizada pelo Xano CLI.
- **E-mail:** SendGrid, chamado pelo Xano.
- **Especificação:** [OpenSpec](https://github.com/Fission-AI/OpenSpec), em `openspec/`.
- **Testes:** `unittest`, em `tests/`.

## Como rodar

```
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:XANO_API_URL = "<endereço do grupo Catalog>"
$env:XANO_AUTH_API_URL = "<endereço do grupo Authentication>"
reflex run
```

Abra `http://localhost:3000`. As duas variáveis são os endereços base dos grupos de API do Xano; peça ao grupo e nunca as coloque em arquivo versionado. Os segredos (como `SENDGRID_API_KEY`) ficam só nas variáveis do workspace do Xano.

## Testes

```
python -m unittest discover -s tests -v
```

Os scripts `scripts/teste_*_real.py` conferem os endpoints contra o Xano real; veja o guia do colaborador antes de rodá-los.

## Estrutura

| Pasta ou arquivo | Conteúdo |
|---|---|
| `doafacil/` | Páginas, estados e componentes do Reflex |
| `assets/` | CSS, imagens, ícones e componentes React próprios |
| `tests/` | Testes automatizados |
| `scripts/` | Testes contra o Xano real e utilitários |
| `xano/` | Cópia local do workspace do Xano (XanoScript) |
| `openspec/` | Specs principais e changes, ativas e arquivadas |
| `docs/` | Documentação (lista abaixo) |
| `AGENTS.md` | Regras para agentes de código |

## Documentos

- [Guia do colaborador](guia-do-colaborador.md): como trabalhar no projeto, decisões já tomadas, cada funcionalidade em detalhe e problemas comuns. **Leia antes de mexer no código.**
- [Visão geral do projeto](project-overview.md): escopo e restrições.
- [Modelo de domínio](domain-model.md): conceitos e relacionamentos.
- [Design](design/README.md): telas de referência e diferenças aprovadas em relação ao Figma.
- [AGENTS.md](../AGENTS.md): fluxo com OpenSpec, Git e Xano.
- [Manual de uso](../README.md) e as capturas em `docs/manual/`.
