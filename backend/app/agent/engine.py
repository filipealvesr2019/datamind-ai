"""Motor do Agente de IA (DataMind AI) — LangChain + Gemini
Orquestra o ciclo de raciocínio, ferramentas de consulta segura e geração determinística de gráficos.
"""

import os
import json
import time
from pathlib import Path
from typing import Dict, Any, Optional, List

from dotenv import load_dotenv

# Carrega variáveis de ambiente do .env
ENV_PATH = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(dotenv_path=ENV_PATH)

from langchain_core.tools import tool
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage
from langchain_google_genai import ChatGoogleGenerativeAI

try:
    from .prompt import SYSTEM_PROMPT
    from .intent_router import classificar_intencao
    from ..security.sql_guard import executar_consulta_segura
    from ..services.chart_builder import construir_especificacao_grafico
except (ImportError, ValueError):
    from agent.prompt import SYSTEM_PROMPT
    from agent.intent_router import classificar_intencao
    from security.sql_guard import executar_consulta_segura
    from services.chart_builder import construir_especificacao_grafico


def _extrair_texto(conteudo: Any) -> str:
    """Extrai texto limpo de strings ou listas de blocos retornadas pelo modelo."""
    if isinstance(conteudo, str):
        return conteudo
    if isinstance(conteudo, list):
        partes = []
        for item in conteudo:
            if isinstance(item, dict) and "text" in item:
                partes.append(item["text"])
            elif isinstance(item, str):
                partes.append(item)
        return "\n".join(partes)
    return str(conteudo)


