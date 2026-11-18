"""Módulo de Conexão com o Banco de Dados — DataMind AI
Gerencia conexões isoladas:
1. Conexão Analítica (Somente Leitura - mode=ro via URI)
2. Conexão de Auditoria / Administrativa (Escrita controlada)
"""

import os
import sqlite3
from pathlib import Path
from typing import Optional, Dict, Any, List

# Caminhos padrão do projeto
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DATA_DIR / "empresa.db"
SCHEMA_PATH = Path(__file__).resolve().parent / "schema.sql"


def init_db(db_path: Optional[Path] = None) -> None:
    """Inicializa as tabelas e índices executando o schema.sql."""
    target_path = db_path or DB_PATH
    with sqlite3.connect(str(target_path)) as conn:
        conn.execute("PRAGMA foreign_keys = ON;")
        with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
            conn.executescript(f.read())
        conn.commit()


def get_write_connection(db_path: Optional[Path] = None) -> sqlite3.Connection:
    """Retorna uma conexão de escrita administrativa (usada para seed e auditoria)."""
    target_path = db_path or DB_PATH
    conn = sqlite3.connect(str(target_path))
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.row_factory = sqlite3.Row
    return conn


def get_read_only_connection(db_path: Optional[Path] = None) -> sqlite3.Connection:
    """Retorna uma conexão estritamente SOMENTE LEITURA usando URI SQLite (mode=ro).

    Qualquer tentativa de modificação disparará sqlite3.OperationalError: attempt to write a readonly database.
    """
    target_path = (db_path or DB_PATH).resolve()
    # Em Windows, o path para URI precisa de barras normais
    uri_path = target_path.as_posix()
    uri = f"file:{uri_path}?mode=ro"
    conn = sqlite3.connect(uri, uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def log_audit(
    pergunta_usuario: Optional[str],
    sql_proposto: str,
    status: str,
    motivo_bloqueio: Optional[str] = None,
    tempo_execucao_ms: float = 0.0,
    linhas_retornadas: int = 0,
    db_path: Optional[Path] = None
) -> int:
    """Grava o registro de auditoria através da conexão de escrita isolada."""
    with get_write_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO auditoria_consultas 
            (pergunta_usuario, sql_proposto, status, motivo_bloqueio, tempo_execucao_ms, linhas_retornadas)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                pergunta_usuario,
                sql_proposto,
                status,
                motivo_bloqueio,
                tempo_execucao_ms,
                linhas_retornadas
            )
        )
        conn.commit()
        return cursor.lastrowid
