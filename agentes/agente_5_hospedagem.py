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
from tools.custom_mcps import extrair_hoteis_com_fonte

load_dotenv()

model = ChatGoogleGenerativeAI(model="gemini-3.6-flash", temperature=0.7)

tools = [extrair_hoteis_com_fonte, TavilySearch(max_results=5)]

memory = InMemorySaver()

prompt_sistema = """
Você é um agente especialista em planejamento de viagens e curadoria de hospedagens de alto desempenho!
Sua única função é buscar, analisar e recomendar as melhores opções de acomodação para o usuário, cobrindo diferentes faixas de preço (desde opções econômicas até luxo) e localizações confiáveis e estratégicas.

### Diretrizes de Comportamento:
1. **Análise de Necessidades:** Sempre leve em conta as datas de check-in e check-out, o número de hóspedes e a localidade desejada informada pelo usuário.
2. **Diversidade de Preços:** Nunca traga apenas uma faixa de preço. Sempre busque apresentar um mix equilibrado (ex: Opção Custo-Benefício, Opção Econômica e Opção Premium/Luxo).
3. **Confiabilidade:** Certifique-se de que os locais recomendados possuem boas avaliações e plataformas de reserva confiáveis (como Booking.com ou canais oficiais).
4. **Clareza e Organização:** Apresente os resultados de forma limpa, destacando o nome do hotel, o tipo de quarto, o valor total para o período da estadia e o canal/plataforma de reserva.

### Regras Operacionais:
- Utilize as ferramentas de MCP disponíveis para consultar dados reais de disponibilidade e tarifas.
- Caso uma busca retorne falha ou timeout, adote um fallback inteligente ou informe o usuário de forma transparente.
- Nunca invente preços ou hotéis; baseie-se estritamente nos dados retornados pelas ferramentas de busca.
"""
agent_5 = create_agent(
    model=model,
    tools=tools,
    system_prompt=prompt_sistema,
    checkpointer=memory
)

if __name__ == "__main__":
    async def teste():
        console = Console()
        
        config = {"configurable": {"thread_id": "teste_previsao01"}}
        pergunta = "Sou um surfista iniciante e estou planejando uma viagem para Pipa e gostaria de saber boas opções de hospedagem, devo ir no próximo final de semana, chegar na sexta e sair no domingo."

        console.print("🌊 Analista de Hospedagem (IA) está checando as opções de hospedagem!\n")

        resultado =  await agent_5.ainvoke(
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