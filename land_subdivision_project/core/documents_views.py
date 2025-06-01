# core/documents_views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, HttpResponseServerError
from django.contrib.auth.decorators import login_required

# Importaciones absolutas desde core/
from core.models import Proyecto, Terreno
from core.forms import SubirArchivoTerrenoForm

# Importaciones de utilidades (matplotlib y io no son vistas, así que las sacamos a un archivo de utilidades)
import csv
import json
import io
import matplotlib.pyplot as plt # Mantener aquí o mover a plotting_utils.py

# Si decides mover la lógica de graficación a 'plotting_utils.py', la importación sería:
# from core.plotting_utils import generate_terreno_plot

@login_required
def subir_terreno_view(request):
    mensaje = None
    if request.method == 'POST':
        form = SubirArchivoTerrenoForm(request.POST, request.FILES)
        if form.is_valid():
            nombre = form.cleaned_data['nombre']
            archivo_puntos = form.cleaned_data['archivo_puntos']

            vertices = []
            try:
                decoded_file = archivo_puntos.read().decode('utf-8').splitlines()
                reader = csv.reader(decoded_file)
                for i, row in enumerate(reader):
                    if len(row) == 2:
                        try:
                            lat = float(row[0].strip())
                            lon = float(row[1].strip())
                            vertices.append([lat, lon])
                        except ValueError:
                            mensaje = f"Error en la línea {i+1}: Las coordenadas deben ser números. Formato esperado: latitud,longitud"
                            vertices = []
                            break
                    else:
                        mensaje = f"Error en la línea {i+1}: Cada línea debe tener exactamente dos valores (latitud, longitud) separados por coma."
                        vertices = []
                        break

                if vertices:
                    geojson_coords_raw = [[lon, lat] for lat, lon in vertices]
                    if geojson_coords_raw[0] != geojson_coords_raw[-1]:
                        geojson_coords_raw.append(geojson_coords_raw[0])

                    geojson_geometry = {
                        "type": "Polygon",
                        "coordinates": [geojson_coords_raw]
                    }

                    proyecto_del_usuario = request.user.proyecto_set.first()
                    if not proyecto_del_usuario:
                        proyecto_del_usuario = Proyecto.objects.create(
                            usuario=request.user,
                            nombre_proyecto=f"Proyecto por defecto de {request.user.username}"
                        )

                    Terreno.objects.create(
                        proyecto=proyecto_del_usuario,
                        nombre_terreno=nombre,
                        geometria_geojson=json.dumps(geojson_geometry),
                    )
                    mensaje = f"Terreno '{nombre}' subido y guardado exitosamente."
                    # Asegúrate que 'subir_terreno' es el nombre de la URL
                    return redirect('subir_terreno')
                elif not mensaje:
                    mensaje = "Error: El archivo de puntos está vacío o no contiene datos válidos."

            except Exception as e:
                mensaje = f"Error inesperado al procesar el archivo: {e}"
        else:
            mensaje = "Error de validación en el formulario. Por favor, verifica los campos."
    else:
        form = SubirArchivoTerrenoForm()

    terrenos = Terreno.objects.filter(proyecto__usuario=request.user).order_by('-fecha_registro')
    return render(request, 'core/documentos/subir_documento.html', {
        'form': form,
        'mensaje': mensaje,
        'terrenos': terrenos
    })

@login_required
def mostrar_grafico_terreno(request, terreno_id):
    terreno = get_object_or_404(Terreno, pk=terreno_id, proyecto__usuario=request.user)
    vertices_para_dibujar = terreno.get_vertices_from_geojson()

    try:
        if not vertices_para_dibujar or len(vertices_para_dibujar) < 2:
            return HttpResponseServerError("No hay suficientes vértices válidos para dibujar un gráfico.")

        latitudes = [v[0] for v in vertices_para_dibujar]
        longitudes = [v[1] for v in vertices_para_dibujar]

        plt.figure(figsize=(8, 6))
        plt.plot(longitudes, latitudes, marker='o', linestyle='-', color='blue')
        plt.fill(longitudes, latitudes, color='lightblue', alpha=0.5)
        plt.title(f"Gráfico del Terreno: {terreno.nombre_terreno}")
        plt.xlabel("Longitud")
        plt.ylabel("Latitud")
        plt.grid(True)
        plt.gca().set_aspect('equal', adjustable='box')

        for i, (lat, lon) in enumerate(vertices_para_dibujar):
            plt.annotate(f'({i+1})', (lon, lat), textcoords="offset points", xytext=(5,-5), ha='center', fontsize=9)

        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', bbox_inches='tight')
        buffer.seek(0)
        plt.close()

        return HttpResponse(buffer.getvalue(), content_type='image/png')

    except Exception as e:
        print(f"Error al generar el gráfico para el terreno {terreno.id}: {e}")
        return HttpResponseServerError(f"Error interno al generar el gráfico: {e}")