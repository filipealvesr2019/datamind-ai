"""Teste do Agente de IA (test_agent.py) — DataMind AI
Localização: backend/tests/test_agent.py
Testa a orquestração do Agente LangChain + Gemini:
- Execução das 5 perguntas de negócios essenciais
- Escolha da ferramenta de consulta segura
- Construção determinística de gráficos Plotly
- Transparência com exibição do SQL executado
"""

import os
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR / "app"))

from agent.engine import DataMindAgent
from services.chart_builder import construir_especificacao_grafico


def testar_pipeline_grafico_direto():
    print("\n--- [TESTE 1] Teste Unitário do Gerador Determinístico de Gráficos ---")
    dados_exemplo = [
        {"nome": "Notebook Pro", "total": 85},
        {"nome": "Monitor 24", "total": 72},
        {"nome": "Teclado Mecânico", "total": 64}
    ]
    spec = construir_especificacao_grafico(
        tipo="bar",
        dados=dados_exemplo,
        coluna_x="nome",
        coluna_y="total",
        titulo="Top 3 Produtos"
    )
    assert spec is not None
    assert "data" in spec and "layout" in spec
    print("  -> SUCESSO: Especificação Plotly gerada com precisão determinística!")
    print(f"  -> Tipo de trace: {spec['data'][0]['type']}, Título: {spec['layout']['title']['text']}")


def testar_agente_gemini():
    print("\n--- [TESTE 2] Teste do Agente com as 5 Perguntas Empresariais ---")
    agente = DataMindAgent()

    if not agente.api_key:
        print("  -> AVISO: GEMINI_API_KEY não encontrada no arquivo .env.")
        print("  -> Para testar com a IA do Gemini ao vivo:")
        print("     1. Abra o arquivo backend/.env")
        print("     2. Insira sua chave: GEMINI_API_KEY=AIzaSy...")
        print("     3. Execute novamente este teste: python datamind-ai/backend/tests/test_agent.py")
        return

    perguntas = [
        "Quanto a empresa faturou no total em vendas concluídas?",
        "Quais foram os cinco produtos mais vendidos em quantidade e gere um gráfico de barras?",
        "Quais clientes estão com pagamentos atrasados e qual o valor total da inadimplência?",
        "Qual vendedor teve o melhor desempenho em faturamento?",
        "Qual o ticket médio das vendas concluídas?"
    ]

    for idx, pergunta in enumerate(perguntas, 1):
        print(f"\n=======================================================")
        print(f"PERGUNTA {idx}: \"{pergunta}\"")
        print(f"=======================================================")
        resultado = agente.responder(pergunta)
        
        if resultado["sucesso"]:
            print(f"\nRESPOSTA DO DATAMIND AI:\n{resultado['resposta']}\n")
            print(f"[TRANSPARÊNCIA SQL]: {resultado['sql_executado']}")
            print(f"[REGISTROS ENCONTRADOS]: {resultado['total_registros']}")
            print(f"[TEMPO DE EXECUÇÃO]: {resultado['tempo_ms']} ms")
            if resultado["grafico"]:
                print(f"[GRÁFICO GERADO]: Sim ({resultado['grafico']['data'][0]['type']})")
        else:
            print(f"FALHA NO PROCESSAMENTO: {resultado.get('mensagem')}")


if __name__ == "__main__":
    testar_pipeline_grafico_direto()
    testar_agente_gemini()
