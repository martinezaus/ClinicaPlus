from django.urls import path

from .views import (
    AccesoView,
    dar_de_baja_usuario,
    alta_modulo,
    cambiar_estado_modulo,
    configuracion,
    editar_usuario,
    editar_modulo,
    facturacion,
    inicio,
    modulos,
    parametros,
    restablecer_contrasena_usuario,
    salir,
    soporte,
    usuarios,
)

app_name = "organizaciones"

urlpatterns = [
    path("", AccesoView.as_view(), name="login"),
    path("login/", AccesoView.as_view(), name="login-alias"),
    path("inicio/", inicio, name="inicio"),
    path("configuracion/", configuracion, name="configuracion"),
    path("configuracion/parametros/", parametros, name="parametros"),
    path("configuracion/modulos/", modulos, name="modulos"),
    path("configuracion/modulos/alta/", alta_modulo, name="alta-modulo"),
    path(
        "configuracion/modulos/<int:modulo_id>/editar/",
        editar_modulo,
        name="editar-modulo",
    ),
    path(
        "configuracion/modulos/<int:modulo_id>/estado/",
        cambiar_estado_modulo,
        name="cambiar-estado-modulo",
    ),
    path("facturacion/", facturacion, name="facturacion"),
    path("usuarios/", usuarios, name="usuarios"),
    path(
        "usuarios/<int:usuario_id>/editar/",
        editar_usuario,
        name="editar-usuario",
    ),
    path(
        "usuarios/<int:usuario_id>/baja/",
        dar_de_baja_usuario,
        name="dar-de-baja-usuario",
    ),
    path(
        "usuarios/<int:usuario_id>/contrasena/",
        restablecer_contrasena_usuario,
        name="restablecer-contrasena-usuario",
    ),
    path("logout/", salir, name="logout"),
    path("soporte/", soporte, name="soporte"),
]
