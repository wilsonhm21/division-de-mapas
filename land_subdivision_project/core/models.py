from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class Proyecto(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    nombre_proyecto = models.CharField(max_length=255)
    descripcion = models.TextField(blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nombre_proyecto

class Terreno(models.Model):
    proyecto = models.ForeignKey(Proyecto, related_name='terrenos', on_delete=models.CASCADE)
    nombre_terreno = models.CharField(max_length=255)
    geometria_geojson = models.TextField(help_text="Geometría del terreno en formato GeoJSON")
    area_total = models.FloatField(blank=True, null=True, help_text="Área total calculada del terreno")
    metadatos_json = models.JSONField(blank=True, null=True, help_text="Metadatos adicionales en formato JSON")
    fecha_registro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nombre_terreno} (Proyecto: {self.proyecto.nombre_proyecto})"

class ParametrosSubdivision(models.Model):
    proyecto = models.OneToOneField(Proyecto, on_delete=models.CASCADE, related_name='parametros_subdivision')
    area_min_lote = models.FloatField(blank=True, null=True)
    area_max_lote = models.FloatField(blank=True, null=True)
    frente_min_lote = models.FloatField(blank=True, null=True)
    algoritmo_seleccionado = models.CharField(max_length=100, blank=True, null=True)
    otros_criterios_json = models.JSONField(blank=True, null=True, help_text="Otros criterios urbanísticos en JSON")
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Parámetros para {self.proyecto.nombre_proyecto}"

class LoteResultante(models.Model):
    terreno = models.ForeignKey(Terreno, related_name='lotes_resultantes', on_delete=models.CASCADE)
    numero_lote = models.CharField(max_length=50)
    geometria_lote_geojson = models.TextField(help_text="Geometría del lote en formato GeoJSON")
    area_lote = models.FloatField(blank=True, null=True)
    frente_lote = models.FloatField(blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Lote {self.numero_lote} (Terreno: {self.terreno.nombre_terreno})"

class Perfil(models.Model):
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    notificaciones = models.BooleanField(default=True)
    tema_oscuro = models.BooleanField(default=False)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    direccion = models.TextField(blank=True, null=True)
    fecha_nacimiento = models.DateField(blank=True, null=True)
    
    def __str__(self):
        return f"Perfil de {self.usuario.username}"

# Señal para crear automáticamente un perfil cuando se crea un usuario
@receiver(post_save, sender=User)
def crear_perfil_usuario(sender, instance, created, **kwargs):
    if created:
        Perfil.objects.create(usuario=instance)

# Señal para guardar el perfil cuando se guarda el usuario
@receiver(post_save, sender=User)
def guardar_perfil_usuario(sender, instance, **kwargs):
    instance.perfil.save()