import random
from datetime import datetime

def gerar_entrada_diario(missao: dict) -> str:
    """
    Recebe um dicionário de missão e retorna uma entrada de diário em formato de texto.
    """
    # --- Formatação da Data ---
    try:
        data_obj = datetime.strptime(missao['date'], '%d/%m/%Y')
        data_formatada = data_obj.strftime('%d de %B de %Y') # Ex: 01 de Janeiro de 1916
    except ValueError:
        data_formatada = missao['date']

    # --- Construção da Narrativa ---
    narrativa = f"**{data_formatada}**\n\n"
    
    # Clima e Partida
    frases_clima = [
        f"O dia começou com o tempo {missao['weather_simple'].lower()}. Partimos de {missao['airfield']} por volta das {missao['time']}.",
        f"As condições hoje eram de {missao['weather_simple'].lower()}. Decolamos de {missao['airfield']} às {missao['time']}.",
        f"Voamos sob um céu {missao['weather_simple'].lower()}. A missão começou em {missao['airfield']} às {missao['time']}."
    ]
    narrativa += random.choice(frases_clima)
    
    # Detalhes da Missão
    narrativa += f" Nossa tarefa era uma missão de '{missao['duty']}' no meu {missao['aircraft']}. "
    
    # Companheiros de Voo
    if missao['pilots']:
        # Pega até 3 companheiros para não poluir o texto
        companheiros = [p.split()[-1] for p in missao['pilots'][:3] if p != "Ltn Alphonse Von Richter"]
        if companheiros:
            nomes_companheiros = ", ".join(companheiros)
            frases_companheiros = [
                f"Tive a honra de voar ao lado de {nomes_companheiros}.",
                f"A esquadrilha era composta por mim e pelos camaradas {nomes_companheiros}.",
                f"Voaram comigo hoje os pilotos {nomes_companheiros}."
            ]
            narrativa += random.choice(frases_companheiros) + " "

    # Resultado da Missão
    if missao['result']['victories']:
        num_vitorias = len(missao['result']['victories'])
        tipo_aeronave = missao['result']['victories'][0] # Pega o primeiro tipo de abate como exemplo
        frases_vitoria = [
            f"O combate foi intenso! Consegui confirmar a destruição de {num_vitorias} aeronave(s) inimiga(s), incluindo um {tipo_aeronave}.",
            f"Hoje a sorte esteve do nosso lado. Retorno à base com {num_vitorias} vitória(s) confirmada(s), uma delas contra um {tipo_aeronave}.",
            f"Missão cumprida com sucesso. Derrubamos {num_vitorias} inimigo(s), um deles um {tipo_aeronave}."
        ]
        narrativa += "\n" + random.choice(frases_vitoria)
    elif missao['result']['status'] == 'WIA':
        frases_ferido = [
            "Infelizmente, a missão não terminou bem para mim. Fui ferido em combate, mas consegui trazer meu avião de volta.",
            "Encontramos o inimigo e acabei sendo atingido. Retornei à base ferido, mas vivo.",
            "Um dia difícil. Fui ferido durante o confronto, mas por sorte, pousei em segurança."
        ]
        narrativa += "\n" + random.choice(frases_ferido)
    else: # Missão tranquila
        frases_tranquilo = [
            "A patrulha ocorreu sem grandes incidentes e retornamos em segurança.",
            "Não encontramos atividade inimiga significativa hoje. Missão tranquila.",
            "Voamos a patrulha conforme o planejado e voltamos para a base sem contato com o inimigo."
        ]
        narrativa += random.choice(frases_tranquilo)
        
    narrativa += "\n" + ("-" * 80) + "\n"
    return narrativa

def criar_diario_completo(dados_campanha: dict) -> str:
    """
    Gera o texto completo do diário de bordo a partir dos dados da campanha.
    """
    piloto = dados_campanha['pilot']
    missoes = sorted(dados_campanha['missions'], key=lambda m: datetime.strptime(m['date'], '%d/%m/%Y'))

    # --- Cabeçalho do Diário ---
    diario = "================================================================================\n"
    diario += "                   DIÁRIO DE BORDO DE CAMPANHA\n"
    diario += "================================================================================\n\n"
    diario += f"Piloto: {piloto['name']}\n"
    diario += f"Esquadrão: {piloto['squadron']}\n"
    diario += f"Período da Campanha: {missoes[0]['date']} a {missoes[-1]['date']}\n\n"
    diario += "================================================================================\n\n"

    # --- Entradas do Diário ---
    for missao in missoes:
        diario += gerar_entrada_diario(missao)
        
    return diario

# ===================================================================
# DADOS DE EXEMPLO (MOCK DATA) - Simula o que viria do main_app.py
# ===================================================================
mock_data = {
    "pilot": {
        "name": "Ltn Alphonse Von Richter",
        "squadron": "KEK 3",
    },
    "missions": [
        {
            'date': '01/01/1916',
            'time': '11:00:00',
            'aircraft': 'Fokker E.III',
            'duty': 'Patrulha Aérea de Combate',
            'airfield': 'La Brayelle',
            'pilots': ['Ltn Alphonse Von Richter', 'Ltn Oswald Boelcke', 'Fw Rupert Altenau'],
            'weather_simple': 'Nublado com neve',
            'result': {'victories': [], 'status': 'OK'}
        },
        {
            'date': '05/01/1916',
            'time': '09:30:00',
            'aircraft': 'Fokker E.III',
            'duty': 'Escolta de Bombardeiros',
            'airfield': 'La Brayelle',
            'pilots': ['Ltn Alphonse Von Richter', 'Fw Oswald Haerig'],
            'weather_simple': 'Céu limpo',
            'result': {'victories': ['Nieuport 11'], 'status': 'OK'}
        },
        {
            'date': '12/01/1916',
            'time': '14:00:00',
            'aircraft': 'Fokker E.III',
            'duty': 'Interceptação',
            'airfield': 'La Brayelle',
            'pilots': ['Ltn Alphonse Von Richter', 'Ltn Emil Doldinger'],
            'weather_simple': 'Chuvoso',
            'result': {'victories': [], 'status': 'WIA'} # WIA = Wounded in Action
        },
        {
            'date': '20/01/1916',
            'time': '10:00:00',
            'aircraft': 'Albatros D.II', # Mudou de aeronave
            'duty': 'Varredura Ofensiva',
            'airfield': 'La Brayelle',
            'pilots': ['Ltn Alphonse Von Richter', 'Ltn Heiner Wehausen'],
            'weather_simple': 'Céu limpo',
            'result': {'victories': ['F.E.2b', 'Sopwith Pup'], 'status': 'OK'}
        }
    ]
}

# ===================================================================
# PONTO DE ENTRADA DO SCRIPT DE TESTE
# ===================================================================
if __name__ == "__main__":
    # 1. Gera o diário completo a partir dos dados de exemplo
    diario_final = criar_diario_completo(mock_data)
    
    # 2. Imprime o resultado no terminal
    print(diario_final)
    
    # 3. Salva o resultado em um arquivo de texto
    nome_piloto_arquivo = mock_data['pilot']['name'].replace(" ", "_")
    nome_arquivo = f"Diario_de_Bordo_{nome_piloto_arquivo}.txt"
    
    try:
        with open(nome_arquivo, "w", encoding="utf-8") as f:
            f.write(diario_final)
        print(f"\n[SUCESSO] Diário de bordo salvo em: {nome_arquivo}")
    except IOError as e:
        print(f"\n[ERRO] Não foi possível salvar o arquivo: {e}")

