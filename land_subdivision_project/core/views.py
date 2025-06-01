from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.contrib import messages
from .forms import PerfilForm, ConfiguracionForm
from .models import Perfil

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