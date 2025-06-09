import json
from typing import Dict, Any, List
from core.models import LoteResultante, Terreno
from core.subdivision_logic import get_subdivision_algorithm
from core.serializers import LoteResultanteSerializer

def perform_terreno_subdivision(terreno: Terreno, num_lots: int, method: str) -> Dict[str, Any]:
    """
    Ejecuta la subdivisión de un terreno usando el algoritmo seleccionado.

    Args:
        terreno (Terreno): Instancia del terreno a subdividir.
        num_lots (int): Número deseado de lotes resultantes.
        method (str): Nombre del algoritmo o método de subdivisión.

    Returns:
        dict: Contiene mensaje de resultado y la lista de lotes creados (serializados).
    """
    try:
        # Obtener algoritmo de subdivisión basado en el método indicado
        subdivision_algorithm = get_subdivision_algorithm(method)
        if subdivision_algorithm is None:
            return {'message': f'Algoritmo "{method}" no disponible.', 'lotes_creados': []}

        # Ejecutar el algoritmo, debería retornar lista de geometrías GeoJSON y atributos
        lotes_geojson = subdivision_algorithm(terreno.geometria_geojson, num_lots)

        # Eliminar lotes anteriores asociados a este terreno (opcional, según lógica de negocio)
        terreno.lotes_resultantes.all().delete()

        lotes_creados = []
        for idx, geojson in enumerate(lotes_geojson, start=1):
            lote = LoteResultante.objects.create(
                terreno=terreno,
                numero_lote=str(idx),
                geometria_lote_geojson=json.dumps(geojson),
                # Aquí puedes calcular o asignar área_lote y frente_lote si tu algoritmo lo provee
            )
            lotes_creados.append(lote)

        # Serializar para retorno (puede ser útil para respuesta API)
        serializer = LoteResultanteSerializer(lotes_creados, many=True)

        return {
            'message': f'Subdivisión completada con {len(lotes_creados)} lotes creados.',
            'lotes_creados': serializer.data
        }

    except Exception as e:
        return {
            'message': f'Error durante la subdivisión: {str(e)}',
            'lotes_creados': []
        }
