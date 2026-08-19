import operator
from typing import Annotated, Literal
from typing_extensions import TypedDict
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field

from agentes.agente_1_destinos import agent_1
from agentes.agente_2_oceano import agent_2
from agentes.agente_4_custos import agent_4
from agentes.agente_5_hospedagem import agent_5

# 1. Estado compartilhado
class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    agentes_concluidos: Annotated[list[str], operator.add]
    proxima_instrucao: str
    next_step: str
    dados_destinos: str
    dados_oceano: str
    dados_hospedagem: str
    dados_custos: str

# 2. Decisão Estruturada do Supervisor
class DecisaoSupervisor(BaseModel):
    proximo_agente: Literal["agente_destinos", "agente_oceano", "agente_hospedagem", "agente_custos", "FINISH"] = Field(
        description="Especialista a acionar ou FINISH se já tiver todos os dados necessários."
    )
    instrucao_especifica: str = Field(
        description="Pergunta detalhada e contextualizada para o especialista resolver."
    )

llm = ChatGoogleGenerativeAI(model="gemini-3.1-flash-lite", temperature=0.1)
supervisor_estruturado = llm.with_structured_output(DecisaoSupervisor)

# 3. Nó Central: Agente Pai
async def agente_pai_node(state: AgentState):
    concluidos = state.get("agentes_concluidos", [])
    usuario_msg = state["messages"][0].content
    
    # Se todos os 4 já responderam, encerra montando a síntese
    if set(["agente_destinos", "agente_oceano", "agente_hospedagem", "agente_custos"]).issubset(set(concluidos)):
        prompt_sintese = f"""Você é o Orquestrador Principal de Surf Trips.
Consolide todas as análises dos seus especialistas em um relatório final rico, matemático e detalhado:

- DESTINOS: {state.get('dados_destinos', '')}
- OCEANOGRAFIA: {state.get('dados_oceano', '')}
- HOSPEDAGEM: {state.get('dados_hospedagem', '')}
- CUSTOS & LOGÍSTICA: {state.get('dados_custos', '')}

# 🏄 Roteiro de Surf Trip: [Destino]

## 1. 🌊 Análise Oceanográfica & Condições do Mar
## 2. 🏨 Opções de Hospedagem & Tarifas
## 3. 🚗 Logística & Deslocamento
## 4. 💰 Orçamento Consolidado da Viagem
"""
        resposta_final = await llm.ainvoke([HumanMessage(content=prompt_sintese)])
        return {
            "next_step": "FINISH",
            "messages": [resposta_final]
        }

    # Prompt para o Pai decidir quem chamar e o que perguntar
    prompt_decisao = f"""Você é o Agente Pai (Supervisor).
Pedido original do usuário: "{usuario_msg}"

Histórico de dados coletados até agora:
- Destinos: {state.get('dados_destinos', 'Não coletado')}
- Oceano: {state.get('dados_oceano', 'Não coletado')}
- Hospedagem: {state.get('dados_hospedagem', 'Não coletado')}
- Custos: {state.get('dados_custos', 'Não coletado')}

Agentes que JÁ foram executados: {concluidos}.
NUNCA escolha um agente que já está na lista de executados.

Ordem recomendada:
1. 'agente_destinos' (para definir as praias)
2. 'agente_oceano' (para analisar o mar das praias escolhidas)
3. 'agente_hospedagem' (para cotar pousadas nessas praias)
4. 'agente_custos' (para calcular transporte e fechar contas)
"""
    decisao = await supervisor_estruturado.ainvoke([HumanMessage(content=prompt_decisao)])
    
    return {
        "next_step": decisao.proximo_agente,
        "proxima_instrucao": decisao.instrucao_especifica
    }

# 4. Nós dos Especialistas (Executam a instrução preparada pelo Pai)
async def destinos_node(state: AgentState):
    res = await agent_1.ainvoke({"messages": [HumanMessage(content=state["proxima_instrucao"])]})
    texto = str(res["messages"][-1].content)
    return {"dados_destinos": texto, "agentes_concluidos": ["agente_destinos"]}

async def oceano_node(state: AgentState):
    res = await agent_2.ainvoke({"messages": [HumanMessage(content=state["proxima_instrucao"])]})
    texto = str(res["messages"][-1].content)
    return {"dados_oceano": texto, "agentes_concluidos": ["agente_oceano"]}

async def hospedagem_node(state: AgentState):
    res = await agent_5.ainvoke({"messages": [HumanMessage(content=state["proxima_instrucao"])]})
    texto = str(res["messages"][-1].content)
    return {"dados_hospedagem": texto, "agentes_concluidos": ["agente_hospedagem"]}

async def custos_node(state: AgentState):
    res = await agent_4.ainvoke({"messages": [HumanMessage(content=state["proxima_instrucao"])]})
    texto = str(res["messages"][-1].content)
    return {"dados_custos": texto, "agentes_concluidos": ["agente_custos"]}

# 5. Construção do Grafo Hub-and-Spoke
workflow = StateGraph(AgentState)

workflow.add_node("agente_pai", agente_pai_node)
workflow.add_node("agente_destinos", destinos_node)
workflow.add_node("agente_oceano", oceano_node)
workflow.add_node("agente_hospedagem", hospedagem_node)
workflow.add_node("agente_custos", custos_node)

# Entrada sempre no Pai
workflow.add_edge(START, "agente_pai")

# Roteamento condicional do Pai para os especialistas ou encerramento
workflow.add_conditional_edges(
    "agente_pai",
    lambda state: state["next_step"],
    {
        "agente_destinos": "agente_destinos",
        "agente_oceano": "agente_oceano",
        "agente_hospedagem": "agente_hospedagem",
        "agente_custos": "agente_custos",
        "FINISH": END
    }
)

# Todos os especialistas retornam para o nó central do Pai
workflow.add_edge("agente_destinos", "agente_pai")
workflow.add_edge("agente_oceano", "agente_pai")
workflow.add_edge("agente_hospedagem", "agente_pai")
workflow.add_edge("agente_custos", "agente_pai")

agente_pai = workflow.compile()