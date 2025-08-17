import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import os
import sys

def get_script_dir():
    """Retorna o diretório do script, funcionando tanto para .py quanto para executável."""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(os.path.abspath(__file__))

def on_map_click(event):
    """Função chamada quando o usuário clica no mapa."""
    # As coordenadas do evento são relativas à área visível do canvas.
    # Precisamos adicionar a posição da barra de rolagem para obter as coordenadas reais da imagem.
    x = canvas.canvasx(event.x)
    y = canvas.canvasy(event.y)
    
    # Copia a coordenada para a área de transferência (clipboard)
    root.clipboard_clear()
    root.clipboard_append(f"({int(x)}, {int(y)}),")
    
    # Atualiza a label na tela
    info_label.config(text=f"Coordenada ({int(x)}, {int(y)}) copiada para a área de transferência!")
    print(f"Clique em: ({int(x)}, {int(y)})")

# --- Ponto de Entrada do Calibrador ---
if __name__ == "__main__":
    script_directory = get_script_dir()
    map_path = os.path.join(script_directory, "mapa_base1.jpg")

    if not os.path.exists(map_path):
        messagebox.showerror("Erro", f"Arquivo 'mapa_base.jpg' não encontrado no diretório:\n{script_directory}")
    else:
        root = tk.Tk()
        root.title("Calibrador de Mapa - Clique em uma cidade")

        # Cria um frame principal para conter o canvas e as barras de rolagem
        main_frame = tk.Frame(root)
        main_frame.pack(fill=tk.BOTH, expand=1)

        # Cria as barras de rolagem
        hbar = tk.Scrollbar(main_frame, orient=tk.HORIZONTAL)
        vbar = tk.Scrollbar(main_frame, orient=tk.VERTICAL)

        # Carrega a imagem
        pil_image = Image.open(map_path)
        tk_image = ImageTk.PhotoImage(pil_image)

        # Cria um canvas (área de desenho) com o tamanho da imagem
        canvas = tk.Canvas(main_frame, width=pil_image.width, height=pil_image.height,
                           xscrollcommand=hbar.set, yscrollcommand=vbar.set)
        
        hbar.config(command=canvas.xview)
        vbar.config(command=canvas.yview)

        # Empacota as barras de rolagem e o canvas
        hbar.pack(side=tk.BOTTOM, fill=tk.X)
        vbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Adiciona a imagem ao canvas
        canvas.create_image(0, 0, anchor=tk.NW, image=tk_image)

        # Configura a região de rolagem do canvas para ser do tamanho da imagem
        canvas.config(scrollregion=canvas.bbox(tk.ALL))

        # Associa o evento de clique à nossa função
        canvas.bind("<Button-1>", on_map_click)

        # Adiciona uma label para dar feedback ao usuário
        info_label = tk.Label(root, text="Use as barras de rolagem para navegar. Clique em um local para obter suas coordenadas.", font=("Arial", 12))
        info_label.pack(pady=10)

        # Inicia a janela
        root.mainloop()
