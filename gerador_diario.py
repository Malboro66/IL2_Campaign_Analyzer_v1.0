import random
from datetime import datetime
from typing import Dict, List, Optional

PT_MONTHS = {
    1: "janeiro", 2: "fevereiro", 3: "março", 4: "abril",
    5: "maio", 6: "junho", 7: "julho", 8: "agosto",
    9: "setembro", 10: "outubro", 11: "novembro", 12: "dezembro"
}


def format_date_pt(date_str: str) -> str:
    """Tenta formatar 'DD/MM/YYYY' para 'DD de <mês> de YYYY' em português."""
    try:
        d = datetime.strptime(date_str, "%d/%m/%Y")
        month = PT_MONTHS.get(d.month, d.strftime("%B"))
        return f"{d.day:02d} de {month} de {d.year}"
    except Exception:
        return date_str


def format_time_short(time_str: str) -> str:
    """Converte 'HH:MM:SS' para 'HH:MM' quando possível."""
    try:
        t = datetime.strptime(time_str, "%H:%M:%S")
        return t.strftime("%H:%M")
    except Exception:
        # Se já estiver em HH:MM ou outro formato, retorna como veio
        return time_str


def _last_names(pilots: List[str], main_pilot: Optional[str]) -> List[str]:
    """Retorna até 3 sobrenomes dos companheiros, excluindo o piloto principal quando possível."""
    cleaned = []
    for p in pilots:
        if not p:
            continue
        if main_pilot and p.strip().lower() == main_pilot.strip().lower():
            continue
        parts = p.strip().split()
        cleaned.append(parts[-1])
        if len(cleaned) >= 3:
            break
    return cleaned


def gerar_entrada_diario(missao: Dict, main_pilot: Optional[str] = None) -> str:
    """
    Recebe um dicionário de missão e retorna uma entrada de diário em formato de texto.
    Mais robusto a campos ausentes e formata datas/horas em PT.
    """
    # Campos com valores padrão para evitar KeyError
    date_raw = missao.get("date", "Unknown")
    time_raw = missao.get("time", "")
    airfield = missao.get("airfield", "base desconhecida")
    weather = missao.get("weather_simple", "clima desconhecido").lower()
    duty = missao.get("duty", "missão desconhecida")
    aircraft = missao.get("aircraft", "aeronave desconhecida")
    pilots = missao.get("pilots", [])
    result = missao.get("result", {})

    data_formatada = format_date_pt(date_raw)
    hora_formatada = format_time_short(time_raw)

    narrativa = f"{data_formatada}\n\n"

    frases_clima = [
        f"O dia começou com o tempo {weather}. Partimos de {airfield} por volta das {hora_formatada}.",
        f"As condições hoje eram de {weather}. Decolamos de {airfield} às {hora_formatada}.",
        f"Voamos sob um céu {weather}. A missão começou em {airfield} às {hora_formatada}."
    ]
    narrativa += random.choice(frases_clima)

    narrativa += f" Nossa tarefa era uma missão de '{duty}' no meu {aircraft}. "

    companheiros = _last_names(pilots, main_pilot)
    if companheiros:
        nomes_companheiros = ", ".join(companheiros)
        frases_companheiros = [
            f"Tive a honra de voar ao lado de {nomes_companheiros}.",
            f"A esquadrilha era composta por mim e pelos camaradas {nomes_companheiros}.",
            f"Voaram comigo hoje os pilotos {nomes_companheiros}."
        ]
        narrativa += " " + random.choice(frases_companheiros)

    # Resultado da missão
    victories = result.get("victories", []) or []
    status = result.get("status", "").upper()

    if victories:
        num_vitorias = len(victories)
        tipo_aeronave = str(victories[0])
        aeronave_word = "aeronave" if num_vitorias == 1 else "aeronaves"
        frases_vitoria = [
            f"\nO combate foi intenso! Consegui confirmar a destruição de {num_vitorias} {aeronave_word} inimiga(s), incluindo um {tipo_aeronave}.",
            f"\nHoje a sorte esteve do nosso lado. Retorno à base com {num_vitorias} vitória(s) confirmada(s), uma delas contra um {tipo_aeronave}.",
            f"\nMissão cumprida com sucesso. Derrubamos {num_vitorias} inimigo(s), um deles um {tipo_aeronave}."
        ]
        narrativa += random.choice(frases_vitoria)
    elif status == "WIA":
        frases_ferido = [
            "\nInfelizmente, a missão não terminou bem para mim. Fui ferido em combate, mas consegui trazer meu avião de volta.",
            "\nEncontramos o inimigo e acabei sendo atingido. Retornei à base ferido, mas vivo.",
            "\nUm dia difícil. Fui ferido durante o confronto, mas por sorte, pousei em segurança."
        ]
        narrativa += random.choice(frases_ferido)
    else:
        frases_tranquilo = [
            "\nA patrulha ocorreu sem grandes incidentes e retornamos em segurança.",
            "\nNão encontramos atividade inimiga significativa hoje. Missão tranquila.",
            "\nVoamos a patrulha conforme o planejado e voltamos para a base sem contato com o inimigo."
        ]
        narrativa += random.choice(frases_tranquilo)

    narrativa += "\n" + ("-" * 80) + "\n"
    return narrativa


def criar_diario_completo(dados_campanha: Dict) -> str:
    """
    Gera o texto completo do diário de bordo a partir dos dados da campanha.
    Ordena missões por data quando possível e passa o nome do piloto principal
    para evitar listá-lo entre os companheiros.
    """
    piloto = dados_campanha.get("pilot", {})
    pilot_name = piloto.get("name", "Piloto Desconhecido")
    missoes = dados_campanha.get("missions", [])

    def mission_sort_key(m):
        try:
            return datetime.strptime(m.get("date", ""), "%d/%m/%Y")
        except Exception:
            return datetime.max

    missoes = sorted(missoes, key=mission_sort_key)

    diario = "=" * 80 + "\n"
    diario += "                   DIÁRIO DE BORDO DE CAMPANHA\n"
    diario += "=" * 80 + "\n\n"
    diario += f"Piloto: {pilot_name}\n"
    diario += f"Esquadrão: {piloto.get('squadron', 'N/A')}\n"
    if missoes:
        diario += f"Período da Campanha: {missoes[0].get('date', '?')} a {missoes[-1].get('date', '?')}\n\n"
    else:
        diario += "Período da Campanha: N/A\n\n"
    diario += "=" * 80 + "\n\n"

    for missao in missoes:
        diario += gerar_entrada_diario(missao, main_pilot=pilot_name)

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
            'result': {'victories': [], 'status': 'WIA'}  # WIA = Wounded in Action
        },
        {
            'date': '20/01/1916',
            'time': '10:00:00',
            'aircraft': 'Albatros D.II',  # Mudou de aeronave
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
    diario_final = criar_diario_completo(mock_data)
    print(diario_final)

    nome_piloto_arquivo = mock_data['pilot']['name'].replace(" ", "_")
    nome_arquivo = f"Diario_de_Bordo_{nome_piloto_arquivo}.txt"

    try:
        with open(nome_arquivo, "w", encoding="utf-8") as f:
            f.write(diario_final)
        print(f"\n[SUCESSO] Diário de bordo salvo em: {nome_arquivo}")
    except IOError as e:
        print(f"\n[ERRO] Não foi possível salvar o arquivo: {e}")
