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
from tools.custom_mcps import  buscar_meios_locomocao
from tools.calculadora import calculadora


load_dotenv()

model = ChatGoogleGenerativeAI(model="gemini-3.1-flash-lite", temperature=0.7)

tools = [buscar_meios_locomocao, calculadora, TavilySearch(max_results=5)]

memory = InMemorySaver()

prompt_sistema = """
Você é um agente de logística de viagens focado em surfistas.

### Regra de Ouro da Origem:
- Sua localização padrão é Recife, PE.
- SEMPRE inicie a conversa perguntando ou confirmando: "Você está saindo de Recife ou de outra cidade?".
- NÃO prossiga para cálculos de custos ou recomendações de transporte até ter certeza absoluta de onde o usuário está saindo.
- Se o usuário confirmar uma cidade diferente, ajuste todos os cálculos (distância, combustível, voos) para essa nova origem.

- Sempre identifique de onde o usuário está saindo. Se ele não informar, pergunte ou utilize a localização atual detectada no contexto.
- Para distâncias > 500km, priorize o transporte aéreo (pesquise voos) + aluguel de carro no destino.
- Para distâncias < 500km, priorize o deslocamento por carro próprio ou alugado.
- AO CALCULAR GASTOS DE COMBUSTÍVEL: Não utilize médias nacionais. Use a ferramenta de busca (Tavily) para encontrar o preço médio atual da gasolina na cidade de partida e o valor atualizado do pedágio nas rodovias da rota.
- Sempre especifique os dados utilizados: "Preço do combustível usado: R$ X,XX/L (Fonte: [Fonte])".

1. **Diversidade de Preços:** Nunca traga apenas uma faixa de preço. Sempre busque apresentar um mix equilibrado (ex: Opção Custo-Benefício, Opção Econômica e Opção Premium/Luxo).
2. **Confiabilidade:** Certifique-se de que os locais recomendados possuem boas avaliações e plataformas de reserva confiáveis (como Booking.com ou canais oficiais).
3. **Clareza e Organização:** Apresente os resultados de forma limpa, destacando o nome do hotel, o tipo de quarto, o valor total para o período da estadia e o canal/plataforma de reserva.

### Regras Operacionais:
- Utilize as ferramentas de MCP disponíveis para consultar dados reais de disponibilidade e tarifas.
- Caso uma busca retorne falha ou timeout, adote um fallback inteligente ou informe o usuário de forma transparente.
- Sempre informe que são apenas dicas de transporte e que os valores são variáveis e sucetíveis a erro!
- Nunca invente preços ou locadoras/companias aéreas; baseie-se estritamente nos dados retornados pelas ferramentas de busca.
- Traga sempre a fonte da sua informação.
"""
agent_4 = create_agent(
    model=model,
    tools=tools,
    system_prompt=prompt_sistema,
    checkpointer=memory
)


if __name__ == "__main__":
    import asyncio
    
    async def chat_interativo():
        console = Console()
        # Thread ID fixo para manter a conversa na memória do LangGraph
        config = {"configurable": {"thread_id": "sessao_transporte_01"}}
        
        # Primeira pergunta
        pergunta_atual = "Sou um surfista iniciante e estou planejando uma viagem para Ipojuca e queria saber como deve ser minhas opções de se locomover para lá."
        
        while True:
            console.print(f"\n[bold blue]Você:[/bold blue] {pergunta_atual}")
            console.print("🌊 [italic]O agente está processando...[/italic]\n")
            
            # O agente lê a pergunta e usa a memória do thread_id automaticamente
            resultado = await agent_4.ainvoke(
                {"messages": [("user", pergunta_atual)]},
                config=config
            )
            
            # Extração segura da resposta
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
                
            # Mostra a resposta do agente na tela
            console.print(Markdown(f"🏄 **Agente:**\n{resposta_texto}\n"))
            
            # Pede a sua próxima entrada no terminal
            pergunta_atual = console.input("[bold blue]Sua resposta (ou digite 'sair'):[/bold blue] ")
            if pergunta_atual.lower() in ["sair", "tchau"]:
                console.print("\n[bold yellow]Até logo![/bold yellow]")
                break

    asyncio.run(chat_interativo())