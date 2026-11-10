from django.urls import path

from . import views

app_name = "pulseras"

urlpatterns = [
    path("", views.formulario, name="form"),
]
