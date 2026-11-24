"""Testes automatizados do construtor determinÃ­stico de grÃ¡ficos Plotly."""

import sys
import unittest
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent.parent.parent / "backend" / "app"
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from services.chart_builder import construir_especificacao_grafico


class TestChartBuilder(unittest.TestCase):
    def test_dados_vazios_retorna_none(self):
        spec = construir_especificacao_grafico("bar", [], "x", "y", "Vazio")
        self.assertIsNone(spec)

    def test_grafico_barras(self):
        dados = [{"nome": "Produto A", "qtd": 50}, {"nome": "Produto B", "qtd": 30}]
        spec = construir_especificacao_grafico("bar", dados, "nome", "qtd", "Top Produtos")
        self.assertEqual(spec["data"][0]["type"], "bar")
        self.assertEqual(spec["data"][0]["x"], ["Produto A", "Produto B"])
        self.assertEqual(spec["data"][0]["y"], [50, 30])
        self.assertEqual(spec["layout"]["paper_bgcolor"], "#ffffff")
        self.assertEqual(spec["layout"]["plot_bgcolor"], "#ffffff")

    def test_grafico_linha(self):
        dados = [{"dia": "2026-11-01", "total": 1000}, {"dia": "2026-11-02", "total": 2500}]
        spec = construir_especificacao_grafico("line", dados, "dia", "total", "Vendas DiÃ¡rias")
        self.assertEqual(spec["data"][0]["type"], "scatter")
        self.assertEqual(spec["data"][0]["mode"], "lines+markers")

    def test_grafico_pizza_agrupa_top5_mais_outros(self):
        dados = [{"nome": f"Item {i}", "valor": 1000 - i * 25} for i in range(15)]
        spec = construir_especificacao_grafico("pie", dados, "nome", "valor", "Vendas por Item")
        trace = spec["data"][0]
        self.assertEqual(trace["type"], "pie")
        self.assertEqual(len(trace["labels"]), 6)
        self.assertEqual(trace["labels"][-1], "Outros (10 itens)")
        self.assertEqual(trace["textinfo"], "percent")
        self.assertEqual(trace["textposition"], "inside")

    def test_grafico_rosca_tem_buraco_central(self):
        dados = [{"cat": "Hardware", "v": 400}, {"cat": "Software", "v": 600}]
        spec = construir_especificacao_grafico("donut", dados, "cat", "v", "Por Categoria")
        self.assertGreater(spec["data"][0]["hole"], 0)


if __name__ == "__main__":
    unittest.main()

