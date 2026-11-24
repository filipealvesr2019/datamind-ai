# Suíte de Testes Automatizados — DataMind AI

Esta pasta reúne os testes automatizados da plataforma **DataMind AI**, organizados por domínio, com documentação individual (`README.md`) em cada subpasta.

## Estrutura

| Pasta | Escopo | Documentação |
| :--- | :--- | :--- |
| `tests/api/` | Endpoints FastAPI (KPIs, dashboard, auditoria, PDF, chat e frontend) | [README.md](api/README.md) |
| `tests/chart_builder/` | Construtor determinístico de gráficos Plotly (`bar`, `line`, `pie`, `donut` e `Top 5 + Outros`) | [README.md](chart_builder/README.md) |
| `tests/intent_router/` | Roteador de intenções, formatação de histórico e fallback seguro | [README.md](intent_router/README.md) |
| `tests/pdf_exporter/` | Geração de relatórios executivos em PDF com texto, tabela e gráfico | [README.md](pdf_exporter/README.md) |
| `tests/sql_security/` | Camada de segurança SQL via AST (`sqlglot`), whitelisting e `LIMIT` | [README.md](sql_security/README.md) |

## Como Executar Todos os Testes

Na raiz do projeto:

```bash
python -m unittest discover -s tests -v
```
