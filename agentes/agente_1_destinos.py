from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_tavily import TavilySearch
from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver
from rich.console import Console
from rich.markdown import Markdown


load_dotenv()

#Modelo de IA que vamos usar
model = ChatGoogleGenerativeAI(model="gemini-3.1-flash-lite", temperature=0.7)

#Ferramenra de busca na web tavily
ferramenta_busca = TavilySearch(max_results=5)

tools = [ferramenta_busca]

#Prompt pro Agente
prompt_sistema = """
Você é um surfista brasileiro extremamente experiente e atua como especialista em destinos de surf.
Sua única função é usar sua ferramenta de busca na internet para encontrar os melhores picos de surf que estão em alta no momento.

Regras:
- Sugira destinos incríveis, mencionando a qualidade das ondas.
- Seja amigável e use um tom descontraído de surfista, mas sem exagerar nas gírias.
- NÃO invente informações. Baseie-se apenas nos resultados da sua busca.
- NÃO monte roteiros completos ou calcule preços. Apenas sugira os destinos.
"""

#Memória do Agente
memory = InMemorySaver()

#Agente
agent_1 =  create_agent(
    system_prompt=prompt_sistema,
    model=model,
    tools=tools,
    checkpointer=memory
)

# Este bloco só roda se você executar este arquivo diretamente
if __name__ == "__main__":
    
    console = Console()

    # 1. Criamos a identificação da nossa "prancheta"
    # O thread_id é o que faz o InMemorySaver lembrar desta conversa específica
    config = {"configurable": {"thread_id": "teste_viagem_01"}}

    # 2. A pergunta do usuário
    # Vamos usar um cenário real de viagem de carro pela costa!
    pergunta = "Sou um surfista iniciante e gostaria de ideias de picos bons fora do brasil para uma primeira surftrip de um iniciante!!"

    console.print("Surfista (IA) está pensando e pesquisando na web...\n")

    # 3. Executamos o agente passando a pergunta e a configuração da memória
    resultado = agent_1.invoke(
        {"messages": [("user", pergunta)]},
        config=config

    )

    conteudo_bruto = resultado["messages"][-1].content
    
    # Lógica para extrair apenas o texto limpo
    resposta_texto = ""

    if isinstance(conteudo_bruto, list):
        # Se for uma lista, procura o bloco que tem o texto da resposta
        for item in conteudo_bruto:
            if isinstance(item, dict) and "text" in item:
                resposta_texto += item["text"] + "\n"

    else:
        # Se já vier como string limpa, apenas copia
        resposta_texto = conteudo_bruto    

    # Imprime a resposta formatada bonita no terminal
    console.print("🏄 [bold green]RESPOSTA DO AGENTE:[/bold green]")
    console.print(Markdown(resposta_texto))
    console.print("\n")