from functools import wraps

from django.contrib import messages
from django.contrib.auth import get_user_model, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.http import Http404
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods, require_POST

from .access import requiere_modulo
from .forms import (
    AccesoForm,
    AltaUsuarioForm,
    EditarUsuarioForm,
    RestablecerContrasenaForm,
)
from .forms import ModuloExternoForm
from .models import Membresia, ModuloExterno, Organizacion
from archivo.models import ExpedienteFisico, PrestamoExpediente
from pacientes.models import Paciente


def superusuario_required(view):
    @wraps(view)
    @login_required
    def wrapped(request, *args, **kwargs):
        if not request.user.is_superuser:
            raise PermissionDenied
        return view(request, *args, **kwargs)

    return wrapped


class AccesoView(LoginView):
    authentication_form = AccesoForm
    template_name = "organizaciones/index.html"
    redirect_authenticated_user = True


@login_required
def inicio(request):
    if request.user.is_superuser:
        organizacion = request.organizacion
        perfil = "Administrador del sistema"
        puede_archivo = True
        puede_pulseras = True
    else:
        try:
            membresia = request.user.membresia_organizacion
        except Membresia.DoesNotExist:
            raise PermissionDenied("Solicitá al administrador que te asigne un perfil.")

        if not membresia.activa or not membresia.organizacion.activa:
            raise PermissionDenied("El usuario o la organización están inactivos.")

        organizacion = membresia.organizacion
        perfil = membresia.get_perfil_display()
        puede_archivo = membresia.puede_acceder("archivo")
        puede_pulseras = membresia.puede_acceder("pulseras")

    sistemas = []
    if puede_archivo:
        sistemas.extend(
            [
                {
                    "nombre": "Pacientes",
                    "descripcion": "Alta, consulta y actualización de los datos de pacientes.",
                    "icono": "♙",
                    "url": "pacientes:index",
                    "disponible": True,
                    "estado": "Disponible",
                },
                {
                    "nombre": "Expediente físico / Archivo",
                    "descripcion": "Búsqueda, creación y seguimiento de expedientes físicos.",
                    "icono": "▤",
                    "url": "archivo:buscar",
                    "disponible": True,
                    "estado": "Disponible",
                },
            ]
        )
    if puede_pulseras:
        sistemas.append(
            {
                "nombre": "Admisión",
                "descripcion": "Emisión de pulseras identificatorias. El ingreso a internación está en desarrollo.",
                "icono": "＋",
                "url": "pulseras:form",
                "disponible": True,
                "estado": "Parcialmente disponible",
            }
        )
    if request.user.is_superuser or request.user.membresia_organizacion.puede_acceder(
        "facturacion"
    ):
        sistemas.append(
            {
                "nombre": "Facturación",
                "descripcion": "Módulo de facturación en preparación.",
                "icono": "$",
                "url": "organizaciones:facturacion",
                "disponible": True,
                "estado": "En preparación",
            }
        )
    if request.user.is_superuser:
        sistemas.extend(
            [
                {
                    "nombre": "Turnos",
                    "descripcion": "Gestión de agendas, disponibilidad y turnos de atención.",
                    "icono": "▦",
                    "disponible": False,
                    "estado": "Bloqueado · En desarrollo",
                },
                {
                    "nombre": "Prestaciones",
                    "descripcion": "Registro y consulta de prestaciones realizadas.",
                    "icono": "✚",
                    "disponible": False,
                    "estado": "Bloqueado · En desarrollo",
                },
                {
                    "nombre": "Estadísticas y reportes",
                    "descripcion": "Consultas e informes sobre la actividad de la organización.",
                    "icono": "▥",
                    "disponible": False,
                    "estado": "Bloqueado · En desarrollo",
                },
                {
                    "nombre": "Farmacia",
                    "descripcion": "Carga de recetas y expendido de medicación.",
                    "icono": "⚕",
                    "disponible": False,
                    "estado": "Bloqueado · En desarrollo",
                },
            ]
        )
        sistemas.append(
            {
                "nombre": "Configuración",
                "descripcion": "Configurá los usuarios y sus accesos al sistema.",
                "icono": "⚙",
                "url": "organizaciones:configuracion",
                "disponible": True,
                "estado": "Administración",
            }
        )
    modulos_externos = ModuloExterno.objects.filter(activo=True)
    if not request.user.is_superuser:
        modulos_externos = request.user.membresia_organizacion.modulos_externos.filter(
            activo=True
        )

    estadisticas = []
    if puede_archivo:
        pacientes_org = Paciente.objects.filter(organizacion=organizacion)
        expedientes_org = ExpedienteFisico.objects.filter(paciente__organizacion=organizacion)
        total_expedientes = expedientes_org.count()
        estadisticas = [
            {"nombre": "Pacientes registrados", "valor": pacientes_org.count(), "icono": "♙"},
            {"nombre": "Expedientes físicos", "valor": total_expedientes, "icono": "▤"},
            {
                "nombre": "Archivo activo",
                "valor": expedientes_org.filter(archivo="A").count(),
                "icono": "●",
            },
            {
                "nombre": "Archivo pasivo",
                "valor": expedientes_org.filter(archivo="P").count(),
                "icono": "◌",
            },
            {
                "nombre": "Expedientes desaparecidos",
                "valor": expedientes_org.filter(archivo="D").count(),
                "icono": "!",
            },
            {
                "nombre": "Préstamos vigentes",
                "valor": PrestamoExpediente.objects.filter(
                    expediente__paciente__organizacion=organizacion,
                    fecha_devolucion__isnull=True,
                ).count(),
                "icono": "↗",
            },
        ]

    return render(
        request,
        "organizaciones/inicio.html",
        {
            "organizacion": organizacion,
            "perfil": perfil,
            "sistemas": sistemas,
            "modulos_externos": modulos_externos,
            "estadisticas": estadisticas,
            "estadisticas_disponibles": puede_archivo,
        },
    )


