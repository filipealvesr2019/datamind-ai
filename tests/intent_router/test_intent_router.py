"""Testes automatizados do Intent Router (estrutura, formatação de histórico e fallback)."""

import sys
import unittest
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent.parent.parent / "backend" / "app"
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from agent.intent_router import IntentDecision, _formatar_historico, classificar_intencao


class TestIntentRouter(unittest.TestCase):
    def test_formatar_historico_vazio(self):
        self.assertEqual(_formatar_historico(None), "(Sem histórico anterior)")
        self.assertEqual(_formatar_historico([]), "(Sem histórico anterior)")

    def test_formatar_historico_com_mensagens(self):
        hist = [
            {"role": "user", "content": "crie um grafico de pizza"},
            {"role": "assistant", "content": "Deseja dividir por categoria ou vendedor?"},
        ]
        formatado = _formatar_historico(hist)
        self.assertIn("Usuário: crie um grafico de pizza", formatado)
        self.assertIn("Assistente: Deseja dividir por categoria ou vendedor?", formatado)

    def test_modelo_intent_decision(self):
        dec = IntentDecision(
            intencao="esclarecimento",
            esta_claro=False,
            intencao_consolidada="Gráfico de pizza sem dimensão",
            pergunta_esclarecimento="Prefere dividir por categoria ou vendedor?",
        )
        self.assertEqual(dec.intencao, "esclarecimento")
        self.assertFalse(dec.esta_claro)

    def test_fallback_seguro_sem_modelos_validos(self):
        dec = classificar_intencao(
            pergunta="Qual o faturamento total?",
            historico=[],
            api_key="chave-invalida",
            modelos_candidatos=[],
        )
        self.assertEqual(dec.intencao, "consulta_dados")
        self.assertTrue(dec.esta_claro)
        self.assertEqual(dec.intencao_consolidada, "Qual o faturamento total?")


if __name__ == "__main__":
    unittest.main()
