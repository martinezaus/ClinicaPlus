from django.contrib import messages
from django.shortcuts import render
from django.views.decorators.cache import never_cache

from organizaciones.access import requiere_modulo
from .forms import PulseraForm
from .models import ImpresoraPulsera, PerfilMedioPulsera, TrabajoImpresion
from .printing import ImpresionError, construir_comando, enviar_a_windows


@never_cache
@requiere_modulo("pulseras")
def formulario(request):
    datos_pulsera = None
    perfil = None
    if request.method == "POST":
        form = PulseraForm(request.POST, organizacion=request.organizacion)
        if form.is_valid():
            datos_pulsera = form.cleaned_data
            impresora = datos_pulsera["impresora"]
            accion = request.POST.get("accion")
            if impresora:
                perfil = PerfilMedioPulsera.objects.filter(
                    impresora=impresora,
                    tipo=datos_pulsera["tipo"],
                ).first()
            if accion == "imprimir" and perfil:
                trabajo = TrabajoImpresion.objects.create(
                    impresora=perfil.impresora,
                    tipo=perfil.tipo,
                    copias=datos_pulsera["copias"],
                    solicitado_por=(
                        request.user if request.user.is_authenticated else None
                    ),
                )
                try:
                    payload = construir_comando(
                        datos_pulsera,
                        perfil,
                        datos_pulsera["copias"],
                    )
                    enviar_a_windows(perfil.impresora.cola_sistema, payload)
                except ImpresionError as error:
                    trabajo.estado = "error"
                    trabajo.error = str(error)
                    trabajo.save(update_fields=("estado", "error"))
                    messages.error(request, str(error))
                else:
                    trabajo.estado = "sent"
                    trabajo.save(update_fields=("estado",))
                    messages.success(
                        request,
                        f"Trabajo enviado a la cola «{perfil.impresora.cola_sistema}». "
                        "Verificá la impresión física antes de colocar la pulsera.",
                    )
    else:
        form = PulseraForm(
            initial={"tipo": "adulto"},
            organizacion=request.organizacion,
        )

    impresoras = list(
        ImpresoraPulsera.objects.filter(organizacion=request.organizacion)
        .prefetch_related("perfiles")
    )
    tipo_seleccionado = (
        form.data.get("tipo") if form.is_bound else form.initial.get("tipo", "adulto")
    )
    impresoras_configuradas = any(
        impresora.activa
        and impresora.cola_sistema.strip()
        and any(
            perfil.tipo == tipo_seleccionado
            and perfil.ancho_mm > 0
            and perfil.largo_mm > 0
            for perfil in impresora.perfiles.all()
        )
        for impresora in impresoras
    )
    for impresora in impresoras:
        perfiles = list(impresora.perfiles.all())
        faltantes = []
        if not impresora.activa:
            faltantes.append("inactiva")
        if not impresora.cola_sistema.strip():
            faltantes.append("falta configurar la cola de Windows")
        if not any(
            perfil.tipo == tipo_seleccionado
            and perfil.ancho_mm > 0
            and perfil.largo_mm > 0
            for perfil in perfiles
        ):
            faltantes.append(f"falta configurar la medida {tipo_seleccionado}")
        impresora.estado_configuracion = (
            "Lista para imprimir" if not faltantes else ", ".join(faltantes)
        )
    return render(
        request,
        "pulseras/formulario.html",
        {
            "form": form,
            "datos_pulsera": datos_pulsera,
            "perfil": perfil,
            "impresoras_configuradas": impresoras_configuradas,
            "impresoras": impresoras,
        },
    )
