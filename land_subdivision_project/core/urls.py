from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views

from core.registration_views import register
from core.dashboard_views import dashboard_view
from core.map_views import map_view
from core import views 
from core.documents_views import subir_terreno_view, mostrar_grafico_terreno
from core.api_views import (
     TerrenoViewSet,ProyectoViewSet,ParametrosSubdivisionViewSet, LoteResultanteViewSet
)

from core.views import subdividir_terreno
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'proyectos', ProyectoViewSet)
router.register(r'terrenos', TerrenoViewSet)
router.register(r'parametros-subdivision', ParametrosSubdivisionViewSet)
router.register(r'lotes-resultantes', LoteResultanteViewSet)

# Si usas namespace para urls, descomenta esta línea
app_name = 'core'

urlpatterns = [
    path('admin/', admin.site.urls),

    # Autenticación
    path('register/', register, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='core/registration/login.html'), name='login'),
     path('logout/', auth_views.LogoutView.as_view(next_page='/core/login/'), name='logout'),

    # Perfil y configuración
    path('perfil/', views.perfil_view, name='perfil'),
    path('configuracion/', views.configuracion_view, name='configuracion'),

    # Dashboard
    path('dashboard/', dashboard_view, name='dashboard'),

    # Mapa
    path('map/', map_view, name='map_interface'),

    # Documentos
    path('subir-terreno/', subir_terreno_view, name='subir_terreno'),
    path('terreno/<int:terreno_id>/grafico/', mostrar_grafico_terreno, name='mostrar_grafico_terreno'),

    # API
    path('api/', include(router.urls)),

    # url del algoroitmo de spep
     path('subdividir/', subdividir_terreno, name='subdividir_terreno'),
    # Ruta base (opcional)
    # path('', views.home_view, name='home'),
]
