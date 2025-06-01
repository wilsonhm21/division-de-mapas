# core/api_views.py

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from django.http import JsonResponse

# Importaciones absolutas desde core/
from core.models import Proyecto, Terreno, ParametrosSubdivision, LoteResultante
from core.serializers import (ProyectoSerializer, TerrenoSerializer,
                              ParametrosSubdivisionSerializer, LoteResultanteSerializer)
from core.subdivision_logic import get_subdivision_algorithm # Importación de tu lógica de subdivisión
# Si moviste la lógica de subdivisión a un 'services.py', sería:
# from core.services import perform_terreno_subdivision

import json # Necesario para manejar GeoJSON

class ProyectoViewSet(viewsets.ModelViewSet):
    queryset = Proyecto.objects.all()
    serializer_class = ProyectoSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(usuario=self.request.user)

    def perform_create(self, serializer):
        serializer.save(usuario=self.request.user)

class TerrenoViewSet(viewsets.ModelViewSet):
    queryset = Terreno.objects.all()
    serializer_class = TerrenoSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(proyecto__usuario=self.request.user)

    def perform_create(self, serializer):
        proyecto_id = self.request.data.get('proyecto')
        if not proyecto_id:
            raise ValidationError({'proyecto': 'El ID del proyecto es requerido para crear un terreno.'})
        try:
            proyecto = Proyecto.objects.get(pk=proyecto_id, usuario=self.request.user)
            serializer.save(proyecto=proyecto)
        except Proyecto.DoesNotExist:
            raise ValidationError({'proyecto': 'Proyecto no encontrado o no pertenece al usuario.'})

    @action(detail=True, methods=["post"], url_path="subdivide")
    def subdivide_terreno(self, request, pk=None):
        terreno = self.get_object()
        num_lots = request.data.get("num_lots", 2)
        method = request.data.get("method", "line")

        try:
            num_lots = int(num_lots)
            if num_lots <= 0:
                return Response({"error": "Number of lots must be a positive integer."}, status=status.HTTP_400_BAD_REQUEST)
        except ValueError:
            return Response({"error": "Invalid number of lots provided."}, status=status.HTTP_400_BAD_REQUEST)

        if not terreno.geometria_geojson:
            return Response({"error": "Terreno has no geometry to subdivide."}, status=status.HTTP_400_BAD_REQUEST)

        # Aquí es donde podrías llamar a una función en services.py si decides mover esa lógica
        subdivision_algorithm = get_subdivision_algorithm(method)
        if not subdivision_algorithm:
            return Response({"error": f"Método de subdivisión '{method}' no válido."}, status=status.HTTP_400_BAD_REQUEST)

        subdivision_result = subdivision_algorithm(terreno.geometria_geojson, num_lots)

        if "error" in subdivision_result:
            return Response(subdivision_result, status=status.HTTP_400_BAD_REQUEST)

        lotes_creados = []
        for i, lote_geom_data in enumerate(subdivision_result.get('lotes', [])):
            lote_num = f"{terreno.nombre_terreno}-{i+1}"
            lote_obj = LoteResultante.objects.create(
                terreno=terreno,
                numero_lote=lote_num,
                geometria_lote_geojson=json.dumps(lote_geom_data)
            )
            lotes_creados.append(LoteResultanteSerializer(lote_obj).data)

        return Response({"message": "Terreno subdividido exitosamente", "lotes_creados": lotes_creados}, status=status.HTTP_200_OK)

    @action(detail=True, methods=["get"], url_path="export")
    def export_terreno_geojson(self, request, pk=None):
        terreno = self.get_object()
        features = []

        try:
            original_geom_data = json.loads(terreno.geometria_geojson)
            geometry_to_add = original_geom_data["geometry"] if original_geom_data.get("type") == "Feature" else original_geom_data

            features.append({
                "type": "Feature",
                "geometry": geometry_to_add,
                "properties": {
                    "id": terreno.id,
                    "nombre": terreno.nombre_terreno,
                    "tipo": "terreno_original"
                }
            })
        except json.JSONDecodeError:
            print(f"Error al decodificar GeoJSON para terreno {terreno.id}: {terreno.geometria_geojson[:50]}...")
            pass
        except Exception as e:
            print(f"Error general al procesar GeoJSON original para exportación: {e}")
            pass

        lotes_guardados = LoteResultante.objects.filter(terreno=terreno)
        for lote in lotes_guardados:
            try:
                lote_geom_data = json.loads(lote.geometria_lote_geojson)
                features.append({
                    "type": "Feature",
                    "geometry": lote_geom_data,
                    "properties": {
                        "id_lote": lote.id,
                        "numero_lote": lote.numero_lote,
                        "area_m2": lote.area_lote,
                        "frente_m": lote.frente_lote,
                        "tipo": "lote_subdividido"
                    }
                })
            except json.JSONDecodeError:
                print(f"Error al decodificar GeoJSON para lote resultante {lote.id}: {lote.geometria_lote_geojson[:50]}...")
                pass
            except Exception as e:
                print(f"Error general al procesar GeoJSON de lote resultante para exportación: {e}")
                pass

        feature_collection = {
            "type": "FeatureCollection",
            "features": features
        }

        response = JsonResponse(feature_collection)
        response["Content-Disposition"] = f"attachment; filename=terreno_{terreno.id}_export.geojson"
        return response

class ParametrosSubdivisionViewSet(viewsets.ModelViewSet):
    queryset = ParametrosSubdivision.objects.all()
    serializer_class = ParametrosSubdivisionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(proyecto__usuario=self.request.user)

class LoteResultanteViewSet(viewsets.ModelViewSet):
    queryset = LoteResultante.objects.all()
    serializer_class = LoteResultanteSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(terreno__proyecto__usuario=self.request.user)