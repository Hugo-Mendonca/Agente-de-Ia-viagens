import asyncio
from typing import Literal
import sys
import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.tools import tool
from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver
from rich.console import Console
from rich.markdown import Markdown


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from agentes.agente_1_destinos import agent_1
from agentes.agente_2_oceano import agent_2
#from agentes.agente_3_guia import agent_3
from agentes.agente_4_custos import agent_4
from agentes.agente_5_hospedagem import agent_5

load_dotenv()

@tool
async def consultar_destinos(pergunta: str)-> str:
    """
    Acione o Agente de destinos, especialista em buscar bons destinos de viagens para surfistas indecisos que querem fazer sua primeira trip,
    Um surfista experiente capaz de identificar boas trips para qualquer tipo de surfista
    """
    config = {"configurable":{"thread_id":"sub_destinos"}}
    resultado = await agent_1.ainvoke({"messages": [("user", pergunta)]}, config=config)
    conteudo = resultado["messages"][-1].content
    if isinstance(conteudo, list):
        return "".join([item.get("text", "") for item in conteudo if isinstance(item, dict)])
    return str(conteudo)

@tool
async def consultar_oceano(pergunta:str)->str:
    """
    Acione o Agente Oceanográfico, especilista para buscar condições de mar, 
    swell, vento, maré e picos ideais para surf em praias específicas.
    """
    config = {"configurable": {"thread_id": "sub_oceano"}}
    resultado = await agent_2.ainvoke({"messages": [("user", pergunta)]}, config=config)
    conteudo = resultado["messages"][-1].content
    if isinstance(conteudo, list):
        return "".join([item.get("text", "") for item in conteudo if isinstance(item, dict)])
    return str(conteudo)

#@tool
#async def consultar_guia(pergunta:str)->str:
#    """
#    Acione o Agente Guia, especialista em montar um guia turístico para qualquer lugar,
#    Sabe indenficar os melhores passeios, restaurantes e recomendações de qualquer lugar.
#    """
#    config = {"configurable": {"thread_id": "sub_guia"}}
#    resultado = await agent_3.ainvoke({"messages": [("user", pergunta)]}, config=config)
#    conteudo = resultado["messages"][-1].content
#    if isinstance(conteudo, list):
#        return "".join([item.get("text", "") for item in conteudo if isinstance(item, dict)])
#    return str(conteudo)

@tool
async def consultar_locomocao_custos(pergunta: str)->str:
    """
    Aciona o Agente de Transporte e Custos para analisar a logística de deslocamento 
    (carro, voo, combustível, pedágios) e calcular o orçamento consolidado da viagem.
    """
    config = {"configurable": {"thread_id": "sub_locomocao"}}
    resultado = await agent_4.ainvoke({"messages": [("user", pergunta)]}, config=config)
    conteudo = resultado["messages"][-1].content
    if isinstance(conteudo, list):
            return "".join([item.get("text", "") for item in conteudo if isinstance(item, dict)])
    return str(conteudo)

@tool
async def consultar_hospedagens(pergunta: str) -> str:
    """
    Aciona o Agente de Hospedagem especialista para buscar pousadas, hotéis, 
    valores reais de diárias e canais de reserva para o destino e período informados.
    """
    config = {"configurable": {"thread_id": "sub_hospedagem"}}
    resultado = await agent_5.ainvoke({"messages": [("user", pergunta)]}, config=config)
    conteudo = resultado["messages"][-1].content
    if isinstance(conteudo, list):
        return "".join([item.get("text", "") for item in conteudo if isinstance(item, dict)])
    return str(conteudo)

model = ChatGoogleGenerativeAI(model=f"gemini-3.1-flash-lite", temperature=0.5) 

tools_supervisor = [
    consultar_destinos,
    consultar_hospedagens,
    #consultar_guia,
    consultar_locomocao_custos,
    consultar_oceano
]

prompt_supervisor = """
Você é o Orquestrador Principal (Agente Pai) de um sistema de planejamento de viagens de surf de alto nível.
Sua missão é coordenar os agentes especialistas e entregar um plano de viagem DETALHADO, RICO EM DADOS e FINANCEIRAMENTE CONSOLIDADO.

### DIRETRIZES DE PRESERVAÇÃO DE DADOS (CRÍTICO):
1. **NUNCA resuma ou omita os preços:** Se o especialista de hospedagem retornou nomes de pousadas, faixas de preço (R$) e canais de reserva, você DEVE incluir todas essas opções na resposta final.
2. **Cálculos Matemáticos Obrigatórios:** Traga a matemática detalhada do combustível (km, consumo, preço/L) e pedágios.
3. **Consolidação Financeira:** Apresente sempre a tabela ou bloco consolidado com o CUSTO TOTAL DA VIAGEM (Hospedagem + Deslocamento + Pedágios + Gastos Extras).
4. **Detalhes Técnicos de Surf:** Traga as informações de vento, maré, swell e tipo de fundo completas que o especialista oceanográfico fornecer.

### ESTRUTURA OBRIGATÓRIA DA RESPOSTA FINAL:
Sua resposta final ao usuário DEVE conter exatamente estas seções bem formatadas em Markdown:

# 🏄 Roteiro de Surf Trip: [Destino]

## 1. 🌊 Análise Oceanográfica & Condições do Mar
- Melhores picos recomendados para o nível do surfista
- Análise de fundo, maré ideal, vento e segurança

## 2. 🏨 Opções de Hospedagem & Tarifas
- Apresentar as opções retornadas (Econômica, Custo-Benefício, Conforto) com os valores reais em R$ e canais de reserva sugeridos.

## 3. 🚗 Logística & Deslocamento
- Rota recomendada, distância e tempo estimado
- Cálculo detalhado de combustível e pedágios

## 4. 💰 Orçamento Consolidado da Viagem
- Tabela discriminando: Hospedagem + Combustível + Pedágios + Alimentação/Aulas estimadas
- **Custo Total Estimado da Viagem (R$)**
- **Custo Rateado por Pessoa**
"""

memory = InMemorySaver()

agente_pai = create_agent(
    model=model,
    tools= tools_supervisor,
    system_prompt= prompt_supervisor,
    checkpointer= memory
)

if __name__ == "__main__":
    async def chat_orquestrador():
        console = Console()
        config = {"configurable": {"thread_id": "sessao_orquestrador_01"}}
        
        pergunta = "Sou um surfista intermediário saindo de Recife e quero planejar uma surftrip para alguma piscina de onda no brasil. Me ajude com tudo: hospedagem, transporte e o custo total."        
        console.print(f"[bold blue]Você:[/bold blue] {pergunta}\n")
        console.print("🚀 [bold magenta]Orquestrador Principal ativado, consultando especialistas...[/bold magenta]\n")
        
        resultado = await agente_pai.ainvoke(
            {"messages": [("user", pergunta)]},
            config=config
        )
        
        conteudo_bruto = resultado["messages"][-1].content
        resposta_texto = ""
        if isinstance(conteudo_bruto, list):
            for item in conteudo_bruto:
                if isinstance(item, dict) and "text" in item:
                    resposta_texto += item["text"]
                elif isinstance(item, str):
                    resposta_texto += item
        else:
            resposta_texto = conteudo_bruto
            
        console.print("📋 [bold green]PLANO DE VIAGEM CONSOLIDADO:[/bold green]\n")
        console.print(Markdown(resposta_texto))

    asyncio.run(chat_orquestrador())