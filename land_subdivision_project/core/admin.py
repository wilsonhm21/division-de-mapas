from django.contrib import admin
from .models import Proyecto, Terreno, ParametrosSubdivision, LoteResultante

class TerrenoInline(admin.TabularInline):  
    model = Terreno
    extra = 1
    fields = ('nombre_terreno', 'area_total', 'fecha_registro')
    readonly_fields = ('area_total', 'fecha_registro')

class ParametrosSubdivisionInline(admin.StackedInline):
    model = ParametrosSubdivision
    can_delete = False
    verbose_name_plural = 'Parámetros de Subdivisión'

@admin.register(Proyecto)
class ProyectoAdmin(admin.ModelAdmin):
    list_display = ('nombre_proyecto', 'usuario', 'fecha_creacion')
    list_filter = ('usuario', 'fecha_creacion')
    search_fields = ('nombre_proyecto', 'descripcion')
    inlines = [TerrenoInline, ParametrosSubdivisionInline]
    readonly_fields = ('fecha_creacion',)
    ordering = ('-fecha_creacion',)
    list_per_page = 25

@admin.register(Terreno)
class TerrenoAdmin(admin.ModelAdmin):
    list_display = ('nombre_terreno', 'proyecto', 'area_total', 'fecha_registro')
    list_filter = ('proyecto', 'fecha_registro')
    search_fields = ('nombre_terreno', 'proyecto__nombre_proyecto')
    readonly_fields = ('area_total', 'fecha_registro')
    raw_id_fields = ('proyecto',)
    ordering = ('-fecha_registro',)
    list_per_page = 25

@admin.register(LoteResultante)
class LoteResultanteAdmin(admin.ModelAdmin):
    list_display = ('numero_lote', 'terreno', 'area_lote', 'frente_lote', 'fecha_creacion')
    list_filter = ('terreno__proyecto', 'fecha_creacion')
    search_fields = ('numero_lote', 'terreno__nombre_terreno')
    readonly_fields = ('fecha_creacion',)
    raw_id_fields = ('terreno',)
    ordering = ('-fecha_creacion',)
    list_per_page = 25

@admin.register(ParametrosSubdivision)
class ParametrosSubdivisionAdmin(admin.ModelAdmin):
    list_display = ('proyecto', 'area_min_lote', 'area_max_lote', 'frente_min_lote')
    search_fields = ('proyecto__nombre_proyecto',)
    raw_id_fields = ('proyecto',)
    list_per_page = 25
