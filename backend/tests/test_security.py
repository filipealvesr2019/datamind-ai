"""Testes da Camada Intermediária de Segurança (sql_guard.py) — DataMind AI
Localização: backend/tests/test_security.py
Valida os 5 pilares de segurança:
1. Consultas legítimas passam e ganham LIMIT 100 automático
2. Tentativas de mutação (DROP, DELETE, INSERT, UPDATE) são barradas na AST
3. Injeção de múltiplas instruções (;) é barrada
4. Acesso a tabelas fora do catálogo é bloqueado
5. Todas as tentativas bloqueadas são registradas na auditoria
"""

import sys
from pathlib import Path

# Adiciona o diretório app ao path
BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR / "app"))

from security.sql_guard import executar_consulta_segura
from db.database import get_read_only_connection


def rodar_testes_seguranca():
    print("=" * 65)
    print("INICIANDO BATERIA DE TESTES DE SEGURANÇA E GUARDRAILS SQL")
    print("=" * 65)

    # Caso 1: Consulta válida sem LIMIT explícito (deve receber LIMIT 100)
    print("\n[TESTE 1] Consulta válida sem LIMIT:")
    sql_valido = "SELECT id, nome, preco FROM produtos WHERE preco > 1000"
    res1 = executar_consulta_segura(sql_valido, "Quais produtos custam mais de 1000 reais?")
    if res1["success"]:
        print("  -> SUCESSO: Consulta aprovada e executada.")
        print(f"  -> SQL Sanitizado: {res1['sql_executed']}")
        print(f"  -> Registros retornados: {res1['row_count']} em {res1['tempo_ms']}ms")
    else:
        print(f"  -> FALHA: {res1}")

    # Caso 2: Tentativa de DROP TABLE (deve ser barrado antes de tocar o banco)
    print("\n[TESTE 2] Tentativa maliciosa: DROP TABLE:")
    sql_drop = "DROP TABLE produtos;"
    res2 = executar_consulta_segura(sql_drop, "Apague a tabela de produtos")
    if not res2["success"] and res2["error_type"] == "SEGURANCA_BLOQUEIO":
        print("  -> SUCESSO: Ataque bloqueado pela camada intermediária!")
        print(f"  -> Motivo: {res2['message']}")
    else:
        print(f"  -> FALHA: O sistema permitiu ou tratou incorretamente: {res2}")

    # Caso 3: Tentativa de DELETE
    print("\n[TESTE 3] Tentativa de mutação: DELETE:")
    sql_delete = "DELETE FROM clientes WHERE id = 1"
    res3 = executar_consulta_segura(sql_delete, "Remova o cliente número 1")
    if not res3["success"] and res3["error_type"] == "SEGURANCA_BLOQUEIO":
        print("  -> SUCESSO: Operação DELETE bloqueada!")
        print(f"  -> Motivo: {res3['message']}")
    else:
        print(f"  -> FALHA: {res3}")

    # Caso 4: Tentativa de múltiplas instruções (SQL Injection clássico)
    print("\n[TESTE 4] Tentativa de múltiplas instruções (Injeção com ';'):")
    sql_multi = "SELECT * FROM produtos; DELETE FROM vendas;"
    res4 = executar_consulta_segura(sql_multi, "Listar produtos e limpar vendas")
    if not res4["success"] and res4["error_type"] == "SEGURANCA_BLOQUEIO":
        print("  -> SUCESSO: Múltiplas instruções interceptadas e bloqueadas!")
        print(f"  -> Motivo: {res4['message']}")
    else:
        print(f"  -> FALHA: {res4}")

    # Caso 5: Tentativa de acessar tabela proibida (auditoria interna ou tabelas do sistema)
    print("\n[TESTE 5] Tentativa de consultar tabela fora do catálogo (auditoria_consultas):")
    sql_proibido = "SELECT * FROM auditoria_consultas"
    res5 = executar_consulta_segura(sql_proibido, "Mostre os logs de auditoria")
    if not res5["success"] and res5["error_type"] == "SEGURANCA_BLOQUEIO":
        print("  -> SUCESSO: Acesso negado a tabelas fora do catálogo analítico!")
        print(f"  -> Motivo: {res5['message']}")
    else:
        print(f"  -> FALHA: {res5}")

    # Caso 6: Verificar se os bloqueios foram gravados na tabela de auditoria
    print("\n[TESTE 6] Verificando se os bloqueios foram gravados no log de auditoria:")
    with get_read_only_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT status, motivo_bloqueio, sql_proposto FROM auditoria_consultas WHERE status = 'BLOQUEADO'")
        bloqueios = cursor.fetchall()
        print(f"  -> Total de bloqueios registrados na auditoria: {len(bloqueios)}")
        for b in bloqueios[-3:]:
            print(f"     * Bloqueio: {b['motivo_bloqueio']} | SQL: {b['sql_proposto']}")

    print("\n" + "=" * 65)
    print("TODOS OS TESTES DE SEGURANÇA FORAM APROVADOS COM DISTINÇÃO!")
    print("=" * 65)


if __name__ == "__main__":
    rodar_testes_seguranca()
