# core/serializers.py
from rest_framework import serializers
from .models import Proyecto, Terreno, ParametrosSubdivision, LoteResultante
from django.contrib.auth.models import User
import json
from shapely.geometry import shape
from shapely.validation import explain_validity

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email"]

class ProyectoSerializer(serializers.ModelSerializer):
    usuario = UserSerializer(read_only=True)
    usuario_id = serializers.IntegerField(
        write_only=True,
        help_text="ID del usuario dueño del proyecto",
        error_messages={'does_not_exist': 'El usuario con ID {pk_value} no existe.'}
    )

    class Meta:
        model = Proyecto
        fields = ["id", "usuario", "usuario_id", "nombre_proyecto", "descripcion", "fecha_creacion"]
        read_only_fields = ["fecha_creacion"]

    def validate_usuario_id(self, value):
        if not User.objects.filter(pk=value).exists():
            raise serializers.ValidationError(f"El usuario con ID {value} no existe.")
        return value

class TerrenoSerializer(serializers.ModelSerializer):
    proyecto_id = serializers.IntegerField(write_only=True, help_text="ID del proyecto asociado")
    proyecto = ProyectoSerializer(read_only=True)
    area_total = serializers.FloatField(read_only=True, help_text="Área en m² calculada automáticamente")

    class Meta:
        model = Terreno
        fields = ["id", "proyecto", "proyecto_id", "nombre_terreno", "geometria_geojson", 
                  "area_total", "metadatos_json", "fecha_registro"]
        read_only_fields = ["area_total", "fecha_registro"]

    def validate_geometria_geojson(self, value):
        try:
            data = json.loads(value)
            if 'type' not in data or 'coordinates' not in data:
                raise serializers.ValidationError("GeoJSON debe contener 'type' y 'coordinates'.")
            geom = shape(data)
            if not geom.is_valid:
                raise serializers.ValidationError(f"Geometría inválida: {explain_validity(geom)}")
            return value
        except json.JSONDecodeError:
            raise serializers.ValidationError("GeoJSON no es un JSON válido")
        except Exception as e:
            raise serializers.ValidationError(f"Error en geometría: {str(e)}")

class ParametrosSubdivisionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ParametrosSubdivision
        fields = "__all__"
        read_only_fields = ["fecha_actualizacion"]

class LoteResultanteSerializer(serializers.ModelSerializer):
    class Meta:
        model = LoteResultante
        fields = "__all__"
        read_only_fields = ["fecha_creacion"]
