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
            "font": {"family": "Inter, system-ui, sans-serif", "size": 14, "color": "#1e293b"}
        },
        "height": 260,
        "paper_bgcolor": "rgba(0,0,0,0)",
        "plot_bgcolor": "rgba(0,0,0,0)",
        "margin": {"l": 45, "r": 15, "t": 35, "b": 75},
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
        layout_base["xaxis"] = {"gridcolor": "#f1f5f9", "tickangle": -25}
        layout_base["yaxis"] = {"gridcolor": "#e2e8f0"}

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
        layout_base["xaxis"] = {"gridcolor": "#f1f5f9"}
        layout_base["yaxis"] = {"gridcolor": "#e2e8f0"}

    elif tipo_normalizado in ("pie", "donut"):
        hole_size = 0.55 if tipo_normalizado == "donut" else 0.0
        traces = [{
            "type": "pie",
            "labels": valores_x,
            "values": valores_y,
            "hole": hole_size,
            "marker": {"colors": PALETA_CORES[:len(valores_x)]},
            "textinfo": "label+percent",
            "insidetextorientation": "radial"
        }]

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
