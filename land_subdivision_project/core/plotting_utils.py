# core/plotting_utils.py
import io
import matplotlib.pyplot as plt
from typing import List, Tuple

def generate_terreno_plot(vertices: List[Tuple[float, float]], name: str) -> io.BytesIO:
    """
    Genera un gráfico del terreno a partir de una lista de vértices (x, y).
    Devuelve un objeto BytesIO con la imagen PNG del gráfico.
    
    Args:
        vertices (List[Tuple[float, float]]): Lista de coordenadas (x, y) del terreno, en orden.
        name (str): Nombre del terreno para poner en el título del gráfico.
    
    Returns:
        io.BytesIO: Imagen PNG del gráfico en memoria.
    """
    if not vertices or len(vertices) < 3:
        raise ValueError("Se necesitan al menos 3 vértices para graficar un terreno.")

    # Separa las listas de X y Y
    x_coords, y_coords = zip(*vertices)

    # Para cerrar el polígono, repetimos el primer punto al final
    x_coords = list(x_coords) + [x_coords[0]]
    y_coords = list(y_coords) + [y_coords[0]]

    plt.figure(figsize=(6,6))
    plt.plot(x_coords, y_coords, 'b-', marker='o')  # Línea azul con puntos
    plt.fill(x_coords, y_coords, 'skyblue', alpha=0.4)  # Relleno semitransparente
    plt.title(f"Terreno: {name}")
    plt.xlabel("Coordenada X")
    plt.ylabel("Coordenada Y")
    plt.grid(True)
    plt.axis('equal')  # Para mantener la proporción en ambos ejes

    # Guardar la figura en un buffer de memoria
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    plt.close()
    buf.seek(0)  # Volver al inicio del buffer para lectura
    
    return buf
