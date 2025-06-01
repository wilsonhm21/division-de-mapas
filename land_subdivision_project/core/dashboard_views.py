# core/dashboard_views.py

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from core.models import Proyecto, Terreno, LoteResultante # Importación absoluta desde core.models

@login_required
def dashboard_view(request):
    """
    Vista principal del dashboard.
    Solo accesible para usuarios autenticados.
    """
    num_projects = Proyecto.objects.filter(usuario=request.user).count()
    num_terrenos = Terreno.objects.filter(proyecto__usuario=request.user).count()
    num_lotes = LoteResultante.objects.filter(terreno__proyecto__usuario=request.user).count()

    context = {
        'num_active_projects': num_projects,
        'num_created_terrenos': num_terrenos,
        'num_created_lots': num_lotes,
        'num_alerts': 2,
        'user_name': request.user.username
    }
    return render(request, "core/dashboard.html", context)