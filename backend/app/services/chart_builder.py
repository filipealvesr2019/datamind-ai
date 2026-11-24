"""Construtor Determinístico de Gráficos Plotly — DataMind AI
Gera especificações no padrão Plotly.js a partir dos dados tabulares retornados pelo banco.
Elimina a necessidade do LLM inventar estruturas de JSON, garantindo robustez e padronização.
"""

from typing import List, Dict, Any, Optional


PALETA_CORES = [
    "#3b82f6",  # Azul Royal
    "#8b5cf6",  # Roxo IA
    "#10b981",  # Verde Esmeralda
    "#f59e0b",  # Âmbar / Laranja
    "#ec4899",  # Rosa Moderno
    "#06b6d4",  # Ciano
    "#6366f1"   # Índigo
]


def construir_especificacao_grafico(
    tipo: str,
    dados: List[Dict[str, Any]],
    coluna_x: str,
    coluna_y: str,
    titulo: str,
    nome_serie: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """Constrói um objeto compatível com Plotly (data e layout).
    
    Args:
        tipo: 'bar', 'line', 'pie', 'donut'
        dados: Lista de dicionários resultantes do SQL
        coluna_x: Nome da coluna para eixo X (ou rótulo)
        coluna_y: Nome da coluna para eixo Y (ou valor)
        titulo: Título exibido no cabeçalho do gráfico
        nome_serie: Rótulo da legenda
    """
    if not dados:
        return None

    # Extrai valores para os eixos
    valores_x = [row.get(coluna_x, "") for row in dados]
    valores_y = [row.get(coluna_y, 0) for row in dados]

    tipo_normalizado = tipo.lower().strip()

    layout_base = {
        "title": {
            "text": titulo,
            "x": 0.5,
            "xanchor": "center",
            "font": {"family": "Inter, system-ui, sans-serif", "size": 14, "color": "#1e293b"}
        },
        "height": 320,
        "paper_bgcolor": "rgba(0,0,0,0)",
        "plot_bgcolor": "rgba(0,0,0,0)",
        "margin": {"l": 50, "r": 20, "t": 50, "b": 75},
        "autosize": True,
        "font": {"family": "Inter, system-ui, sans-serif", "color": "#64748b", "size": 11}
    }

    if tipo_normalizado == "bar":
        traces = [{
            "type": "bar",
            "x": valores_x,
            "y": valores_y,
            "name": nome_serie or coluna_y,
            "marker": {
                "color": PALETA_CORES[0],
                "line": {"color": "#1d4ed8", "width": 1}
            }
        }]
        layout_base["xaxis"] = {"gridcolor": "#f1f5f9", "tickangle": -25, "automargin": True}
        layout_base["yaxis"] = {"gridcolor": "#e2e8f0", "automargin": True}

    elif tipo_normalizado == "line":
        traces = [{
            "type": "scatter",
            "mode": "lines+markers",
            "x": valores_x,
            "y": valores_y,
            "name": nome_serie or coluna_y,
            "line": {"color": PALETA_CORES[1], "width": 3, "shape": "spline"},
            "marker": {"size": 7, "color": PALETA_CORES[1]}
        }]
        layout_base["xaxis"] = {"gridcolor": "#f1f5f9", "automargin": True}
        layout_base["yaxis"] = {"gridcolor": "#e2e8f0", "automargin": True}

    elif tipo_normalizado in ("pie", "donut"):
        # Agrupa automaticamente em "Top 5 + Outros" quando há muitas fatias para evitar poluição visual
        pares = []
        for lx, vy in zip(valores_x, valores_y):
            try:
                num = float(vy) if vy is not None else 0.0
            except (TypeError, ValueError):
                num = 0.0
            if num > 0:
                pares.append((str(lx), num))

        pares.sort(key=lambda item: item[1], reverse=True)
        if len(pares) > 6:
            top_5 = pares[:5]
            restante = pares[5:]
            soma_outros = round(sum(v for _, v in restante), 2)
            pares = top_5 + [(f"Outros ({len(restante)} itens)", soma_outros)]

        labels_limpos = [p[0] for p in pares]
        valores_limpos = [p[1] for p in pares]
        cores = [PALETA_CORES[i % len(PALETA_CORES)] for i in range(len(labels_limpos))]

        hole_size = 0.52 if tipo_normalizado == "donut" else 0.0
        traces = [{
            "type": "pie",
            "labels": labels_limpos,
            "values": valores_limpos,
            "hole": hole_size,
            "sort": False,
            "marker": {
                "colors": cores,
                "line": {"color": "#ffffff", "width": 2}
            },
            "textinfo": "percent",
            "textposition": "inside",
            "insidetextorientation": "horizontal",
            "textfont": {"size": 12, "color": "#ffffff"},
            "hovertemplate": "<b>%{label}</b><br>Valor: %{value:,.2f}<br>Participação: %{percent}<extra></extra>"
        }]
        layout_base["margin"] = {"l": 20, "r": 20, "t": 52, "b": 20}
        layout_base["legend"] = {
            "orientation": "v",
            "x": 1.02,
            "y": 0.5,
            "yanchor": "middle",
            "font": {"size": 11, "color": "#334155"}
        }

    else:
        # Fallback para gráfico de barras
        traces = [{
            "type": "bar",
            "x": valores_x,
            "y": valores_y,
            "marker": {"color": PALETA_CORES[0]}
        }]

    return {
        "data": traces,
        "layout": layout_base,
        "config": {"responsive": True, "displayModeBar": False}
    }
