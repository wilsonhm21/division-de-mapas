from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Proyecto, Terreno, ParametrosSubdivision, LoteResultante
from .serializers import (
    ProyectoSerializer, 
    TerrenoSerializer, 
    ParametrosSubdivisionSerializer, 
    LoteResultanteSerializer
)
from django.shortcuts import render, redirect
from django.http import JsonResponse
from .subdivision_logic import get_subdivision_algorithm 
import json
from django.contrib.auth import login
from .forms import UserRegisterForm

def map_view(request):
    """Vista para renderizar la interfaz del mapa"""
    return render(request, "core/map_interface.html")

def register(request):
    """Vista para el registro de nuevos usuarios"""
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('map_interface')  # Asegúrate de que esta URL esté definida en tus urls.py
    else:
        form = UserRegisterForm()
    return render(request, 'core/register.html', {'form': form})

class ProyectoViewSet(viewsets.ModelViewSet):
    queryset = Proyecto.objects.all()
    serializer_class = ProyectoSerializer
    # permission_classes = [permissions.IsAuthenticated]

class TerrenoViewSet(viewsets.ModelViewSet):
    queryset = Terreno.objects.all()
    serializer_class = TerrenoSerializer
    # permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    @action(detail=True, methods=["post"], url_path="subdivide")
    def subdivide_terreno(self, request, pk=None):
        """Acción para subdividir un terreno en lotes"""
        terreno = self.get_object()
        num_lots = request.data.get("num_lots", 2) 
        method = request.data.get("method", "line") 

        try:
            num_lots = int(num_lots)
            if num_lots <= 0:
                return Response(
                    {"error": "Number of lots must be a positive integer."},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except ValueError:
            return Response(
                {"error": "Invalid number of lots provided."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not terreno.geometria_geojson:
            return Response(
                {"error": "Terreno has no geometry to subdivide."},
                status=status.HTTP_400_BAD_REQUEST
            )

        subdivision_algorithm = get_subdivision_algorithm(method)
        if not subdivision_algorithm:
            return Response(
                {"error": f"Método de subdivisión '{method}' no válido."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            subdivision_result = subdivision_algorithm(terreno.geometria_geojson, num_lots)
        except Exception as e:
            return Response(
                {"error": f"Error durante la subdivisión: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        if "error" in subdivision_result:
            return Response(subdivision_result, status=status.HTTP_400_BAD_REQUEST)

        return Response(subdivision_result, status=status.HTTP_200_OK)

    @action(detail=True, methods=["get"], url_path="export")
    def export_terreno_geojson(self, request, pk=None):
        """Exporta el terreno y sus lotes como GeoJSON"""
        terreno = self.get_object()
        features = []

        # Procesar geometría original del terreno
        if terreno.geometria_geojson:
            try:
                original_geom_data = json.loads(terreno.geometria_geojson)
                geometry = original_geom_data["geometry"] if original_geom_data.get("type") == "Feature" else original_geom_data
                
                features.append({
                    "type": "Feature",
                    "geometry": geometry,
                    "properties": {
                        "id": terreno.id,
                        "nombre": terreno.nombre_terreno,
                        "tipo": "terreno_original"
                    }
                })
            except (json.JSONDecodeError, KeyError) as e:
                print(f"Error procesando GeoJSON del terreno {terreno.id}: {str(e)}")

        # Procesar lotes resultantes
        lotes_guardados = LoteResultante.objects.filter(terreno=terreno)
        for lote in lotes_guardados:
            if lote.geometria_lote_geojson:
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
                except json.JSONDecodeError as e:
                    print(f"Error procesando GeoJSON del lote {lote.id}: {str(e)}")

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
    # permission_classes = [permissions.IsAuthenticated]

class LoteResultanteViewSet(viewsets.ModelViewSet):
    queryset = LoteResultante.objects.all()
    serializer_class = LoteResultanteSerializer
    # permission_classes = [permissions.IsAuthenticated]