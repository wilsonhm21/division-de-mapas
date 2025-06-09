# core/map_views.py

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from core.models import Proyecto
from django.http import HttpResponseServerError

@login_required
def map_view(request):
    """
    Vista que muestra la interfaz del mapa de subdivisión.
    Solo accesible para usuarios autenticados.
    """
    try:
        proyecto_del_usuario, created = Proyecto.objects.get_or_create(
            usuario=request.user,
            defaults={'nombre_proyecto': f"Proyecto por defecto de {request.user.username}"}
        )
    except Exception as e:
        return HttpResponseServerError(f"Error al obtener o crear proyecto: {e}")

    context = {
        'proyecto_id': proyecto_del_usuario.id
    }
    return render(request, "core/map_interface.html", context)
