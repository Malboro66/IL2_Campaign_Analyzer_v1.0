import json
import re
import numpy as np
from sklearn.linear_model import LinearRegression

def parse_mission_file(mission_path):
    waypoints = []
    with open(mission_path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()
    matches = re.findall(r"XPos = ([\d\.\-]+).*?ZPos = ([\d\.\-]+)", content, re.DOTALL)
    for x_str, z_str in matches:
        waypoints.append((float(x_str), float(z_str)))
    return waypoints

def calibrar_transformacao(mission_path, json_path, n_refs=50):
    # Carregar JSON calibrado
    with open(json_path, "r", encoding="utf-8") as f:
        map_coordinates = json.load(f)

    # Extrair waypoints
    waypoints = parse_mission_file(mission_path)[:n_refs]  # pegar alguns para calibrar

    # Dados de treino
    X_coords, px_coords, py_coords = [], [], []
    localidades = list(map_coordinates.items())

    for (XPos, ZPos) in waypoints:
        # procurar localidade mais próxima
        nearest = min(localidades, key=lambda item: (item[1][0] - XPos) ** 2 + (item[1][1] - ZPos) ** 2)
        (px, py) = nearest[1]

        X_coords.append([XPos, ZPos])
        px_coords.append(px)
        py_coords.append(py)

    # Regressão linear para px
    model_px = LinearRegression().fit(X_coords, px_coords)
    model_py = LinearRegression().fit(X_coords, py_coords)

    print("Transformação aproximada:")
    print(f"px = {model_px.coef_[0]:.6f} * XPos + {model_px.coef_[1]:.6f} * ZPos + {model_px.intercept_:.2f}")
    print(f"py = {model_py.coef_[0]:.6f} * XPos + {model_py.coef_[1]:.6f} * ZPos + {model_py.intercept_:.2f}")

    return model_px, model_py

# Exemplo de uso
if __name__ == "__main__":
    mission_path = "Alphonse Von Richter 1916-01-08.mission"
    json_path = "coordenadas_mapa_final_calibrado.json"

    model_px, model_py = calibrar_transformacao(mission_path, json_path)