import json
import os
import sys

def get_script_dir():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(os.path.abspath(__file__))

# ===================================================================
# PONTOS DE CALIBRAÇÃO - PREENCHA COM SEUS DADOS!
# ===================================================================
# Use 4 pontos nos cantos do mapa para obter a melhor precisão.
# Substitua os valores de "pixel" pelos que você obteve no calibrador.
PONTOS_DE_CALIBRACAO = {
    # Ponto 1: Canto Superior Esquerdo (Ex: Ypres)
    "p1": {
        "jogo": {"x": 304498.0, "z": 100281.0},
        "pixel": {"x": 1460, "y": 593} 
    },
    # Ponto 2: Canto Superior Direito (Ex: Thionville)
    "p2": {
        "jogo": {"x": 139619.0, "z": 337979.0},
        "pixel": {"x": 4894, "y": 2984}
    },
    # Ponto 3: Canto Inferior Esquerdo (Ex: Beauvais)
    "p3": {
        "jogo": {"x": 148209.0, "z": 40681.0},
        "pixel": {"x": 594, "y": 2871}
    },
}

def calcular_transformacao_afim(pontos):
    """
    Calcula os 6 parâmetros de uma transformação afim (escala, rotação, deslocamento)
    usando 3 pontos de referência.
    """
    # --- VERSÃO LIMPA SEM VARIÁVEIS NÃO UTILIZADAS ---

    # Calcular escala e offset para o eixo X do pixel (baseado no Z do jogo)
    # Fórmula: pixel_x = A * jogo_z + B
    delta_z_jogo = pontos['p2']['jogo']['z'] - pontos['p1']['jogo']['z']
    delta_x_pixel = pontos['p2']['pixel']['x'] - pontos['p1']['pixel']['x']
    
    # Evita divisão por zero se os pontos forem os mesmos
    if delta_z_jogo == 0:
        raise ValueError("Pontos de calibração p1 e p2 não podem ter a mesma coordenada Z no jogo.")
    
    A = delta_x_pixel / delta_z_jogo
    B = pontos['p1']['pixel']['x'] - A * pontos['p1']['jogo']['z']

    # Calcular escala e offset para o eixo Y do pixel (baseado no X do jogo)
    # Fórmula: pixel_y = C * jogo_x + D
    delta_x_jogo = pontos['p3']['jogo']['x'] - pontos['p1']['jogo']['x']
    delta_y_pixel = pontos['p3']['pixel']['y'] - pontos['p1']['pixel']['y']

    # Evita divisão por zero se os pontos forem os mesmos
    if delta_x_jogo == 0:
        raise ValueError("Pontos de calibração p1 e p3 não podem ter a mesma coordenada X no jogo.")

    C = delta_y_pixel / delta_x_jogo
    D = pontos['p1']['pixel']['y'] - C * pontos['p1']['jogo']['x']
    
    print("--- Parâmetros de Transformação Corrigidos ---")
    print(f"A (escala z->x): {A}")
    print(f"B (offset x): {B}")
    print(f"C (escala x->y): {C}")
    print(f"D (offset y): {D}\n")
    
    return A, B, C, D

def processar_com_transformacao(json_path, params):
    """Converte todas as localizações usando os parâmetros de transformação calculados."""
    A, B, C, D = params
    
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    locations = data['locations']
    
    map_coordinates = {}
    for loc in locations:
        jogo_x = loc['position']['xPos']
        jogo_z = loc['position']['zPos']
        
        # Aplica a fórmula de transformação afim
        pixel_x = int(A * jogo_z + B)
        pixel_y = int(C * jogo_x + D)
        
        map_coordinates[loc['name']] = (pixel_x, pixel_y)
        
    return map_coordinates

# ===================================================================
# PONTO DE ENTRADA DO SCRIPT
# ===================================================================
if __name__ == "__main__":
    script_dir = get_script_dir()
    path_json = os.path.join(script_dir, "MapLocations.json")

    # 1. Calcula os parâmetros de transformação
    parametros_finais = calcular_transformacao_afim(PONTOS_DE_CALIBRACAO)
    
    # 2. Processa todas as localizações com esses parâmetros
    coordenadas_finais = processar_com_transformacao(path_json, parametros_finais)

    if coordenadas_finais:
        output_dict_path = os.path.join(script_dir, "coordenadas_mapa_final_calibrado.json")
        with open(output_dict_path, 'w', encoding='utf-8') as f:
            json.dump(coordenadas_finais, f, indent=2)
        
        print(f"[SUCESSO] Dicionário de coordenadas final salvo em: {output_dict_path}")
        print("Use este arquivo no seu 'gerador_mapa.py'.")

