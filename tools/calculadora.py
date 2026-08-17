from langchain.tools import tool

@tool
async def calculadora(
    custo_transporte: float = 0.0,
    custo_combustivel: float = 0.0,
    custo_pedagios: float = 0.0,
    custo_hospedagem: float = 0.0,
    custo_alimentacao_extra: float = 0.0,
    custo_passeios: float = 0.0,
    custo_variaveis: float = 0.0,
    qtd_pessoas: int = 1
)-> str:
    
    """
    Calcula o custo consolidado da viagem, somando transporte/aluguel, combustível, 
    pedágios, hospedagem e extras, calculando também o valor rateado por pessoa.
    
    Args:
        custo_transporte: Gasto com passagens aéreas ou aluguel de veículo (R$).
        custo_combustivel: Gasto estimado com gasolina/álcool (R$).
        custo_pedagios: Total de tarifas de pedágio (R$).
        custo_hospedagem: Valor total das diárias de hospedagem (R$).
        custo_variáveis: Custos que estão fora do escopo, meio que uma reserva de emergência(R$).
        custo_passeios: Custo destinado a passeios turísticos no local(R$).
        custo_alimentacao_extra: Estimativa de alimentação e passeios extras (R$).
        qtd_pessoas: Quantidade de viajantes para divisão de custos (padrão: 1).
    """
    total = (
        custo_transporte
        + custo_combustivel
        + custo_pedagios
        + custo_hospedagem
        + custo_passeios
        + custo_variaveis
        + custo_alimentacao_extra
    )
    
    por_pessoa = total / qtd_pessoas if qtd_pessoas > 0 else total
    
    relatorio_financeiro = f"""
💰 **CONSOLIDAÇÃO FINANCEIRA DA VIAGEM**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🚗 Transporte / Passagens / Locação: R$ {custo_transporte:,.2f}
⛽ Combustível: R$ {custo_combustivel:,.2f}
🛣️ Pedágios: R$ {custo_pedagios:,.2f}
🏨 Hospedagem: R$ {custo_hospedagem:,.2f}
🍔 Alimentação / Extras: R$ {custo_alimentacao_extra:,.2f}
🦺 Reserva / Imprevistos: R$ {custo_variaveis:,.2f}
🍔 Alimentação / Extras: R$ {custo_alimentacao_extra:,.2f}
────────────────────────────────────
💵 **CUSTO TOTAL:** R$ {total:,.2f}
👥 **VALOR POR PESSOA ({qtd_pessoas} pessoa(s)):** R$ {por_pessoa:,.2f}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
    return relatorio_financeiro