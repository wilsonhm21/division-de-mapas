from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView
from .models import Proyecto
from .serializers import ProyectoSerializer

class ProyectoViewSet(viewsets.ModelViewSet):
    """
    ViewSet para API REST (DRF) - Maneja todas las operaciones CRUD vía JSON
    """
    queryset = Proyecto.objects.all()
    serializer_class = ProyectoSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(usuario=self.request.user)

    def perform_create(self, serializer):
        serializer.save(usuario=self.request.user)

    @action(detail=False, methods=['GET'], template_name='core/proyectos/list.html')
    def list_html(self, request):
        """
        Versión HTML del listado (para usar en templates Django)
        URL: /api/proyectos/list_html/
        """
        proyectos = self.get_queryset()
        return render(request, self.template_name, {'proyectos': proyectos})

    @action(detail=True, methods=['GET'], template_name='core/proyectos/detail.html')
    def detail_html(self, request, pk=None):
        """
        Versión HTML del detalle
        URL: /api/proyectos/{pk}/detail_html/
        """
        proyecto = get_object_or_404(self.get_queryset(), pk=pk)
        return render(request, self.template_name, {'proyecto': proyecto})

class ProyectoListView(LoginRequiredMixin, ListView):
    """
    Vista basada en clase tradicional para HTML (opcional)
    URL: /proyectos/list/
    """
    model = Proyecto
    template_name = 'core/proyectos/list_alternativo.html'
    context_object_name = 'proyectos'

    def get_queryset(self):
        return Proyecto.objects.filter(usuario=self.request.user)