class DataMindAgent:
    def __init__(self, model_name: Optional[str] = None):
        self.api_key = os.getenv("GEMINI_API_KEY", "").strip()
        self.model_name = model_name or os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite")
        
        self.ultimo_sql: Optional[str] = None
        self.ultimos_dados: List[Dict[str, Any]] = []
        self.ultimo_grafico: Optional[Dict[str, Any]] = None

    def _criar_ferramentas(self, pergunta_usuario: str):
        """Cria as ferramentas amarradas ao contexto da pergunta atual."""
        self.ultimo_sql = None
        self.ultimos_dados = []
        self.ultimo_grafico = None

        @tool
        def consultar_banco(sql: str) -> str:
            """Executa uma consulta analítica (somente SELECT) no banco de dados SQLite.
            O SQL é validado na AST via sqlglot, impedindo mutações e aplicando LIMIT automático.
            Exemplo: SELECT nome, preco FROM produtos ORDER BY preco DESC LIMIT 5
            """
            resultado = executar_consulta_segura(sql, pergunta_usuario=pergunta_usuario)
            if not resultado["success"]:
                return f"ERRO_SEGURANCA: {resultado.get('message', 'Falha ao executar SQL')}"

            self.ultimo_sql = resultado.get("sql_executed", sql)
            self.ultimos_dados = resultado.get("data", [])

            return json.dumps(resultado["data"], ensure_ascii=False)

        @tool
        def gerar_grafico(tipo: str, coluna_x: str, coluna_y: str, titulo: str) -> str:
            """Configura a geração determinística de um gráfico Plotly a partir dos dados retornados.
            Args:
                tipo: 'bar' (barras), 'line' (linha/série), 'pie' (pizza) ou 'donut' (rosca).
                coluna_x: nome da coluna para o eixo X ou rótulos.
                coluna_y: nome da coluna para o eixo Y ou valores.
                titulo: título de exibição do gráfico.
            """
            if not self.ultimos_dados:
                return "Aviso: Nenhuma consulta com dados retornados está disponível para gerar o gráfico."

            spec = construir_especificacao_grafico(
                tipo=tipo,
                dados=self.ultimos_dados,
                coluna_x=coluna_x,
                coluna_y=coluna_y,
                titulo=titulo
            )
            self.ultimo_grafico = spec
            return f"Gráfico do tipo '{tipo}' gerado com sucesso com título '{titulo}'."

        return [consultar_banco, gerar_grafico]

    def responder(self, pergunta: str, historico: Optional[List[Dict[str, str]]] = None) -> Dict[str, Any]:
        """Processa a pergunta do gestor e retorna resposta executiva, SQL e gráfico."""
        if not self.api_key:
            return {
                "sucesso": False,
                "erro": "CHAVE_GEMINI_AUSENTE",
                "mensagem": "A variável GEMINI_API_KEY não foi configurada no arquivo .env.",
                "instrucoes": "Crie sua chave gratuita no Google AI Studio (https://aistudio.google.com/) e adicione-a no arquivo backend/.env."
            }

        inicio = time.perf_counter()

        # Modelos para tentar em cascata caso o primeiro falhe por cota (429) ou sobrecarga (503)
        modelos_candidatos = [self.model_name]
        for fallback in [
            "gemini-2.5-flash-lite",
            "gemini-3.1-flash-lite",
            "gemini-3.5-flash-lite",
            "gemini-3.8-flash",
        ]:
            if fallback not in modelos_candidatos:
                modelos_candidatos.append(fallback)

        # 1. Intent Router: classifica a intenção e valida se há ambiguidade antes de acionar SQL
        decisao = classificar_intencao(
            pergunta=pergunta,
            historico=historico,
            api_key=self.api_key,
            modelos_candidatos=modelos_candidatos
        )

        if (decisao.intencao == "esclarecimento" or not decisao.esta_claro) and decisao.pergunta_esclarecimento:
            duracao_ms = round((time.perf_counter() - inicio) * 1000, 2)
            return {
                "sucesso": True,
                "intencao": "esclarecimento",
                "resposta": decisao.pergunta_esclarecimento,
                "sql_executado": None,
                "dados_tabela": [],
                "total_registros": 0,
                "grafico": None,
                "tempo_ms": duracao_ms,
                "modelo_usado": self.model_name
            }

        if decisao.intencao == "conversa_geral" and decisao.resposta_direta:
            duracao_ms = round((time.perf_counter() - inicio) * 1000, 2)
            return {
                "sucesso": True,
                "intencao": "conversa_geral",
                "resposta": decisao.resposta_direta,
                "sql_executado": None,
                "dados_tabela": [],
                "total_registros": 0,
                "grafico": None,
                "tempo_ms": duracao_ms,
                "modelo_usado": self.model_name
            }

        # 2. Execução do Agente SQL + Gráfico usando a intenção consolidada
        ferramentas = self._criar_ferramentas(pergunta)
        ferramentas_map = {f.name: f for f in ferramentas}

        diretriz_router = f"\n\n### DIRETRIZ DO ROTEADOR DE INTENÇÕES:\n- Intenção: {decisao.intencao}\n- Solicitação consolidada: {decisao.intencao_consolidada}"
        if decisao.tipo_grafico:
            diretriz_router += f"\n- Gráfico obrigatório: tipo='{decisao.tipo_grafico}'"
        if decisao.dimensao:
            diretriz_router += f"\n- Dimensão de agrupamento: {decisao.dimensao}"

        ultimo_erro = None
        for modelo_atual in modelos_candidatos:
            try:
                llm = ChatGoogleGenerativeAI(
                    model=modelo_atual,
                    google_api_key=self.api_key,
                    temperature=0.1,
                    max_retries=1
                ).bind_tools(ferramentas)

                mensagens: List[Any] = [SystemMessage(content=SYSTEM_PROMPT + diretriz_router)]
                if historico:
                    for msg in historico[-10:]:
                        role = msg.get("role", "")
                        content = (msg.get("content") or "").strip()
                        if not content:
                            continue
                        if role == "user":
                            mensagens.append(HumanMessage(content=content))
                        elif role == "assistant":
                            mensagens.append(AIMessage(content=content))
                mensagens.append(HumanMessage(content=pergunta))

                # Loop do agente com até 5 iterações para chamadas de ferramentas
                texto_resposta = ""
                houve_chamada_ferramenta = False

                for _ in range(5):
                    resposta_ia = llm.invoke(mensagens)
                    mensagens.append(resposta_ia)

                    tool_calls = getattr(resposta_ia, "tool_calls", [])
                    if not tool_calls:
                        texto_resposta = _extrair_texto(resposta_ia.content)
                        break

                    houve_chamada_ferramenta = True
                    for call in tool_calls:
                        fn_name = call["name"]
                        args = call["args"]
                        tool_func = ferramentas_map.get(fn_name)
                        if tool_func:
                            res_tool = tool_func.invoke(args)
                            mensagens.append(ToolMessage(
                                content=str(res_tool),
                                tool_call_id=call["id"],
                                name=fn_name
                            ))

                # Se houve chamadas de ferramentas e o modelo ainda não sintetizou a resposta em texto
                if houve_chamada_ferramenta and not texto_resposta.strip():
                    llm_sintese = ChatGoogleGenerativeAI(
                        model=modelo_atual,
                        google_api_key=self.api_key,
                        temperature=0.2
                    )
                    mensagens.append(HumanMessage(
                        content="Com base nos dados retornados acima, apresente a resposta final executiva completa para o gestor, aplicando as regras de negócio e a formatação solicitada."
                    ))
                    resposta_sintese = llm_sintese.invoke(mensagens)
                    texto_resposta = _extrair_texto(resposta_sintese.content)

                if not texto_resposta.strip() and self.ultimos_dados:
                    texto_resposta = f"Consultei os dados com sucesso. Foram encontrados {len(self.ultimos_dados)} registros correspondentes à sua solicitação."

                duracao_ms = round((time.perf_counter() - inicio) * 1000, 2)

                return {
                    "sucesso": True,
                    "intencao": decisao.intencao,
                    "resposta": texto_resposta,
                    "sql_executado": self.ultimo_sql,
                    "dados_tabela": self.ultimos_dados[:100],
                    "total_registros": len(self.ultimos_dados),
                    "grafico": self.ultimo_grafico,
                    "tempo_ms": duracao_ms,
                    "modelo_usado": modelo_atual
                }

            except Exception as e:
                ultimo_erro = e
                erro_str = str(e)
                # Em caso de cota (429), sobrecarga temporária (503/500) ou modelo indisponível (404), tenta o próximo modelo
                if any(cod in erro_str for cod in ("429", "RESOURCE_EXHAUSTED", "503", "UNAVAILABLE", "500", "404", "NOT_FOUND")):
                    continue
                else:
                    break

        duracao_ms = round((time.perf_counter() - inicio) * 1000, 2)
        return {
            "sucesso": False,
            "erro": "ERRO_AGENTE",
            "mensagem": f"Erro durante a execução do agente: {str(ultimo_erro)}",
            "tempo_ms": duracao_ms
        }
