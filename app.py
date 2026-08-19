import uuid
import chainlit as cl
from core.agente_pai import agente_pai

@cl.on_chat_start
async def start():
    # Gera um ID único para cada sessão de chat aberta no navegador
    session_id = str(uuid.uuid4())
    cl.user_session.set("thread_id", session_id)
    
    await cl.Message(
        content=(
            "🏄 **Olá! Eu sou o seu Assistente Especialista em Surf Trips.**\n\n"
            "Posso planejar sua viagem completa: escolher os melhores picos para o seu nível, "
            "analisar as condições do mar, buscar hospedagens e calcular todo o orçamento.\n\n"
            "👉 *Me diga: para onde você quer viajar (ou que tipo de onda busca) e de onde você está saindo?*"
        )
    ).send()

@cl.on_message
async def main(message: cl.Message):
    thread_id = cl.user_session.get("thread_id")
    config = {"configurable": {"thread_id": thread_id}}
    
    # Cria uma mensagem inicial indicando que os especialistas estão trabalhando
    msg = cl.Message(content="🌊 *Consultando os especialistas e montando seu planejamento...*", author="Surf Trip Guide")
    await msg.send()
    
    # Invoca o Agente Pai com o thread_id contínuo
    resultado = await agente_pai.ainvoke(
        {"messages": [("user", message.content)]},
        config=config
    )
    
    # Extração segura da resposta final
    conteudo_bruto = resultado["messages"][-1].content
    resposta_texto = ""
    if isinstance(conteudo_bruto, list):
        for item in conteudo_bruto:
            if isinstance(item, dict) and "text" in item:
                resposta_texto += item["text"]
            elif isinstance(item, str):
                resposta_texto += item
    else:
        resposta_texto = str(conteudo_bruto)
        
    # Atualiza a mensagem na tela com a resposta formatada
    msg.content = resposta_texto
    await msg.update()