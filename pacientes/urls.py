from django.urls import path
from . import views

app_name = "pacientes"

urlpatterns = [
    path("", views.lista, name="index"),
    path("nuevo/", views.editar, name="crear"),
    path("<int:paciente_id>/editar/", views.editar, name="editar"),
    path("pulseras/", views.pulseras, name="pulseras"),
    path("historias/", views.historias, name="historias"),
]
