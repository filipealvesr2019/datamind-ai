"""Intent Router — Classificador de Intenções e Validador de Parâmetros (Slots)
Analisa a pergunta atual junto com o histórico da conversa antes de acionar o agente SQL:
- Identifica a intenção (consulta_dados, gerar_grafico, esclarecimento, conversa_geral)
- Verifica se faltam parâmetros essenciais (ex.: dimensão de quebra em gráficos de pizza)
- Consolida respostas curtas de follow-up em uma instrução completa para o agente SQL
"""

from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI


class IntentDecision(BaseModel):
    intencao: Literal["consulta_dados", "gerar_grafico", "esclarecimento", "conversa_geral"] = Field(
        description="Classificação principal da solicitação do usuário."
    )
    esta_claro: bool = Field(
        description="True se a solicitação tem informações suficientes para consultar o banco/gerar gráfico; False se está ambígua ou faltando parâmetro essencial."
    )
    intencao_consolidada: str = Field(
        description="Descrição completa e autossuficiente do que o usuário quer, combinando o histórico da conversa com a mensagem atual."
    )
    tipo_grafico: Optional[Literal["line", "bar", "pie", "donut"]] = Field(
        default=None,
        description="Tipo de gráfico solicitado, se aplicável."
    )
    dimensao: Optional[str] = Field(
        default=None,
        description="Dimensão de agrupamento identificada (ex.: 'dia', 'mes', 'categoria', 'produto', 'vendedor', 'status')."
    )
    pergunta_esclarecimento: Optional[str] = Field(
        default=None,
        description="Pergunta curta, objetiva e amigável com 2 ou 3 opções concretas caso esta_claro seja False."
    )
    resposta_direta: Optional[str] = Field(
        default=None,
        description="Resposta direta em português caso intencao seja 'conversa_geral' (ex.: saudações ou dúvidas sobre o que o assistente faz)."
    )


ROUTER_SYSTEM_PROMPT = """Você é o Intent Router (Roteador de Intenções) do DataMind AI, um analista de BI corporativo conectado a um banco SQLite com as tabelas:
- clientes (id, nome, email, cidade, estado, data_cadastro)
- produtos (id, nome, categoria, preco, estoque)
- vendedores (id, nome, email, meta_mensal)
- vendas (id, cliente_id, vendedor_id, data_venda, status)
- itens_venda (id, venda_id, produto_id, quantidade, preco_unitario)
- contas_receber (id, cliente_id, venda_id, valor, vencimento, status_pagamento, data_pagamento)

Seu papel é classificar a intenção do usuário considerando SEMPRE o histórico da conversa + a mensagem atual.

### REGRAS DE DECISÃO:
1. `conversa_geral`:
   - Apenas para saudações simples ("oi", "olá", "tudo bem?"), agradecimentos ("obrigado") ou perguntas sobre suas capacidades ("o que você faz?").
   - Preencha `resposta_direta` de forma simpática e curta.

2. `esclarecimento` (`esta_claro = False`):
   - Use quando faltar um parâmetro crítico que impediria gerar um resultado útil:
     a) O usuário pediu um gráfico de **pizza** ou **rosca** (`pie`/`donut`) de vendas/faturamento SEM especificar a dimensão de divisão (ex.: "gráfico de pizza das vendas do mês atual"). Um gráfico de pizza precisa de múltiplas fatias! Pergunte objetivamente se prefere dividir por **categoria de produto**, por **vendedor**, por **produto** ou por **status da venda**.
     b) O pedido é vago demais sem indicar métrica nem entidade (ex.: "faz um gráfico", "analisa o último mês", "mostra os dados").
   - Preencha `pergunta_esclarecimento` com UMA pergunta curta e direta oferecendo 2 a 3 opções claras.

3. `gerar_grafico` (`esta_claro = True`):
   - Quando o usuário pede um gráfico e os dados necessários estão claros (na mensagem atual ou combinados com o histórico):
     - Ex.: "crie um gráfico de linha com as vendas do mês" -> CLARO! (`tipo_grafico="line"`, `dimensao="dia"`, vendas concluídas do mês mais recente na base).
     - Ex.: "top 5 produtos mais vendidos em gráfico de barras" -> CLARO! (`tipo_grafico="bar"`, `dimensao="produto"`).
     - Ex.: Histórico tinha pedido gráfico de pizza das vendas do mês + assistente perguntou a dimensão + usuário respondeu "por vendedor" -> CLARO! (`tipo_grafico="pie"`, `dimensao="vendedor"`, `intencao_consolidada="Gerar gráfico de pizza com o faturamento das vendas concluídas do mês mais recente agrupadas por vendedor"`).

4. `consulta_dados` (`esta_claro = True`):
   - Perguntas diretas de negócio (faturamento total, ticket médio, inadimplência, melhor vendedor, ranking de produtos, listas de clientes, etc.).
   - IMPORTANTE: Se o usuário tentar comandos perigosos/mutação (ex.: "apague a tabela de clientes", "DELETE", "DROP"), classifique como `consulta_dados` (`esta_claro = True`) para que passe pela camada de segurança SQL e seja auditado como bloqueio.

5. CONSOLIDAÇÃO DO HISTÓRICO:
   - Sempre reescreva `intencao_consolidada` de forma completa juntando o contexto anterior com a resposta atual do usuário.
"""


def _formatar_historico(historico: Optional[List[Dict[str, str]]]) -> str:
    if not historico:
        return "(Sem histórico anterior)"
    linhas = []
    for msg in historico[-8:]:
        role = "Usuário" if msg.get("role") == "user" else "Assistente"
        content = (msg.get("content") or "").strip()
        if content:
            linhas.append(f"{role}: {content[:400]}")
    return "\n".join(linhas) if linhas else "(Sem histórico anterior)"


def classificar_intencao(
    pergunta: str,
    historico: Optional[List[Dict[str, str]]],
    api_key: str,
    modelos_candidatos: List[str]
) -> IntentDecision:
    """Classifica a intenção do usuário com saída estruturada (Pydantic) e fallback entre modelos."""
    contexto_historico = _formatar_historico(historico)
    prompt_usuario = (
        f"HISTÓRICO DA CONVERSA:\n{contexto_historico}\n\n"
        f"MENSAGEM ATUAL DO USUÁRIO:\n{pergunta}"
    )

    for modelo_atual in modelos_candidatos:
        try:
            llm_router = ChatGoogleGenerativeAI(
                model=modelo_atual,
                google_api_key=api_key,
                temperature=0.0,
                max_retries=1
            ).with_structured_output(IntentDecision)

            decisao = llm_router.invoke([
                SystemMessage(content=ROUTER_SYSTEM_PROMPT),
                HumanMessage(content=prompt_usuario)
            ])
            if isinstance(decisao, IntentDecision):
                return decisao
        except Exception as e:
            erro_str = str(e)
            if any(cod in erro_str for cod in ("429", "RESOURCE_EXHAUSTED", "503", "UNAVAILABLE", "500", "404", "NOT_FOUND")):
                continue
            break

    # Fallback seguro: segue direto para o agente de dados sem travar o fluxo
    return IntentDecision(
        intencao="consulta_dados",
        esta_claro=True,
        intencao_consolidada=pergunta
    )
