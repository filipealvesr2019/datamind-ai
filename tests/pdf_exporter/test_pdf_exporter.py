"""Testes automatizados do gerador de relatÃ³rios executivos em PDF."""

import base64
import io
import sys
import unittest
from pathlib import Path

from PIL import Image as PILImage
from pypdf import PdfReader

APP_DIR = Path(__file__).resolve().parent.parent.parent / "backend" / "app"
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from services.pdf_exporter import gerar_relatorio_pdf


def _criar_png_base64_teste() -> str:
    img = PILImage.new("RGB", (320, 180), color=(79, 70, 229))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode("ascii")


class TestPDFExporter(unittest.TestCase):
    def test_gera_pdf_valido_com_texto_grafico_e_tabela(self):
        dados = [
            {"produto": "Servidor Rack 1U Xeon", "faturamento": 333700.0},
            {"produto": "Notebook Pro 16", "faturamento": 67670.0},
        ]
        pdf_bytes = gerar_relatorio_pdf(
            pergunta="Quais os produtos mais vendidos em novembro?",
            resposta="## Resumo Executivo\n\nO faturamento atingiu **R$ 663.438,00**.\n- LideranÃ§a de Servidor Rack.",
            dados_tabela=dados,
            grafico_imagem_base64=_criar_png_base64_teste(),
        )

        self.assertTrue(pdf_bytes.startswith(b"%PDF-"))
        self.assertGreater(len(pdf_bytes), 1500)

        reader = PdfReader(io.BytesIO(pdf_bytes))
        self.assertGreaterEqual(len(reader.pages), 1)
        texto_extraido = "\n".join(page.extract_text() or "" for page in reader.pages)
        self.assertIn("DataMind AI", texto_extraido)
        self.assertIn("Servidor Rack 1U Xeon", texto_extraido)
        self.assertIn("663.438,00", texto_extraido)

    def test_ignora_imagem_corrompida_sem_falhar(self):
        pdf_bytes = gerar_relatorio_pdf(
            pergunta="Teste resiliente",
            resposta="Resumo executivo simples.",
            dados_tabela=[],
            grafico_imagem_base64="data:image/png;base64,INVALIDO!!!",
        )
        self.assertTrue(pdf_bytes.startswith(b"%PDF-"))
        reader = PdfReader(io.BytesIO(pdf_bytes))
        self.assertEqual(len(reader.pages), 1)


if __name__ == "__main__":
    unittest.main()

