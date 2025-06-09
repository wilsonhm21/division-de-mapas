from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.contrib import messages
from .forms import PerfilForm, ConfiguracionForm
from .models import Perfil

import io
import sys
from .spep import subdivide_terrain_geographic


@login_required
def perfil_view(request):
    # Asegurarse de que el perfil exista
    perfil, created = Perfil.objects.get_or_create(usuario=request.user)
    
    if request.method == 'POST':
        form = PerfilForm(request.POST, request.FILES, instance=request.user)  # ¡Añade request.FILES!
        if form.is_valid():
            form.save()
            messages.success(request, 'Perfil actualizado correctamente')
            return redirect('core:perfil')
    else:
        form = PerfilForm(instance=request.user)

    # Obtener conteos
    proyectos_count = request.user.proyecto_set.count()
    terrenos_count = sum(proyecto.terrenos.count() for proyecto in request.user.proyecto_set.all())

    context = {
        'form': form,
        'proyectos_count': proyectos_count,
        'terrenos_count': terrenos_count,
        'tiene_avatar': perfil.avatar and perfil.avatar.url  # Verifica si hay avatar
    }
    return render(request, 'core/perfil.html', context)

@login_required
def configuracion_view(request):
    # Asegurar que el perfil exista
    perfil, created = Perfil.objects.get_or_create(usuario=request.user)
    
    # Obtener conteos (igual que en perfil_view)
    proyectos_count = request.user.proyecto_set.count()
    terrenos_count = sum(
        proyecto.terrenos.count()
        for proyecto in request.user.proyecto_set.all()
    )

    # Formularios
    password_form = PasswordChangeForm(request.user)
    config_form = ConfiguracionForm(instance=perfil)

    if request.method == 'POST':
        if 'cambiar_password' in request.POST:
            password_form = PasswordChangeForm(request.user, request.POST)
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)
                messages.success(request, 'Contraseña actualizada correctamente')
                return redirect('core:configuracion')
        
        elif 'cambiar_config' in request.POST:
            config_form = ConfiguracionForm(request.POST, request.FILES, instance=perfil)
            if config_form.is_valid():
                config_form.save()
                messages.success(request, 'Configuración guardada correctamente')
                return redirect('core:configuracion')

    context = {
        'password_form': password_form,
        'config_form': config_form,
        'proyectos_count': proyectos_count,
        'terrenos_count': terrenos_count
    }
    return render(request, 'core/configuracion.html', context)

@login_required
def subdividir_terreno(request):
    if request.method == 'POST':
        coordenadas = request.POST.get('coordenadas')
        partes = int(request.POST.get('partes'))
        ancho_carretera = float(request.POST.get('ancho_carretera', 3.0))
        area_verde = request.POST.get('area_verde')
        area_verde = int(area_verde) if area_verde else None

        try:
            coords = eval(coordenadas)
            if coords[0] != coords[-1]:
                coords.append(coords[0])
        except:
            return render(request, 'core/proyectos/formulario.html', {'error': 'Coordenadas inválidas'})

        output_path = 'core/static/img/subdivision_resultado.png'

        # 🔄 Capturar salida de consola
        buffer = io.StringIO()
        sys_stdout = sys.stdout
        sys.stdout = buffer

        # Ejecutar subdivisión
        subdivide_terrain_geographic(
            lat_lon_coords=coords,
            parts=partes,
            road_width=ancho_carretera,
            green_area_idx=area_verde,
            output_path=output_path
        )

        # Restaurar salida estándar
        sys.stdout = sys_stdout
        resumen_texto = buffer.getvalue()
        buffer.close()

        return render(request, 'core/proyectos/resultado.html', {
            'imagen_url': '/static/img/subdivision_resultado.png',
            'resumen': resumen_texto
        })
        
        #resultado = subdivide_terrain_geographic(
         #   lat_lon_coords=coords,
          #  parts=partes,
           # road_width=ancho_carretera,
            #green_area_idx=area_verde,
            #output_path=output_path
        #)

        #return render(request, 'core/proyectos/resultado.html', {
         #   'imagen_url': '/static/img/subdivision_resultado.png',
          #  'validaciones': resultado['validation_results']
        #})

    return render(request, 'core/proyectos/formulario.html')