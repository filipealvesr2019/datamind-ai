"""API REST FastAPI — DataMind AI
Fornece endpoints para o Dashboard de BI, Chat com o Agente de IA e Auditoria em Tempo Real.
"""

from pathlib import Path
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))

from db.database import get_read_only_connection
from agent.engine import DataMindAgent

app = FastAPI(
    title="DataMind AI — Analista Empresarial Inteligente",
    description="API de BI e Agente de IA para análise de dados empresariais.",
    version="1.0.0"
)

# Habilita CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Instância compartilhada do agente
agent = DataMindAgent()

# Diretórios
FRONTEND_DIR = Path(__file__).resolve().parent.parent.parent / "frontend"


class PerguntaRequest(BaseModel):
    pergunta: str


# ==========================================
# ENDPOINTS DO DASHBOARD DE BI
# ==========================================

@app.get("/api/kpis")
def obter_kpis():
    """Retorna os indicadores executivos para os KPI Cards do Dashboard."""
    with get_read_only_connection() as conn:
        cursor = conn.cursor()

        # Faturamento e Vendas Concluídas
        cursor.execute("""
            SELECT 
                COUNT(DISTINCT v.id) as total_vendas,
                COALESCE(SUM(iv.quantidade * iv.preco_unitario), 0) as faturamento_total,
                COALESCE(ROUND(SUM(iv.quantidade * iv.preco_unitario) / COUNT(DISTINCT v.id), 2), 0) as ticket_medio
            FROM vendas v
            JOIN itens_venda iv ON v.id = iv.venda_id
            WHERE v.status = 'concluida'
        """)
        faturamento_kpis = dict(cursor.fetchone())

        # Inadimplência Real
        cursor.execute("""
            SELECT 
                COALESCE(SUM(cr.valor), 0) as total_inadimplencia,
                COUNT(DISTINCT cr.cliente_id) as clientes_inadimplentes
            FROM contas_receber cr
            WHERE cr.status_pagamento = 'pendente' AND cr.vencimento < DATE('now')
        """)
        inadimplencia_kpis = dict(cursor.fetchone())

        # Total de Clientes Cadastrados
        cursor.execute("SELECT COUNT(*) as total_clientes FROM clientes")
        total_clientes = cursor.fetchone()["total_clientes"]

        return {
            "faturamento_total": faturamento_kpis["faturamento_total"],
            "vendas_concluidas": faturamento_kpis["total_vendas"],
            "ticket_medio": faturamento_kpis["ticket_medio"],
            "inadimplencia_total": inadimplencia_kpis["total_inadimplencia"],
            "clientes_inadimplentes": inadimplencia_kpis["clientes_inadimplentes"],
            "total_clientes": total_clientes
        }


@app.get("/api/dashboard/vendas-mensais")
def obter_vendas_mensais():
    """Retorna a evolução do faturamento mês a mês para gráfico de linha."""
    with get_read_only_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                strftime('%Y-%m', v.data_venda) as mes,
                COUNT(DISTINCT v.id) as total_pedidos,
                ROUND(SUM(iv.quantidade * iv.preco_unitario), 2) as faturamento
            FROM vendas v
            JOIN itens_venda iv ON v.id = iv.venda_id
            WHERE v.status = 'concluida'
            GROUP BY strftime('%Y-%m', v.data_venda)
            ORDER BY mes ASC
        """)
        return [dict(r) for r in cursor.fetchall()]


@app.get("/api/dashboard/top-produtos")
def obter_top_produtos():
    """Retorna os 5 produtos mais vendidos em quantidade."""
    with get_read_only_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                p.nome,
                p.categoria,
                SUM(iv.quantidade) as qtd_vendida,
                ROUND(SUM(iv.quantidade * iv.preco_unitario), 2) as faturamento
            FROM itens_venda iv
            JOIN produtos p ON p.id = iv.produto_id
            JOIN vendas v ON v.id = iv.venda_id
            WHERE v.status = 'concluida'
            GROUP BY p.id
            ORDER BY qtd_vendida DESC
            LIMIT 5
        """)
        return [dict(r) for r in cursor.fetchall()]


# ==========================================
# ENDPOINT DO ANALISTA IA
# ==========================================

@app.post("/api/chat")
def conversar_com_dados(req: PerguntaRequest):
    """Processa pergunta em linguagem natural, gera SQL validado e retorna resposta com gráfico."""
    if not req.pergunta.strip():
        raise HTTPException(status_code=400, detail="A pergunta não pode ser vazia.")

    resultado = agent.responder(req.pergunta)
    return resultado


# ==========================================
# ENDPOINT DE AUDITORIA E LOGS
# ==========================================

@app.get("/api/audit")
def listar_auditoria(limite: int = 50):
    """Retorna os registros de auditoria em tempo real."""
    with get_read_only_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, data_hora, pergunta_usuario, sql_proposto, status, motivo_bloqueio, tempo_execucao_ms, linhas_retornadas
            FROM auditoria_consultas
            ORDER BY id DESC
            LIMIT ?
        """, (limite,))
        return [dict(r) for r in cursor.fetchall()]


# Servir frontend estático
if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
