"""Persistência de Conversas e Histórico do Chat — DataMind AI
Armazena conversas e mensagens (incluindo gráficos Plotly e dados tabulares)
em tabelas dedicadas no SQLite através da conexão de escrita isolada.
"""

from contextlib import closing
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from ..db.database import get_write_connection
except (ImportError, ValueError):
    from db.database import get_write_connection


def init_chat_tables(db_path: Optional[Path] = None) -> None:
    """Garante que as tabelas de conversas e mensagens existam no banco."""
    with closing(get_write_connection(db_path)) as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS conversas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                titulo TEXT NOT NULL DEFAULT 'Nova conversa',
                criada_em DATETIME DEFAULT CURRENT_TIMESTAMP,
                atualizada_em DATETIME DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS mensagens_chat (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversa_id INTEGER NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('user', 'assistant')),
                conteudo TEXT NOT NULL,
                intencao TEXT,
                grafico_json TEXT,
                dados_tabela_json TEXT,
                criada_em DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (conversa_id) REFERENCES conversas(id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_mensagens_conversa
                ON mensagens_chat(conversa_id, id);
        """)
        conn.commit()


def criar_conversa(titulo: str = "Nova conversa", db_path: Optional[Path] = None) -> Dict[str, Any]:
    """Cria uma nova conversa e retorna seus metadados."""
    init_chat_tables(db_path)
    titulo_limpo = (titulo or "Nova conversa").strip()[:80] or "Nova conversa"
    with closing(get_write_connection(db_path)) as conn:
        cur = conn.cursor()
        cur.execute("INSERT INTO conversas (titulo) VALUES (?)", (titulo_limpo,))
        conversa_id = cur.lastrowid
        conn.commit()
        cur.execute(
            "SELECT id, titulo, criada_em, atualizada_em FROM conversas WHERE id = ?",
            (conversa_id,),
        )
        row = dict(cur.fetchone())
        row["total_mensagens"] = 0
        return row


def listar_conversas(limite: int = 50, db_path: Optional[Path] = None) -> List[Dict[str, Any]]:
    """Lista conversas ordenadas da mais recente para a mais antiga."""
    init_chat_tables(db_path)
    with closing(get_write_connection(db_path)) as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT
                c.id,
                c.titulo,
                c.criada_em,
                c.atualizada_em,
                COUNT(m.id) AS total_mensagens
            FROM conversas c
            LEFT JOIN mensagens_chat m ON m.conversa_id = c.id
            GROUP BY c.id
            ORDER BY c.atualizada_em DESC, c.id DESC
            LIMIT ?
            """,
            (limite,),
        )
        return [dict(r) for r in cur.fetchall()]


def obter_conversa(conversa_id: int, db_path: Optional[Path] = None) -> Optional[Dict[str, Any]]:
    """Retorna os metadados da conversa e todas as suas mensagens com gráficos/tabelas."""
    init_chat_tables(db_path)
    with closing(get_write_connection(db_path)) as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT id, titulo, criada_em, atualizada_em FROM conversas WHERE id = ?",
            (conversa_id,),
        )
        conversa_row = cur.fetchone()
        if not conversa_row:
            return None

        conversa = dict(conversa_row)
        cur.execute(
            """
            SELECT id, role, conteudo, intencao, grafico_json, dados_tabela_json, criada_em
            FROM mensagens_chat
            WHERE conversa_id = ?
            ORDER BY id ASC
            """,
            (conversa_id,),
        )

        mensagens = []
        for row in cur.fetchall():
            item = dict(row)
            grafico_raw = item.pop("grafico_json", None)
            dados_raw = item.pop("dados_tabela_json", None)
            item["grafico"] = json.loads(grafico_raw) if grafico_raw else None
            item["dados_tabela"] = json.loads(dados_raw) if dados_raw else []
            mensagens.append(item)

        conversa["mensagens"] = mensagens
        return conversa


def salvar_mensagem(
    conversa_id: int,
    role: str,
    conteudo: str,
    intencao: Optional[str] = None,
    grafico: Optional[Dict[str, Any]] = None,
    dados_tabela: Optional[List[Dict[str, Any]]] = None,
    db_path: Optional[Path] = None,
) -> int:
    """Salva uma mensagem na conversa, atualiza timestamp e define título automático na 1ª pergunta."""
    init_chat_tables(db_path)
    grafico_json = json.dumps(grafico, ensure_ascii=False) if grafico else None
    dados_json = json.dumps(dados_tabela, ensure_ascii=False) if dados_tabela else None

    with closing(get_write_connection(db_path)) as conn:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO mensagens_chat
            (conversa_id, role, conteudo, intencao, grafico_json, dados_tabela_json)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (conversa_id, role, conteudo, intencao, grafico_json, dados_json),
        )
        msg_id = cur.lastrowid

        # Atualiza título automático se ainda estiver padrão na primeira pergunta do usuário
        if role == "user":
            cur.execute("SELECT titulo FROM conversas WHERE id = ?", (conversa_id,))
            row = cur.fetchone()
            if row and row["titulo"] == "Nova conversa":
                novo_titulo = conteudo.strip().replace("\n", " ")[:55]
                if len(conteudo.strip()) > 55:
                    novo_titulo += "..."
                cur.execute(
                    "UPDATE conversas SET titulo = ?, atualizada_em = CURRENT_TIMESTAMP WHERE id = ?",
                    (novo_titulo, conversa_id),
                )
            else:
                cur.execute(
                    "UPDATE conversas SET atualizada_em = CURRENT_TIMESTAMP WHERE id = ?",
                    (conversa_id,),
                )
        else:
            cur.execute(
                "UPDATE conversas SET atualizada_em = CURRENT_TIMESTAMP WHERE id = ?",
                (conversa_id,),
            )

        conn.commit()
        return msg_id


def excluir_conversa(conversa_id: int, db_path: Optional[Path] = None) -> bool:
    """Remove uma conversa e todas as suas mensagens (via ON DELETE CASCADE)."""
    init_chat_tables(db_path)
    with closing(get_write_connection(db_path)) as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM conversas WHERE id = ?", (conversa_id,))
        conn.commit()
        return cur.rowcount > 0
