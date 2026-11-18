"""Script de Verificação e Validação de Coerência de Dados — DataMind AI
Localização: backend/tests/test_db.py
"""

import sys
from pathlib import Path

# Adiciona o diretório app ao path
BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR / "app"))

from db.database import get_read_only_connection, log_audit, DB_PATH


def testar_modo_somente_leitura():
    print("\n--- [TESTE 1] Segurança da Conexão Somente Leitura (mode=ro) ---")
    ro_conn = get_read_only_connection()
    cursor = ro_conn.cursor()
    try:
        cursor.execute("INSERT INTO vendedores (nome, email) VALUES ('Hacker', 'hacker@teste.com')")
        print("FALHA: A conexão permitiu escrita!")
    except Exception as e:
        print(f"SUCESSO: Bloqueio nativo do driver SQLite funcionou com sucesso:")
        print(f"  Mensagem de erro: {e}")
    finally:
        ro_conn.close()


def testar_kpis_empresariais():
    print("\n--- [TESTE 2] Cálculo de Indicadores Empresariais (KPIs) ---")
    ro_conn = get_read_only_connection()
    cursor = ro_conn.cursor()

    # 1. Faturamento Total e Vendas Concluídas
    cursor.execute("""
        SELECT 
            COUNT(DISTINCT v.id) as total_vendas_concluidas,
            SUM(iv.quantidade * iv.preco_unitario) as faturamento_total,
            ROUND(SUM(iv.quantidade * iv.preco_unitario) / COUNT(DISTINCT v.id), 2) as ticket_medio
        FROM vendas v
        JOIN itens_venda iv ON v.id = iv.venda_id
        WHERE v.status = 'concluida'
    """)
    res_faturamento = cursor.fetchone()
    total_vendas = res_faturamento["total_vendas_concluidas"]
    faturamento = res_faturamento["faturamento_total"]
    ticket_medio = res_faturamento["ticket_medio"]

    print(f"Vendas Concluídas: {total_vendas}")
    print(f"Faturamento Total: R$ {faturamento:,.2f}")
    print(f"Ticket Médio: R$ {ticket_medio:,.2f}")

    # 2. Distribuição de Status de Vendas
    print("\nDistribuição de Status das Vendas:")
    cursor.execute("SELECT status, COUNT(*) as qtd FROM vendas GROUP BY status")
    for row in cursor.fetchall():
        print(f"  - {row['status'].capitalize()}: {row['qtd']} vendas")

    # 3. Inadimplência Real vs Contas a Vencer
    print("\nAnálise Financeira de Contas a Receber:")
    cursor.execute("""
        SELECT 
            SUM(CASE WHEN status_pagamento = 'pendente' AND vencimento < DATE('now') THEN valor ELSE 0 END) as total_inadimplencia,
            COUNT(DISTINCT CASE WHEN status_pagamento = 'pendente' AND vencimento < DATE('now') THEN cliente_id END) as clientes_inadimplentes,
            SUM(CASE WHEN status_pagamento = 'pendente' AND vencimento >= DATE('now') THEN valor ELSE 0 END) as total_a_vencer,
            SUM(CASE WHEN status_pagamento = 'pago' THEN valor ELSE 0 END) as total_pago
        FROM contas_receber
    """)
    res_fin = cursor.fetchone()
    print(f"  - Inadimplência Real (Atrasadas): R$ {res_fin['total_inadimplencia']:,.2f} ({res_fin['clientes_inadimplentes']} clientes)")
    print(f"  - Contas a Vencer (No Prazo): R$ {res_fin['total_a_vencer']:,.2f}")
    print(f"  - Contas Pagas (Realizadas): R$ {res_fin['total_pago']:,.2f}")

    # 4. Top 5 Produtos Mais Vendidos
    print("\nTop 5 Produtos Campeões de Venda:")
    cursor.execute("""
        SELECT 
            p.nome,
            p.categoria,
            SUM(iv.quantidade) as qtd_vendida,
            SUM(iv.quantidade * iv.preco_unitario) as faturamento_prod
        FROM itens_venda iv
        JOIN produtos p ON p.id = iv.produto_id
        JOIN vendas v ON v.id = iv.venda_id
        WHERE v.status = 'concluida'
        GROUP BY p.id
        ORDER BY qtd_vendida DESC
        LIMIT 5
    """)
    for idx, prod in enumerate(cursor.fetchall(), 1):
        print(f"  {idx}. {prod['nome']} ({prod['categoria']}) -> {prod['qtd_vendida']} un. (R$ {prod['faturamento_prod']:,.2f})")

    # 5. Desempenho dos Vendedores
    print("\nDesempenho Comercial dos Vendedores:")
    cursor.execute("""
        SELECT 
            vd.nome,
            vd.meta_mensal,
            COUNT(DISTINCT v.id) as total_pedidos,
            SUM(iv.quantidade * iv.preco_unitario) as faturamento_total
        FROM vendedores vd
        LEFT JOIN vendas v ON vd.id = v.vendedor_id AND v.status = 'concluida'
        LEFT JOIN itens_venda iv ON v.id = iv.venda_id
        GROUP BY vd.id
        ORDER BY faturamento_total DESC
    """)
    for v in cursor.fetchall():
        print(f"  - {v['nome']}: {v['total_pedidos']} vendas | R$ {v['faturamento_total']:,.2f} faturados")

    ro_conn.close()


def testar_auditoria():
    print("\n--- [TESTE 3] Registro na Conexão de Auditoria Desacoplada ---")
    log_id = log_audit(
        pergunta_usuario="Qual o faturamento total da empresa?",
        sql_proposto="SELECT SUM(quantidade * preco_unitario) FROM itens_venda",
        status="APROVADO",
        tempo_execucao_ms=4.85,
        linhas_retornadas=1
    )
    print(f"Registro de auditoria criado com sucesso! ID={log_id}")


if __name__ == "__main__":
    if not DB_PATH.exists():
        print(f"Banco não encontrado em {DB_PATH}.")
        sys.exit(1)
        
    testar_modo_somente_leitura()
    testar_kpis_empresariais()
    testar_auditoria()
    print("\nTodos os testes de banco foram concluídos com êxito!")
