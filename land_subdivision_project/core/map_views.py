# core/map_views.py

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from core.models import Proyecto # Importación absoluta desde core.models

@login_required
def map_view(request):
    """
    Vista que muestra la interfaz del mapa de subdivisión.
    Solo accesible para usuarios autenticados.
    """
    proyecto_del_usuario = request.user.proyecto_set.first()
    proyecto_id = None
    if proyecto_del_usuario:
        proyecto_id = proyecto_del_usuario.id
    else:
        proyecto_del_usuario = Proyecto.objects.create(
            usuario=request.user,
            nombre_proyecto=f"Proyecto por defecto de {request.user.username}"
        )
        proyecto_id = proyecto_del_usuario.id

    context = {
        'proyecto_id': proyecto_id
    }
    return render(request, "core/map_interface.html", context)