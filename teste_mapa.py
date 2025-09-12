import json
import re
import math
from PIL import Image, ImageDraw, ImageFont

# ===============================
# Classe WaypointMapper (mesma lógica do main_app.py)
# ===============================
class WaypointMapper:
    def __init__(self, map_coordinates):
        self.map_coordinates = map_coordinates

    def find_nearest_locality(self, x, z):
        """Encontra localidade mais próxima no JSON calibrado"""
        nearest = None
        min_dist = float("inf")
        for locality, (px, py) in self.map_coordinates.items():
            dist = math.dist((x, z), (px, py))
            if dist < min_dist:
                nearest = (locality, (px, py))
                min_dist = dist
        return nearest

# ===============================
# Função para extrair XPos/ZPos do .mission
# ===============================
def parse_mission_file(mission_path):
    waypoints = []
    with open(mission_path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    matches = re.findall(r"XPos = ([\d\.\-]+).*?ZPos = ([\d\.\-]+)", content, re.DOTALL)
    for x_str, z_str in matches:
        x, z = float(x_str), float(z_str)
        waypoints.append((x, z))
    return waypoints

# ===============================
# Função principal de teste
# ===============================
def gerar_mapa_teste(json_path, mission_path, base_map_path, output_path="mapa_teste.png"):
    # Carregar JSON calibrado
    with open(json_path, "r", encoding="utf-8") as f:
        map_coordinates = json.load(f)

    # Extrair waypoints
    waypoints = parse_mission_file(mission_path)
    print(f"Total de waypoints extraídos: {len(waypoints)}")

    # Criar mapper
    mapper = WaypointMapper(map_coordinates)

    # Abrir mapa base
    img = Image.open(base_map_path).convert("RGB")
    draw = ImageDraw.Draw(img)
    fonte = ImageFont.load_default()
    r = 5

    # Processar cada waypoint
    for (x, z) in waypoints[:50]:  # limitar aos primeiros 50 p/ teste
        localidade, (px, py) = mapper.find_nearest_locality(x, z)
        draw.ellipse((px - r, py - r, px + r, py + r), fill="red")
        draw.text((px + 5, py - 5), localidade, fill="white", font=fonte)

    # Salvar saída
    img.save(output_path)
    print(f"Mapa gerado: {output_path}")

# ===============================
# Execução de teste
# ===============================
if __name__ == "__main__":
    gerar_mapa_teste(
        json_path="coordenadas_mapa_final_calibrado.json",
        mission_path="Alphonse Von Richter 1916-01-08.mission",
        base_map_path="mapa_base.jpg",
        output_path="mapa_teste.png"
    )
