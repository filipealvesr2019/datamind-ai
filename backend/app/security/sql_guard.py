"""Camada Intermediária de Segurança e Validador AST SQL — DataMind AI
Utiliza a biblioteca sqlglot para analisar a Árvore Sintática Abstrata (AST):
- Garante instrução única do tipo SELECT
- Rejeita qualquer mutação (DML/DDL) e injeção SQL
- Valida catálogo de tabelas autorizadas (whitelisting)
- Força cláusula LIMIT 100 quando ausente
- Executa na conexão somente leitura e registra auditoria completa
"""

import time
import sqlite3
from typing import Dict, Any, List, Optional, Set
import sqlglot
from sqlglot import exp

try:
    from ..db.database import get_read_only_connection, log_audit
except (ImportError, ValueError):
    from db.database import get_read_only_connection, log_audit

# Catálogo explícito de tabelas autorizadas para consulta analítica
TABELAS_AUTORIZADAS: Set[str] = {
    "clientes",
    "produtos",
    "vendedores",
    "vendas",
    "itens_venda",
    "contas_receber"
}

LIMITE_MAXIMO_LINHAS = 500
LIMITE_PADRAO_LINHAS = 100


class SQLValidationError(Exception):
    """Exceção levantada quando uma consulta falha na validação de segurança."""
    pass


def validar_e_sanitizar_sql(sql_query: str) -> str:
    """Analisa e valida sintaticamente a consulta SQL via AST.
    
    Retorna o SQL sanitizado com LIMIT forçado.
    Dispara SQLValidationError caso a consulta viole as regras de segurança.
    """
    if not sql_query or not sql_query.strip():
        raise SQLValidationError("A consulta SQL não pode ser vazia.")

    # 1. Parse da query usando o dialeto SQLite
    try:
        statements = sqlglot.parse(sql_query, read="sqlite")
    except Exception as e:
        raise SQLValidationError(f"Erro de sintaxe SQL: {str(e)}")

    # 2. Bloqueia múltiplas instruções separadas por ponto e vírgula
    if len(statements) == 0:
        raise SQLValidationError("Nenhuma instrução SQL identificada.")
    if len(statements) > 1:
        raise SQLValidationError("Múltiplas instruções SQL são terminantemente proibidas.")

    parsed = statements[0]

    # 3. Garante que a raiz da AST seja rigorosamente uma instrução SELECT
    if not isinstance(parsed, exp.Select):
        tipo_instrucao = parsed.key.upper() if hasattr(parsed, "key") else "DESCONHECIDO"
        raise SQLValidationError(
            f"Operação não autorizada ({tipo_instrucao}). Apenas consultas analíticas (SELECT) são permitidas."
        )

    # 4. Busca qualquer sub-nó perigoso (Insert, Update, Delete, Drop, Alter, Command, Pragma)
    nos_proibidos = (
        exp.Insert, exp.Update, exp.Delete, exp.Drop, exp.Alter,
        exp.Create, exp.Command, exp.Pragma
    )
    for no in parsed.find_all(nos_proibidos):
        raise SQLValidationError(f"Cláusula não autorizada detectada na árvore sintática: {no.key.upper()}")

    # 5. Whitelisting de Tabelas
    tabelas_referenciadas = set()
    for table_node in parsed.find_all(exp.Table):
        tabela_nome = table_node.name.lower()
        tabelas_referenciadas.add(tabela_nome)
        if tabela_nome not in TABELAS_AUTORIZADAS:
            raise SQLValidationError(
                f"Acesso negado à tabela '{tabela_nome}'. Tabelas autorizadas: {', '.join(sorted(TABELAS_AUTORIZADAS))}."
            )

    if not tabelas_referenciadas:
        raise SQLValidationError("A consulta deve referenciar ao menos uma tabela do catálogo de dados.")

    # 6. Enforcement da cláusula LIMIT
    limit_node = parsed.args.get("limit")
    if limit_node is None:
        # Não possui LIMIT -> anexa LIMIT 100
        parsed = parsed.limit(LIMITE_PADRAO_LINHAS)
    else:
        # Possui LIMIT -> verifica se excede o teto de segurança
        try:
            valor_limit = int(limit_node.expression.this)
            if valor_limit > LIMITE_MAXIMO_LINHAS:
                parsed = parsed.limit(LIMITE_MAXIMO_LINHAS)
        except (AttributeError, ValueError):
            parsed = parsed.limit(LIMITE_PADRAO_LINHAS)

    return parsed.sql(dialect="sqlite")


def executar_consulta_segura(
    sql_proposto: str,
    pergunta_usuario: Optional[str] = None
) -> Dict[str, Any]:
    """Fluxo completo da Camada Intermediária:
    1. Valida SQL na AST (sqlglot)
    2. Se inválido: grava auditoria como BLOQUEADO e retorna erro
    3. Se válido: executa na conexão Read-Only e grava auditoria como APROVADO
    """
    inicio_ms = time.perf_counter()

    # 1. Validação Sintática
    try:
        sql_sanitizado = validar_e_sanitizar_sql(sql_proposto)
    except SQLValidationError as e:
        duracao_ms = round((time.perf_counter() - inicio_ms) * 1000, 2)
        motivo = str(e)
        log_audit(
            pergunta_usuario=pergunta_usuario,
            sql_proposto=sql_proposto,
            status="BLOQUEADO",
            motivo_bloqueio=motivo,
            tempo_execucao_ms=duracao_ms,
            linhas_retornadas=0
        )
        return {
            "success": False,
            "error_type": "SEGURANCA_BLOQUEIO",
            "message": motivo,
            "sql_proposto": sql_proposto,
            "tempo_ms": duracao_ms
        }

    # 2. Execução Somente Leitura
    conn = None
    try:
        conn = get_read_only_connection()
        cursor = conn.cursor()
        cursor.execute(sql_sanitizado)
        rows = cursor.fetchall()

        # Extrai nomes das colunas
        colunas = [desc[0] for desc in cursor.description] if cursor.description else []
        dados = [dict(row) for row in rows]
        duracao_ms = round((time.perf_counter() - inicio_ms) * 1000, 2)

        # Grava auditoria de aprovação
        log_audit(
            pergunta_usuario=pergunta_usuario,
            sql_proposto=sql_sanitizado,
            status="APROVADO",
            tempo_execucao_ms=duracao_ms,
            linhas_retornadas=len(dados)
        )

        return {
            "success": True,
            "sql_executed": sql_sanitizado,
            "columns": colunas,
            "data": dados,
            "row_count": len(dados),
            "tempo_ms": duracao_ms
        }

    except sqlite3.OperationalError as e:
        duracao_ms = round((time.perf_counter() - inicio_ms) * 1000, 2)
        erro_msg = f"Erro operacional no SQLite: {str(e)}"
        log_audit(
            pergunta_usuario=pergunta_usuario,
            sql_proposto=sql_sanitizado,
            status="ERRO_EXECUCAO",
            motivo_bloqueio=erro_msg,
            tempo_execucao_ms=duracao_ms,
            linhas_retornadas=0
        )
        return {
            "success": False,
            "error_type": "ERRO_SQL",
            "message": erro_msg,
            "sql_executed": sql_sanitizado,
            "tempo_ms": duracao_ms
        }
    finally:
        if conn:
            conn.close()
