from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib import messages
from core.forms import UserRegisterForm

def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'¡Cuenta creada exitosamente! Bienvenido {user.username}.')
            return redirect('core:dashboard')  # Asegúrate de que esta URL exista
        else:
            messages.error(request, 'Por favor corrige los errores en el formulario.')
    else:
        form = UserRegisterForm()
    return render(request, 'core/registration/register.html', {'form': form})

