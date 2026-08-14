import asyncio
import json
import httpx

async def extrair_hoteis_com_fonte():
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
                "checkin": "2026-10-10",
                "checkout": "2026-10-15",
                "currency": "BRL",
                "guestNationality": "BR",
                "occupancies": [{"adults": 2}],
                "cityName": "Pipa",
                "countryCode": "BR",
                "limit": 3
            }
        },
        "id": 1
    }
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        resposta = await client.post(url, json=payload, headers=headers)
        
        conteudo_json = None
        for linha in resposta.text.splitlines():
            if linha.startswith("data: "):
                conteudo_json = linha.replace("data: ", "", 1).strip()
                break
                
        if conteudo_json:
            dados_brutos = json.loads(conteudo_json)
            texto_interno = dados_brutos["result"]["content"][0]["text"]
            resultado = json.loads(texto_interno)
            
            hoteis_info = {h["id"]: h for h in resultado.get("hotels", [])}
            ofertas = resultado.get("data", [])
            
            print("="*65)
            print("🏨 RELATÓRIO DE HOSPEDAGEM COM PLATAFORMA DE RESERVA")
            print("="*65)
            
            for oferta in ofertas:
                hotel_id = oferta.get("hotelId")
                hotel_detalhes = hoteis_info.get(hotel_id, {})
                nome_hotel = hotel_detalhes.get("name", "Hotel Desconhecido")
                estrelas = hotel_detalhes.get("stars", "?")
                
                print(f"\n📍 **{nome_hotel}** ({estrelas} estrelas)")
                
                quartos_unicos = {}
                
                for quarto in oferta.get("roomTypes", []):
                    nome_quarto = quarto.get("name", "Acomodação Standard")
                    
                    for rate in quarto.get("rates", []):
                        preco = rate.get("retailRate", {}).get("total", [{}])[0].get("amount")
                        
                        # Pegando a fonte sugerida (ex: booking.com)
                        sugestao_preco = rate.get("retailRate", {}).get("suggestedSellingPrice", [{}])
                        fonte = "Plataforma Oficial"
                        if sugestao_preco and isinstance(sugestao_preco, list):
                            fonte = sugestao_preco[0].get("source", "Plataforma Oficial")
                            if not fonte:
                                fonte = "Booking.com"
                        
                        if preco:
                            if nome_quarto not in quartos_unicos or preco < quartos_unicos[nome_quarto]["preco"]:
                                quartos_unicos[nome_quarto] = {
                                    "preco": preco,
                                    "fonte": fonte.capitalize()
                                }
                
                for quarto_nome, info in quartos_unicos.items():
                    print(f"   └── 🛏️ {quarto_nome}")
                    print(f"       💰 Melhor Valor (5 diárias): R$ {info['preco']:,.2f}")
                    print(f"       🌐 Canal/Plataforma: {info['fonte']}")
                    
            print("\n" + "="*65)
        else:
            print("Erro ao processar os dados.")