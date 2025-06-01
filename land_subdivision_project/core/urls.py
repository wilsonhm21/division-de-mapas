# myproject/urls.py

from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views # Para las vistas de login/logout de Django

# Importa las vistas directamente desde sus nuevos archivos
from core.registration_views import register
from core.dashboard_views import dashboard_view
from core.map_views import map_view
from core import views 
from core.documents_views import subir_terreno_view, mostrar_grafico_terreno
from core.api_views import (
    ProyectoViewSet, TerrenoViewSet,
    ParametrosSubdivisionViewSet, LoteResultanteViewSet
)

from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'proyectos', ProyectoViewSet)
router.register(r'terrenos', TerrenoViewSet)
router.register(r'parametros-subdivision', ParametrosSubdivisionViewSet)
router.register(r'lotes-resultantes', LoteResultanteViewSet)

# Opcional: define un app_name si lo usas en tus reverse/redirects.
app_name = 'core' # Descomenta si lo necesitas

urlpatterns = [
    path('admin/', admin.site.urls),

    # URLs de Autenticación
    path('register/', register, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='core/registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='/core/login/'), name='logout'),
    
    path('perfil/', views.perfil_view, name='perfil'),
    path('configuracion/', views.configuracion_view, name='configuracion'),

    # URLs del Dashboard
    path('dashboard/', dashboard_view, name='dashboard'),

    # URLs del Mapa
    path('map/', map_view, name='map_interface'),

    # URLs de Documentos (Subir Terreno, Gráficos)
    path('subir-terreno/', subir_terreno_view, name='subir_terreno'),
    path('terreno/<int:terreno_id>/grafico/', mostrar_grafico_terreno, name='mostrar_grafico_terreno'),

    # URLs de la API
    path('api/', include(router.urls)),

    # Si tu core/views.py vacío tuviera alguna vista, la incluirías aquí.
    # Por ejemplo, si tuviste una 'home_view' en core/views.py:
    # path('', home_base_view, name='home'),
]