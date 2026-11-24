"""Testes automatizados da persistência de conversas do chat em SQLite."""

import sys
import tempfile
import unittest
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent.parent.parent / "backend" / "app"
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from services.chat_storage import (
    criar_conversa,
    excluir_conversa,
    init_chat_tables,
    listar_conversas,
    obter_conversa,
    salvar_mensagem,
)


class TestChatStorage(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.db_path = Path(self._tmpdir.name) / "test_chat.db"
        init_chat_tables(self.db_path)

    def tearDown(self):
        self._tmpdir.cleanup()

    def test_criar_e_listar_conversas(self):
        c1 = criar_conversa("Análise Q4", db_path=self.db_path)
        c2 = criar_conversa("Nova conversa", db_path=self.db_path)
        lista = listar_conversas(db_path=self.db_path)
        self.assertEqual(len(lista), 2)
        ids = {item["id"] for item in lista}
        self.assertEqual(ids, {c1["id"], c2["id"]})

    def test_salvar_mensagens_e_titulo_automatico(self):
        conversa = criar_conversa(db_path=self.db_path)
        cid = conversa["id"]

        salvar_mensagem(cid, "user", "Quais os 5 produtos mais vendidos?", db_path=self.db_path)
        salvar_mensagem(
            cid,
            "assistant",
            "Os 5 produtos mais vendidos foram...",
            intencao="gerar_grafico",
            grafico={"data": [{"type": "bar"}], "layout": {}, "config": {}},
            dados_tabela=[{"nome": "Produto A", "qtd": 120}],
            db_path=self.db_path,
        )

        carregada = obter_conversa(cid, db_path=self.db_path)
        self.assertIsNotNone(carregada)
        self.assertEqual(carregada["titulo"], "Quais os 5 produtos mais vendidos?")
        self.assertEqual(len(carregada["mensagens"]), 2)
        msg_ia = carregada["mensagens"][1]
        self.assertEqual(msg_ia["intencao"], "gerar_grafico")
        self.assertEqual(msg_ia["grafico"]["data"][0]["type"], "bar")
        self.assertEqual(msg_ia["dados_tabela"][0]["nome"], "Produto A")

    def test_excluir_conversa_remove_em_cascata(self):
        cid = criar_conversa(db_path=self.db_path)["id"]
        salvar_mensagem(cid, "user", "Teste exclusão", db_path=self.db_path)
        self.assertTrue(excluir_conversa(cid, db_path=self.db_path))
        self.assertIsNone(obter_conversa(cid, db_path=self.db_path))
        self.assertFalse(excluir_conversa(cid, db_path=self.db_path))

    def test_obter_conversa_inexistente_retorna_none(self):
        self.assertIsNone(obter_conversa(999999, db_path=self.db_path))


if __name__ == "__main__":
    unittest.main()
