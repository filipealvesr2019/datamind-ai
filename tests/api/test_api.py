"""Testes automatizados de integraÃ§Ã£o da API FastAPI â€” DataMind AI."""

import io
import sys
import unittest
from pathlib import Path

from fastapi.testclient import TestClient
from pypdf import PdfReader

APP_DIR = Path(__file__).resolve().parent.parent.parent / "backend" / "app"
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from main import app


class TestDataMindAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_kpis_dashboard(self):
        res = self.client.get("/api/kpis")
        self.assertEqual(res.status_code, 200)
        body = res.json()
        for campo in ("faturamento_total", "vendas_concluidas", "ticket_medio", "inadimplencia_total"):
            self.assertIn(campo, body)
        self.assertGreater(body["faturamento_total"], 0)

    def test_vendas_mensais(self):
        res = self.client.get("/api/dashboard/vendas-mensais")
        self.assertEqual(res.status_code, 200)
        dados = res.json()
        self.assertIsInstance(dados, list)
        self.assertGreater(len(dados), 0)
        self.assertIn("mes", dados[0])
        self.assertIn("faturamento", dados[0])

    def test_top_produtos(self):
        res = self.client.get("/api/dashboard/top-produtos")
        self.assertEqual(res.status_code, 200)
        dados = res.json()
        self.assertEqual(len(dados), 5)

    def test_audit_endpoint(self):
        res = self.client.get("/api/audit?limite=5")
        self.assertEqual(res.status_code, 200)
        self.assertIsInstance(res.json(), list)

    def test_export_pdf_endpoint(self):
        payload = {
            "pergunta": "Resumo de faturamento",
            "resposta": "O faturamento total foi de **R$ 6.078.857,00**.",
            "dados_tabela": [{"mes": "2026-11", "faturamento": 663438.0}],
            "grafico_imagem_base64": None,
        }
        res = self.client.post("/api/export/pdf", json=payload)
        self.assertEqual(res.status_code, 200)
        self.assertIn("application/pdf", res.headers.get("content-type", ""))
        self.assertTrue(res.content.startswith(b"%PDF-"))

        reader = PdfReader(io.BytesIO(res.content))
        texto = "\n".join(p.extract_text() or "" for p in reader.pages)
        self.assertIn("6.078.857,00", texto)

    def test_export_pdf_rejeita_vazio(self):
        res = self.client.post("/api/export/pdf", json={"pergunta": "x", "resposta": "   "})
        self.assertEqual(res.status_code, 400)

    def test_chat_rejeita_pergunta_vazia(self):
        res = self.client.post("/api/chat", json={"pergunta": "   "})
        self.assertEqual(res.status_code, 400)

    def test_crud_conversas_api(self):
        # Cria conversa
        res_create = self.client.post("/api/conversas", json={"titulo": "Teste API Conversa"})
        self.assertEqual(res_create.status_code, 200)
        cid = res_create.json()["id"]

        # Lista e verifica presença
        res_list = self.client.get("/api/conversas")
        self.assertEqual(res_list.status_code, 200)
        self.assertTrue(any(c["id"] == cid for c in res_list.json()))

        # Obtém detalhes
        res_get = self.client.get(f"/api/conversas/{cid}")
        self.assertEqual(res_get.status_code, 200)
        self.assertEqual(res_get.json()["titulo"], "Teste API Conversa")

        # Exclui e confirma 404 depois
        res_del = self.client.delete(f"/api/conversas/{cid}")
        self.assertEqual(res_del.status_code, 200)
        self.assertEqual(self.client.get(f"/api/conversas/{cid}").status_code, 404)

    def test_frontend_estatico_e_funcoes_exportacao(self):
        res_html = self.client.get("/")
        self.assertEqual(res_html.status_code, 200)
        self.assertIn("DataMind AI", res_html.text)
        self.assertIn("chat-history-list", res_html.text)

        res_js = self.client.get("/js/app.js")
        self.assertEqual(res_js.status_code, 200)
        for fn in ("exportarPDF", "exportarCSV", "exportarPNG", "carregarListaConversas", "selecionarConversa"):
            self.assertIn(fn, res_js.text)


if __name__ == "__main__":
    unittest.main()

