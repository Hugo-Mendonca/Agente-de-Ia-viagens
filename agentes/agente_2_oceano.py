from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_tavily import TavilySearch
from langchain.agents import create_agent
import sys
import os
import asyncio
from langgraph.checkpoint.memory import InMemorySaver
from rich.console import Console
from rich.markdown import Markdown

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from tools.custom_mcps import buscar_condicoes_mar

load_dotenv()

# 1. Modelo de IA corrigido para a versão real
model = ChatGoogleGenerativeAI(model="gemini-3.1-flash-lite", temperature=0.7)

# 2. Ferramentas passadas como referências para o Agente escolher quando usar
tools = [buscar_condicoes_mar, TavilySearch(max_results=5)]

prompt_sistema = """
Você é um especialista em análise oceânica focado para o surf.
Sua única função será fazer uma análise elaborada sobre as condições de surf em praias específicas.

Regras:
- Traga informações sobre o tipo de fundo da praia (ex: bancada de pedra, coral ou areia).
- Traga previsões detalhadas para os próximos 3 dias.
- NÃO invente informações. Baseie-se apenas nos resultados das pesquisas e das ferramentas.
- NÃO monte roteiros completos ou calcule preços. Foque estritamente nas condições do mar.
- Monte um plano claro com: altura das ondas, período, horário da maré cheia e maré seca, temperatura da água e ventos (direção e velocidade).
"""

memory = InMemorySaver()

# 3. Agente criado com o padrão LangGraph
agent_2 = create_agent(
    model=model,
    tools=tools,
    system_prompt=prompt_sistema,
    checkpointer=memory
)

if __name__ == "__main__":
    async def teste():
        console = Console()
        
        config = {"configurable": {"thread_id": "teste_previsao01"}}
        pergunta = "Sou um surfista iniciante e estou planejando uma viagem para Ipojuca e gostaria de saber como estará o mar nesse final de semana (sexta, sábado e domingo)."

        console.print("🌊 Analista de Oceanografia (IA) está checando as condições do mar...\n")

        resultado =  await agent_2.ainvoke(
            {"messages": [("user", pergunta)]},
            config=config
        )

        conteudo_bruto = resultado["messages"][-1].content
        
        # Lógica de extração segura da string
        resposta_texto = ""
        if isinstance(conteudo_bruto, list):
            for item in conteudo_bruto:
                if isinstance(item, dict) and "text" in item:
                    resposta_texto += item["text"] + "\n"
        else:
            resposta_texto = conteudo_bruto    

        console.print("🏄 [bold green]RESPOSTA DO AGENTE OCEANOGRÁFICO:[/bold green]")
        console.print(Markdown(resposta_texto))
        console.print("\n")
    asyncio.run(teste())