@superusuario_required
@require_http_methods(["GET", "POST"])
def usuarios(request):
    datos = request.POST if request.method == "POST" else None
    formulario = AltaUsuarioForm(datos)
    if request.method == "POST" and formulario.is_valid():
        with transaction.atomic():
            usuario = formulario.save(commit=False)
            usuario.is_staff = False
            usuario.is_superuser = False
            usuario.save()
            membresia = Membresia.objects.create(
                usuario=usuario,
                organizacion=formulario.cleaned_data["organizacion"],
                perfil=formulario.cleaned_data["perfil"],
                modulos=formulario.cleaned_data["modulos"],
            )
            membresia.modulos_externos.set(
                formulario.cleaned_data["modulos_externos"]
            )
        messages.success(request, f"Se creó el usuario {usuario.username}.")
        return redirect("organizaciones:usuarios")

    membresias = (
        Membresia.objects.select_related("usuario", "organizacion")
        .prefetch_related("modulos_externos")
        .order_by("organizacion__nombre", "usuario__username")
    )
    return render(
        request,
        "organizaciones/usuarios.html",
        {"formulario": formulario, "membresias": membresias},
    )


@superusuario_required
def configuracion(request):
    return render(request, "organizaciones/configuracion.html")


@superusuario_required
def parametros(request):
    return render(request, "organizaciones/parametros.html")


@superusuario_required
def modulos(request):
    return render(
        request,
        "organizaciones/modulos.html",
        {
            "formulario": ModuloExternoForm(),
            "modulos": ModuloExterno.objects.all(),
        },
    )


@superusuario_required
@require_http_methods(["GET", "POST"])
def alta_modulo(request):
    datos = request.POST if request.method == "POST" else None
    formulario = ModuloExternoForm(datos)
    if request.method == "POST" and formulario.is_valid():
        modulo = formulario.save()
        messages.success(request, f"Se agregó el módulo {modulo.nombre}.")
        return redirect("organizaciones:modulos")

    return render(
        request,
        "organizaciones/modulos.html",
        {
            "formulario": formulario,
            "modulos": ModuloExterno.objects.all(),
        },
    )


