"""Testes automatizados da camada de segurança SQL (AST Parser / sqlglot)."""

import sys
import unittest
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent.parent.parent / "backend" / "app"
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from security.sql_guard import validar_e_sanitizar_sql, SQLValidationError


class TestSQLGuard(unittest.TestCase):
    def test_select_valido_injeta_limit_padrao(self):
        sql = validar_e_sanitizar_sql("SELECT nome, preco FROM produtos ORDER BY preco DESC")
        self.assertIn("LIMIT 100", sql.upper())

    def test_limit_excessivo_e_limitado_ao_teto(self):
        sql = validar_e_sanitizar_sql("SELECT nome FROM clientes LIMIT 9999")
        self.assertIn("LIMIT 500", sql.upper())

    def test_bloqueia_drop_table(self):
        with self.assertRaises(SQLValidationError):
            validar_e_sanitizar_sql("DROP TABLE clientes")

    def test_bloqueia_delete(self):
        with self.assertRaises(SQLValidationError):
            validar_e_sanitizar_sql("DELETE FROM vendas WHERE id = 1")

    def test_bloqueia_multiplas_instrucoes(self):
        with self.assertRaises(SQLValidationError):
            validar_e_sanitizar_sql("SELECT * FROM clientes; DROP TABLE clientes;")

    def test_bloqueia_tabela_nao_autorizada(self):
        with self.assertRaises(SQLValidationError):
            validar_e_sanitizar_sql("SELECT * FROM sqlite_master")


if __name__ == "__main__":
    unittest.main()
