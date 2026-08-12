from typing import TypedDict, List

class AgenteState(TypedDict):
    #"Memória" do Agente pai para saber os valores de cada argumento
    destino_escolhido: str
    datas_viagem: str
    condicoes_mar: str
    roteiro_passeios: List[str]
    orcamento_total: float
    
    # É aqui que o histórico da conversa fica guardado
    mensagens: List[str]