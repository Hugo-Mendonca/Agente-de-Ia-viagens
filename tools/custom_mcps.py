import asyncio
import json
import httpx
from langchain.tools import tool
import random

@tool
# Adicionamos 'async' aqui e tipagem para ajudar o LLM a entender a ferramenta
async def buscar_condicoes_mar(cidade: str, pais: str) -> str:
    """
    Busca as condições do mar, swell, vento e clima de praias de surf próximas a uma cidade.
    """
    url = "https://getbeachfinder.com/mcp"
    headers = {
        "Accept": "application/json, text/event-stream",
        "Content-Type": "application/json"
    }
    
    payload = {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
            "name": "search_surf_spots",
            "arguments": {
                "city": cidade,
                "country": pais,
                "radiusKm": 50
            }
        },
        "id": 2
    }
    
    # Usamos o AsyncClient do httpx com 'async with' e 'await'
    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            resposta = await client.post(url, json=payload, headers=headers)
            
            linhas = resposta.text.splitlines()
            for linha in linhas:
                if linha.startswith("data: "):
                    texto_limpo = linha.replace("data: ", "", 1).strip()
                    try:
                        dados = json.loads(texto_limpo)
                        # Agentes leem strings melhor do que dicionários Python
                        return json.dumps(dados, ensure_ascii=False)
                    except json.JSONDecodeError:
                        return "Erro interno: Falha ao decodificar os dados do servidor."
                        
            return "Erro: Formato de resposta inesperado do servidor oceânico."
            
        except Exception as e:
            return f"Erro de conexão ao buscar condições do mar: {str(e)}"

@tool   
async def buscar_meios_locomocao(nome_ferramenta: str, argumentos: dict) -> str:
    """
    Função universal para o LLM acionar qualquer ferramenta do Wingie Enuygun.
    """
    url = "https://mcp.enuygun.com/mcp"
    headers = {
        "Accept": "application/json, text/event-stream",
        "Content-Type": "application/json"
    }
    
    # O comando muda para 'tools/call' e passamos os parâmetros gerados pela IA
    payload = {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
            "name": nome_ferramenta,
            "arguments": argumentos
        },
        "id": 3
    }
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            resposta = await client.post(url, json=payload, headers=headers)
            content_type = resposta.headers.get("Content-Type", "")
            
            # Cenário 1: Servidor devolve JSON nativo
            if "application/json" in content_type:
                dados = resposta.json()
                return json.dumps(dados, ensure_ascii=False)
                
            # Cenário 2: Servidor devolve envelopado em SSE (data: )
            else:
                linhas = resposta.text.splitlines()
                for linha in linhas:
                    if linha.startswith("data: "):
                        texto_limpo = linha.replace("data: ", "", 1).strip()
                        dados = json.loads(texto_limpo)
                        # Retornamos como string JSON para o LLM conseguir ler
                        return json.dumps(dados, ensure_ascii=False)
                        
            return f"Erro: Formato de resposta não reconhecido. Resposta bruta: {resposta.text}"
            
        except Exception as e:
            return f"Erro de conexão com a infraestrutura de reservas: {str(e)}"

@tool
async def extrair_hoteis_com_fonte(cityName: str, checkin: str, checkout: str, countryCode: str = "BR") -> str:    
    """
    Busca opções de hospedagem, hotéis e pousadas baratas em uma cidade específica, 
    retornando os valores e as fontes/links para a viagem.
    
    Args:
        cityName: O nome da cidade de destino extraído da pergunta (ex: Ipojuca, Recife)
        checkin: Data de checkin no formato YYYY-MM-DD
        checkout: Data de checkout no formato YYYY-MM-DD
        countryCode: Sigla do país (padrão é BR)
    """
    url = "https://mcp.maqami.co/"
    headers = {
        "Accept": "application/json, text/event-stream",
        "Content-Type": "application/json"
    }   
    
    payload = {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
            "name": "post_hotels_rates",
            "arguments": {
                "checkin": checkin,
                "checkout": checkout,
                "currency": "BRL",
                "guestNationality": "BR",
                "occupancy": [{"adults": 2}],
                "cityName": cityName,
                "countryCode": countryCode,
                "limit": 3
            }
        },
        "id": random.randint(1, 10000)
    }
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            resposta = await client.post(url, json=payload, headers=headers)
        except Exception as e:
            return f"Erro de conexão com o servidor de hospedagem: {str(e)}"
        
        conteudo_json = None
        for linha in resposta.text.splitlines():
            if linha.startswith("data: "):
                conteudo_json = linha.replace("data: ", "", 1).strip()
                break
                
        if not conteudo_json:
            return f"Erro: O servidor não retornou dados válidos para {cityName} nas datas informadas."

        try:
            dados_brutos = json.loads(conteudo_json)
            texto_interno = dados_brutos["result"]["content"][0]["text"]
            resultado = json.loads(texto_interno)
        except Exception as e:
            return f"Erro ao decodificar a resposta do servidor: {str(e)}"
            
        hoteis_info = {h["id"]: h for h in resultado.get("hotels", [])}
        ofertas = resultado.get("data", [])
        
        if not ofertas:
            return f"Nenhuma hospedagem encontrada para {cityName} no período de {checkin} a {checkout}."

        relatorio = f"🏨 **Hospedagens encontradas em {cityName} ({checkin} a {checkout})**:\n"
        
        for oferta in ofertas:
            hotel_id = oferta.get("hotelId")
            hotel_detalhes = hoteis_info.get(hotel_id, {})
            nome_hotel = hotel_detalhes.get("name", "Hotel Desconhecido")
            estrelas = hotel_detalhes.get("stars", "?")
            
            relatorio += f"\n📍 **{nome_hotel}** ({estrelas} estrelas)\n"
            
            quartos_unicos = {}
            for quarto in oferta.get("roomTypes", []):
                nome_quarto = quarto.get("name", "Acomodação Standard")
                
                for rate in quarto.get("rates", []):
                    preco = rate.get("retailRate", {}).get("total", [{}])[0].get("amount")
                    sugestao_preco = rate.get("retailRate", {}).get("suggestedSellingPrice", [{}])
                    fonte = "Plataforma Oficial"
                    if sugestao_preco and isinstance(sugestao_preco, list):
                        fonte = sugestao_preco[0].get("source", "Plataforma Oficial") or "Booking.com"
                    
                    if preco:
                        if nome_quarto not in quartos_unicos or preco < quartos_unicos[nome_quarto]["preco"]:
                            quartos_unicos[nome_quarto] = {
                                "preco": preco,
                                "fonte": fonte.capitalize()
                            }
            
            for quarto_nome, info in quartos_unicos.items():
                relatorio += f"   └── 🛏️ {quarto_nome}\n"
                relatorio += f"       💰 Melhor Valor: R$ {info['preco']:,.2f}\n"
                relatorio += f"       🌐 Canal/Plataforma: {info['fonte']}\n"
                
        return relatorio