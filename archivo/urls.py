from django.urls import path

from . import views

app_name = "archivo"

urlpatterns = [
    path("", views.buscar, name="buscar"),
    path("alta/", views.alta, name="alta"),
    path(
        "alta/buscar-pacientes/",
        views.buscar_pacientes_para_alta,
        name="buscar_pacientes_para_alta",
    ),
    path(
        "pacientes/<int:paciente_id>/caratula/",
        views.caratula,
        name="caratula",
    ),
    path(
        "expedientes/<int:expediente_id>/ubicacion/",
        views.editar_ubicacion,
        name="editar_ubicacion",
    ),
    path(
        "expedientes/<int:expediente_id>/enviar-a-pasivo/",
        views.enviar_a_pasivo,
        name="enviar_a_pasivo",
    ),
    path("expedientes/<int:expediente_id>/prestamo/", views.prestar, name="prestar"),
    path("expedientes/<int:expediente_id>/", views.ficha, name="ficha"),
    path("expedientes/<int:expediente_id>/historial/", views.historial, name="historial"),
    path("prestamos/<int:prestamo_id>/devolver/", views.devolver, name="devolver"),
]
