# core/registration_views.py

from django.shortcuts import render, redirect
from django.contrib.auth import login
from core.forms import UserRegisterForm # Importación absoluta desde core.forms

def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            # Asegúrate que 'dashboard' es el nombre de la URL de tu dashboard
            return redirect('dashboard')
    else:
        form = UserRegisterForm()
    return render(request, 'core/register.html', {'form': form})