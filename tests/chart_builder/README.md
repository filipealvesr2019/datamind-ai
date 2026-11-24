# Testes do Construtor de Gráficos (`test_chart_builder.py`)

Valida o serviço `backend/app/services/chart_builder.py`, responsável pela geração determinística de especificações Plotly.js.

## Cenários Cobertos

- **`test_dados_vazios_retorna_none`**: Garante que listas vazias retornam `None` sem lançar exceções.
- **`test_grafico_barras`**: Valida tipo `bar` e mapeamento correto dos eixos `x` e `y`.
- **`test_grafico_linha`**: Valida tipo `scatter` com modo `lines+markers`.
- **`test_grafico_pizza_agrupa_top5_mais_outros`**: Valida que gráficos de pizza com mais de 6 itens agrupam automaticamente em **Top 5 + `Outros (N itens)`**, exibindo apenas percentuais internos (`textinfo="percent"`, `textposition="inside"`).
- **`test_grafico_rosca_tem_buraco_central`**: Valida que o tipo `donut` aplica abertura central (`hole > 0`).

## Como Executar

```bash
python -m unittest tests/chart_builder/test_chart_builder.py -v
```
