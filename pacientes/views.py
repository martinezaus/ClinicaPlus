from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import F, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.cache import never_cache

from organizaciones.access import requiere_modulo
from .forms import PacienteForm
from .models import Paciente


@never_cache
@requiere_modulo("archivo")
def lista(request):
    consulta = request.GET.get("q", "").strip()
    pacientes = Paciente.objects.filter(organizacion=request.organizacion)
    if consulta:
        pacientes = pacientes.filter(
            Q(apellido_nombre__icontains=consulta)
            | Q(documento__icontains=consulta)
            | Q(historia_clinica__icontains=consulta)
        )
    pagina = Paginator(
        pacientes.annotate(expediente_id=F("expediente_fisico__id")).order_by(
            "apellido_nombre"
        ),
        50,
    ).get_page(request.GET.get("page"))
    return render(
        request,
        "pacientes/index.html",
        {"pacientes": pagina, "pagina": pagina, "consulta": consulta},
    )


@never_cache
@requiere_modulo("archivo")
def editar(request, paciente_id=None):
    if paciente_id is None:
        paciente = None
    else:
        paciente = get_object_or_404(
            Paciente,
            pk=paciente_id,
            organizacion=request.organizacion,
        )

    crear_expediente = request.GET.get("crear_expediente") == "1" or request.POST.get("crear_expediente") == "1"
    if request.method == "POST":
        form = PacienteForm(request.POST, instance=paciente)
        if form.is_valid():
            paciente = form.save(commit=False)
            if paciente_id is None:
                paciente.organizacion = request.organizacion
            paciente.save()
            messages.success(
                request,
                "Paciente registrado." if paciente_id is None else "Datos del paciente actualizados.",
            )
            if crear_expediente and not Paciente.objects.filter(
                pk=paciente.pk,
                expediente_fisico__isnull=False,
            ).exists():
                return redirect(f"{reverse('archivo:alta')}?paciente_id={paciente.pk}")
            return redirect("pacientes:index")
    else:
        form = PacienteForm(instance=paciente)

    return render(
        request,
        "pacientes/formulario.html",
        {
            "form": form,
            "paciente": paciente,
            "crear_expediente": crear_expediente,
        },
    )


def pulseras(request):
    return redirect("pulseras:form")


def historias(request):
    return redirect("archivo:buscar")
