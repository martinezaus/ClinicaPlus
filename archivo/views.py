from django.contrib import messages
from django.db import IntegrityError, transaction
from django.db.models import F, Prefetch, Q
from django.db.models.functions import Coalesce
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST

from organizaciones.access import requiere_modulo
from pacientes.models import Paciente
from .forms import (
    AltaExpedienteForm,
    BusquedaExpedienteForm,
    PrestamoExpedienteForm,
    UbicacionExpedienteForm,
)
from .models import ExpedienteFisico, PrestamoExpediente


@never_cache
@requiere_modulo("archivo")
def buscar(request):
    form = BusquedaExpedienteForm(request.POST or None)
    expedientes = ExpedienteFisico.objects.none()
    pacientes_sistema = []
    buscado = False

    if form.is_valid():
        identificador = form.cleaned_data["identificador"].strip()
        if identificador:
            expedientes = ExpedienteFisico.objects.filter(
                paciente__organizacion=request.organizacion,
            ).filter(
                Q(paciente__documento__iexact=identificador)
                | Q(paciente__historia_clinica__iexact=identificador)
                | Q(paciente__apellido_nombre__icontains=identificador)
            ).prefetch_related(
                Prefetch(
                    "prestamos",
                    queryset=PrestamoExpediente.objects.filter(
                        fecha_devolucion__isnull=True
                    ),
                    to_attr="prestamos_activos",
                )
            ).select_related("paciente").order_by("paciente__apellido_nombre")
            buscado = True
            if not expedientes.exists():
                pacientes_sistema = list(
                    Paciente.objects.filter(
                        organizacion=request.organizacion,
                        expediente_fisico__isnull=True,
                    ).filter(
                        Q(documento__iexact=identificador)
                        | Q(historia_clinica__iexact=identificador)
                        | Q(apellido_nombre__icontains=identificador)
                    ).order_by("apellido_nombre")[:20]
                )

    actividad_reciente = PrestamoExpediente.objects.select_related(
        "expediente"
    ).filter(
        expediente__paciente__organizacion=request.organizacion
    ).annotate(
        momento_actividad=Coalesce("fecha_devolucion", "fecha_prestamo")
    ).order_by("-momento_actividad")[:10]

    return render(
        request,
        "archivo/busqueda.html",
        {
            "form": form,
            "expedientes": expedientes,
            "pacientes_sistema": pacientes_sistema,
            "buscado": buscado,
            "actividad_reciente": actividad_reciente,
        },
    )


@never_cache
@requiere_modulo("archivo")
def alta(request):
    paciente_id = request.GET.get("paciente_id", "")
    if paciente_id.isdecimal():
        expediente_id = ExpedienteFisico.objects.filter(
            paciente_id=paciente_id,
            paciente__organizacion=request.organizacion,
        ).values_list("pk", flat=True).first()
        if expediente_id:
            return redirect("archivo:ficha", expediente_id=expediente_id)

    inicial = {"paciente": request.GET.get("paciente_id")} if request.GET.get("paciente_id") else {}
    if request.method == "POST":
        form = AltaExpedienteForm(request.POST, organizacion=request.organizacion)
        if form.is_valid():
            expediente = form.save(commit=False)
            try:
                expediente.save()
            except IntegrityError:
                form.add_error("paciente", "Este paciente ya tiene un expediente físico.")
            else:
                messages.success(
                    request,
                    f"Se registró el expediente de {expediente.paciente.apellido_nombre}.",
                )
                return redirect("archivo:buscar")
    else:
        form = AltaExpedienteForm(initial=inicial, organizacion=request.organizacion)

    return render(
        request,
        "archivo/alta.html",
        {
            "form": form,
            "pacientes_disponibles": form.pacientes_disponibles,
            "paciente_seleccionado": form.fields["paciente"].queryset.first(),
        },
    )


@never_cache
@requiere_modulo("archivo")
def buscar_pacientes_para_alta(request):
    consulta = request.GET.get("q", "").strip()
    resultados = []
    if len(consulta) >= 2:
        pacientes = Paciente.objects.filter(
            organizacion=request.organizacion,
            expediente_fisico__isnull=True,
        ).filter(
            Q(apellido_nombre__icontains=consulta)
            | Q(documento__istartswith=consulta)
            | Q(historia_clinica__istartswith=consulta)
        ).order_by("apellido_nombre").values(
            "id", "apellido_nombre", "documento", "historia_clinica"
        )[:15]
        resultados = [
            {
                "id": paciente["id"],
                "nombre": paciente["apellido_nombre"],
                "documento": paciente["documento"],
                "historia_clinica": paciente["historia_clinica"],
            }
            for paciente in pacientes
        ]
    return JsonResponse({"resultados": resultados})


@never_cache
@requiere_modulo("archivo")
def caratula(request, paciente_id):
    paciente = get_object_or_404(
        Paciente.objects.annotate(expediente_id=F("expediente_fisico__id")),
        pk=paciente_id,
        organizacion=request.organizacion,
    )
    expediente = None
    if paciente.expediente_id:
        expediente = get_object_or_404(
            ExpedienteFisico,
            pk=paciente.expediente_id,
            paciente__organizacion=request.organizacion,
        )
    return render(
        request,
        "archivo/caratula.html",
        {
            "paciente": paciente,
            "expediente": expediente,
            "fecha_impresion": timezone.localtime(),
        },
    )