@superusuario_required
@require_http_methods(["GET", "POST"])
def editar_modulo(request, modulo_id):
    try:
        modulo = ModuloExterno.objects.get(pk=modulo_id)
    except ModuloExterno.DoesNotExist as exc:
        raise Http404 from exc

    datos = request.POST if request.method == "POST" else None
    formulario = ModuloExternoForm(datos, instance=modulo)
    if request.method == "POST" and formulario.is_valid():
        formulario.save()
        messages.success(request, f"Se actualizó el módulo {modulo.nombre}.")
        return redirect("organizaciones:modulos")

    return render(
        request,
        "organizaciones/editar_modulo.html",
        {"formulario": formulario, "modulo": modulo},
    )


@superusuario_required
@require_POST
def cambiar_estado_modulo(request, modulo_id):
    try:
        modulo = ModuloExterno.objects.get(pk=modulo_id)
    except ModuloExterno.DoesNotExist as exc:
        raise Http404 from exc

    modulo.activo = not modulo.activo
    modulo.save(update_fields=["activo"])
    estado = "activado" if modulo.activo else "desactivado"
    messages.success(request, f"Se {estado} el módulo {modulo.nombre}.")
    return redirect("organizaciones:modulos")


@superusuario_required
@require_http_methods(["GET", "POST"])
def editar_usuario(request, usuario_id):
    try:
        membresia = Membresia.objects.select_related("usuario", "organizacion").get(
            usuario_id=usuario_id,
            usuario__is_superuser=False,
        )
    except Membresia.DoesNotExist as exc:
        raise Http404 from exc

    datos = request.POST if request.method == "POST" else None
    formulario = EditarUsuarioForm(
        datos,
        usuario=membresia.usuario,
        membresia=membresia,
    )
    if request.method == "POST" and formulario.is_valid():
        with transaction.atomic():
            formulario.save()
        messages.success(
            request,
            f"Se actualizaron los datos y los accesos de {membresia.usuario.username}.",
        )
        return redirect("organizaciones:usuarios")

    return render(
        request,
        "organizaciones/editar_usuario.html",
        {"formulario": formulario, "membresia": membresia},
    )


@requiere_modulo("facturacion")
def facturacion(request):
    return render(request, "organizaciones/facturacion.html")


@superusuario_required
@require_POST
def dar_de_baja_usuario(request, usuario_id):
    try:
        membresia = Membresia.objects.select_related("usuario").get(
            usuario_id=usuario_id,
            usuario__is_superuser=False,
        )
    except Membresia.DoesNotExist as exc:
        raise Http404 from exc

    with transaction.atomic():
        membresia.usuario.is_active = False
        membresia.usuario.save(update_fields=["is_active"])
        membresia.activa = False
        membresia.save(update_fields=["activa"])

    messages.success(request, f"Se dio de baja al usuario {membresia.usuario.username}.")
    return redirect("organizaciones:usuarios")


@superusuario_required
@require_http_methods(["GET", "POST"])
def restablecer_contrasena_usuario(request, usuario_id):
    try:
        usuario = get_user_model().objects.get(
            pk=usuario_id,
            is_superuser=False,
            membresia_organizacion__isnull=False,
        )
        membresia = usuario.membresia_organizacion
    except get_user_model().DoesNotExist as exc:
        raise Http404 from exc

    datos = request.POST if request.method == "POST" else None
    formulario = RestablecerContrasenaForm(usuario, datos)
    if request.method == "POST" and formulario.is_valid():
        formulario.save()
        messages.success(request, f"Se restableció la contraseña de {usuario.username}.")
        return redirect("organizaciones:usuarios")

    return render(
        request,
        "organizaciones/restablecer_contrasena.html",
        {"formulario": formulario, "membresia": membresia},
    )


@login_required
def soporte(request):
    return render(request, "organizaciones/soporte.html")


@require_POST
def salir(request):
    logout(request)
    return redirect("organizaciones:login")
