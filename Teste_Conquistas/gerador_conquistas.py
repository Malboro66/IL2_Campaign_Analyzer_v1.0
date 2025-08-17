# ===================================================================
# MÓDULO DE LÓGICA DE CONQUISTAS
# ===================================================================

def check_primeiro_abate(dados_piloto, dados_missoes):
    """Verifica se o piloto tem pelo menos um abate."""
    return dados_piloto.get('victories', 0) > 0

def check_as_em_um_dia(dados_piloto, dados_missoes):
    """Verifica se o piloto conseguiu 5 ou mais abates em um único dia."""
    abates_por_dia = {}
    for missao in dados_missoes:
        data = missao['date']
        vitorias_na_missao = len(missao.get('result', {}).get('victories', []))
        abates_por_dia[data] = abates_por_dia.get(data, 0) + vitorias_na_missao
    
    return any(abates >= 5 for abates in abates_por_dia.values())

def check_veterano_de_guerra(dados_piloto, dados_missoes):
    """Verifica se o piloto voou mais de 50 missões."""
    return dados_piloto.get('missions_flown', 0) >= 50

def check_polivalente(dados_piloto, dados_missoes):
    """Verifica se o piloto voou em 3 ou mais tipos de aeronaves diferentes."""
    tipos_aeronaves = set()
    for missao in dados_missoes:
        tipos_aeronaves.add(missao['aircraft'])
    return len(tipos_aeronaves) >= 3

def check_sobrevivente(dados_piloto, dados_missoes):
    """Verifica se o piloto foi ferido em combate (WIA) e sobreviveu."""
    for missao in dados_missoes:
        if missao.get('result', {}).get('status') == 'WIA':
            return True
    return False

# ===================================================================
# DICIONÁRIO DE CONQUISTAS
# ===================================================================
# A "base de dados" de todas as conquistas possíveis no programa.
# A chave é um ID único, e o valor é um dicionário com os detalhes.

CONQUISTAS_DEFINIDAS = {
    "PRIMEIRO_ABATE": {
        "nome": "Batismo de Fogo",
        "descricao": "Consiga seu primeiro abate aéreo confirmado.",
        "icone": "icon_primeiro_abate.png",
        "condicao": check_primeiro_abate
    },
    "AS_EM_UM_DIA": {
        "nome": "Ás em um Dia",
        "descricao": "Derrube 5 ou mais aeronaves inimigas em um único dia.",
        "icone": "icon_as_em_um_dia.png",
        "condicao": check_as_em_um_dia
    },
    "VETERANO_50_MISSOES": {
        "nome": "Veterano de Guerra",
        "descricao": "Complete 50 missões de combate.",
        "icone": "icon_veterano.png",
        "condicao": check_veterano_de_guerra
    },
    "POLIVALENTE": {
        "nome": "Piloto Polivalente",
        "descricao": "Voe em pelo menos 3 tipos diferentes de aeronaves em missões de combate.",
        "icone": "icon_polivalente.png",
        "condicao": check_polivalente
    },
    "SOBREVIVENTE": {
        "nome": "Coração Púrpura",
        "descricao": "Seja ferido em combate e retorne à base para lutar outro dia.",
        "icone": "icon_sobrevivente.png",
        "condicao": check_sobrevivente
    }
}

# ===================================================================
# PROCESSADOR DE CONQUISTAS
# ===================================================================

def processar_conquistas_do_piloto(dados_piloto, dados_missoes):
    """
    Verifica todas as conquistas definidas e retorna uma lista daquelas que o piloto desbloqueou.
    """
    conquistas_desbloqueadas = []
    for id_conquista, detalhes_conquista in CONQUISTAS_DEFINIDAS.items():
        # Chama a função de condição associada a esta conquista
        if detalhes_conquista["condicao"](dados_piloto, dados_missoes):
            conquistas_desbloqueadas.append(detalhes_conquista)
            
    return conquistas_desbloqueadas

# ===================================================================
# DADOS DE EXEMPLO (MOCK DATA) PARA TESTE
# ===================================================================
mock_pilot_data = {
    "name": "Ltn Alphonse Von Richter",
    "missions_flown": 52, # Ativa a conquista de veterano
    "victories": 8,       # Ativa a conquista de primeiro abate
}

mock_missions_data = [
    # Missões que, somadas, darão 5 abates no dia 20/01/1916
    {'date': '01/01/1916', 'aircraft': 'Fokker E.III', 'result': {'victories': ['Sopwith Pup']}},
    {'date': '12/01/1916', 'aircraft': 'Fokker E.III', 'result': {'status': 'WIA'}}, # Ativa a de sobrevivente
    {'date': '20/01/1916', 'aircraft': 'Albatros D.II', 'result': {'victories': ['F.E.2b', 'Sopwith Pup']}},
    {'date': '20/01/1916', 'aircraft': 'Albatros D.II', 'result': {'victories': ['SPAD VII', 'Nieuport 17', 'Breguet 14']}}, # 3 abates aqui
    # Missão com terceira aeronave para ativar a conquista de polivalente
    {'date': '25/02/1916', 'aircraft': 'Halberstadt D.II', 'result': {}},
]

# Adiciona mais 47 missões genéricas para totalizar 52
for i in range(47):
    mock_missions_data.append({'date': '01/03/1916', 'aircraft': 'Albatros D.II', 'result': {}})


# ===================================================================
# PONTO DE ENTRADA DO SCRIPT DE TESTE
# ===================================================================
if __name__ == "__main__":
    print("Analisando perfil do piloto para conquistas...\n")
    
    # Chama a função principal para obter a lista de conquistas
    conquistas_obtidas = processar_conquistas_do_piloto(mock_pilot_data, mock_missions_data)
    
    if not conquistas_obtidas:
        print("Nenhuma conquista desbloqueada ainda. Continue voando!")
    else:
        print(f"--- CONQUISTAS DESBLOQUEADAS ({len(conquistas_obtidas)}) ---\n")
        for conquista in conquistas_obtidas:
            print(f"🏆 {conquista['nome']}")
            print(f"   Descrição: {conquista['descricao']}\n")
            
    print("\nAnálise concluída.")