@never_cache
@requiere_modulo("archivo")
def editar_ubicacion(request, expediente_id):
    expediente = get_object_or_404(
        ExpedienteFisico,
        pk=expediente_id,
        paciente__organizacion=request.organizacion,
    )
    if request.method == "POST":
        form = UbicacionExpedienteForm(request.POST, instance=expediente)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                f"Se actualizó la ubicación del expediente de {expediente.paciente.apellido_nombre}.",
            )
            return redirect("archivo:ficha", expediente_id=expediente.pk)
    else:
        form = UbicacionExpedienteForm(instance=expediente)

    return render(
        request,
        "archivo/editar_ubicacion.html",
        {"form": form, "expediente": expediente},
    )


@never_cache
@requiere_modulo("archivo")
@require_POST
def enviar_a_pasivo(request, expediente_id):
    expediente = get_object_or_404(
        ExpedienteFisico,
        pk=expediente_id,
        paciente__organizacion=request.organizacion,
    )
    if expediente.archivo != "A":
        messages.info(request, "Este expediente ya no está en el Archivo Activo.")
        return redirect("archivo:ficha", expediente_id=expediente.pk)
    if expediente.prestamos.filter(fecha_devolucion__isnull=True).exists():
        messages.error(
            request,
            "No se puede enviar al Archivo Pasivo mientras la historia tenga un préstamo activo.",
        )
        return redirect("archivo:ficha", expediente_id=expediente.pk)

    expediente.archivo = "P"
    expediente.save(update_fields=("archivo",))
    messages.success(
        request,
        f"El expediente de {expediente.paciente.apellido_nombre} se envió al Archivo Pasivo.",
    )
    return redirect("archivo:ficha", expediente_id=expediente.pk)


@never_cache
@requiere_modulo("archivo")
def prestar(request, expediente_id):
    expediente = get_object_or_404(
        ExpedienteFisico,
        pk=expediente_id,
        paciente__organizacion=request.organizacion,
    )
    if expediente.archivo != "A":
        messages.error(request, "Solo se pueden prestar historias del Archivo Activo.")
        return redirect("archivo:ficha", expediente_id=expediente.pk)
    if PrestamoExpediente.objects.filter(
        expediente=expediente,
        fecha_devolucion__isnull=True,
    ).exists():
        messages.error(request, "Este expediente ya tiene un préstamo activo.")
        return redirect("archivo:historial", expediente_id=expediente.pk)

    if request.method == "POST":
        form = PrestamoExpedienteForm(request.POST)
        if form.is_valid():
            prestamo = form.save(commit=False)
            prestamo.expediente = expediente
            try:
                with transaction.atomic():
                    prestamo.save()
            except IntegrityError:
                messages.error(request, "Este expediente ya tiene un préstamo activo.")
                return redirect("archivo:historial", expediente_id=expediente.pk)
            messages.success(request, "Se registró la entrega de la historia clínica.")
            return redirect("archivo:historial", expediente_id=expediente.pk)
    else:
        form = PrestamoExpedienteForm()

    return render(
        request,
        "archivo/prestamo.html",
        {"form": form, "expediente": expediente},
    )


@never_cache
@requiere_modulo("archivo")
def devolver(request, prestamo_id):
    prestamo = get_object_or_404(
        PrestamoExpediente.objects.select_related("expediente"),
        pk=prestamo_id,
        expediente__paciente__organizacion=request.organizacion,
    )
    if request.method != "POST":
        return redirect("archivo:historial", expediente_id=prestamo.expediente_id)

    if prestamo.fecha_devolucion is None:
        prestamo.fecha_devolucion = timezone.now()
        prestamo.save(update_fields=("fecha_devolucion",))
        messages.success(
            request,
            f"Se registró la devolución. Permaneció prestada {prestamo.dias_prestado} días.",
        )
    else:
        messages.info(request, "La devolución de este préstamo ya estaba registrada.")
    return redirect("archivo:historial", expediente_id=prestamo.expediente_id)


@never_cache
@requiere_modulo("archivo")
def historial(request, expediente_id):
    expediente = get_object_or_404(
        ExpedienteFisico,
        pk=expediente_id,
        paciente__organizacion=request.organizacion,
    )
    prestamos = expediente.prestamos.order_by("-fecha_prestamo")
    prestamo_activo = prestamos.filter(fecha_devolucion__isnull=True).first()
    return render(
        request,
        "archivo/historial.html",
        {
            "expediente": expediente,
            "prestamos": prestamos,
            "prestamo_activo": prestamo_activo,
        },
    )


@never_cache
@requiere_modulo("archivo")
def ficha(request, expediente_id):
    expediente = get_object_or_404(
        ExpedienteFisico,
        pk=expediente_id,
        paciente__organizacion=request.organizacion,
    )
    prestamos = expediente.prestamos.order_by("-fecha_prestamo")
    prestamo_activo = prestamos.filter(fecha_devolucion__isnull=True).first()
    return render(
        request,
        "archivo/ficha.html",
        {
            "expediente": expediente,
            "prestamos": prestamos,
            "prestamo_activo": prestamo_activo,
        },
    )
