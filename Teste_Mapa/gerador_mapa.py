from PIL import Image, ImageDraw, ImageFont
import os
import sys
import json # Importa a biblioteca JSON

def get_script_dir():
    """Retorna o diretório do script."""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(os.path.abspath(__file__))

def gerar_mapa_de_carreira(missoes: list, mapa_base_path: str, output_path: str, coords: dict):
    """
    Gera uma imagem de mapa de carreira a partir de uma lista de missões.
    """
    try:
        img = Image.open(mapa_base_path).convert("RGB")
        draw = ImageDraw.Draw(img)
        
        try:
            font = ImageFont.truetype("arial.ttf", 20)
        except IOError:
            font = ImageFont.load_default()

        ponto_anterior = None
        
        for i, missao in enumerate(missoes):
            localidade = missao.get('locality')
            if localidade in coords:
                ponto_atual = coords[localidade]
                
                if ponto_anterior:
                    draw.line([ponto_anterior, ponto_atual], fill="yellow", width=3)
                
                raio = 6
                draw.ellipse(
                    (ponto_atual[0] - raio, ponto_atual[1] - raio, ponto_atual[0] + raio, ponto_atual[1] + raio),
                    fill="#FF0000",
                    outline="black",
                    width=2
                )
                
                draw.text((ponto_atual[0] + 12, ponto_atual[1] - 12), str(i + 1), font=font, fill="white", stroke_width=1, stroke_fill="black")

                ponto_anterior = ponto_atual

        img.save(output_path)
        print(f"[SUCESSO] Mapa de carreira salvo em: {output_path}")
        return True

    except FileNotFoundError:
        print(f"[ERRO] Não foi possível encontrar o mapa base em: {mapa_base_path}")
        return False
    except Exception as e:
        print(f"[ERRO] Ocorreu um erro inesperado ao gerar o mapa: {e}")
        return False

# ===================================================================
# PONTO DE ENTRADA DO SCRIPT DE TESTE (VERSÃO COMPLETA)
# ===================================================================
if __name__ == "__main__":
    script_dir = get_script_dir()

    # Define os caminhos para todos os arquivos necessários
    path_mapa_base = os.path.join(script_dir, "mapa_base1.jpg")
    path_mapa_final = os.path.join(script_dir, "Mapa_de_Carreira_Corrigido1.png")
    
    # --- A LINHA QUE FALTAVA ESTÁ AQUI ---
    path_coordenadas = os.path.join(script_dir, "coordenadas_mapa_final_calibrado.json")

    # Carrega o dicionário de coordenadas do arquivo JSON gerado pelo processador
    try:
        with open(path_coordenadas, 'r', encoding='utf-8') as f:
            map_coordinates = json.load(f)
        print(f"Dicionário de coordenadas carregado de '{path_coordenadas}'.")
    except FileNotFoundError:
        print(f"[ERRO] Arquivo de coordenadas '{path_coordenadas}' não encontrado.")
        print("Por favor, execute 'processador_coordenadas_v2.py' primeiro para gerá-lo.")
        sys.exit(1) # Encerra o script se não encontrar o arquivo

    # Dados de exemplo para testar o desenho no mapa
    mock_missions = [
        {'date': '01/01/1916', 'locality': 'Lille', 'duty': 'Patrulha'},
        {'date': '05/01/1916', 'locality': 'Arras', 'duty': 'Escolta'},
        {'date': '12/01/1916', 'locality': 'Cambrai', 'duty': 'Interceptação'},
        {'date': '20/01/1916', 'locality': 'Amiens', 'duty': 'Varredura'},
        {'date': '25/01/1916', 'locality': 'Reims', 'duty': 'Ataque ao Solo'},
        {'date': '03/02/1916', 'locality': 'Verdun', 'duty': 'Reconhecimento'},
        {'date': '10/02/1916', 'locality': 'Arras', 'duty': 'Patrulha'},
    ]

    # Chama a função principal para gerar o mapa
    gerar_mapa_de_carreira(
        missoes=mock_missions,
        mapa_base_path=path_mapa_base,
        output_path=path_mapa_final,
        coords=map_coordinates # Passa o dicionário carregado para a função
    )
