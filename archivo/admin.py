from django.contrib import admin

from organizaciones.models import Membresia
from pacientes.models import Paciente
from .models import ExpedienteFisico, PrestamoExpediente


@admin.register(ExpedienteFisico)
class ExpedienteFisicoAdmin(admin.ModelAdmin):
    list_display = (
        "paciente",
        "pasillo",
        "estanteria",
        "estante",
    )
    search_fields = (
        "paciente__apellido_nombre",
        "paciente__documento",
        "paciente__historia_clinica",
        "pasillo",
        "estanteria",
        "estante",
        "referencia_ubicacion",
    )
    list_filter = ("pasillo", "estanteria", "estante")

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        if request.user.is_superuser:
            return queryset
        try:
            membership = request.user.membresia_organizacion
        except Membresia.DoesNotExist:
            return queryset.none()
        return queryset.filter(paciente__organizacion=membership.organizacion)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "paciente" and not request.user.is_superuser:
            try:
                membership = request.user.membresia_organizacion
            except Membresia.DoesNotExist:
                kwargs["queryset"] = Paciente.objects.none()
            else:
                kwargs["queryset"] = Paciente.objects.filter(
                    organizacion=membership.organizacion
                )
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(PrestamoExpediente)
class PrestamoExpedienteAdmin(admin.ModelAdmin):
    list_display = (
        "expediente",
        "entregado_por",
        "retirado_por",
        "servicio",
        "profesional",
        "fecha_prestamo",
        "fecha_devolucion",
        "dias_prestado",
    )
    search_fields = (
        "expediente__paciente__apellido_nombre",
        "expediente__paciente__documento",
        "expediente__paciente__historia_clinica",
        "entregado_por",
        "retirado_por",
        "servicio",
        "profesional",
    )
    list_filter = ("servicio", "fecha_prestamo", "fecha_devolucion")
    readonly_fields = ("fecha_prestamo", "fecha_devolucion")

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "expediente" and not request.user.is_superuser:
            try:
                membership = request.user.membresia_organizacion
            except Membresia.DoesNotExist:
                kwargs["queryset"] = ExpedienteFisico.objects.none()
            else:
                kwargs["queryset"] = ExpedienteFisico.objects.filter(
                    paciente__organizacion=membership.organizacion
                )
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        if request.user.is_superuser:
            return queryset
        try:
            membership = request.user.membresia_organizacion
        except Membresia.DoesNotExist:
            return queryset.none()
        return queryset.filter(expediente__paciente__organizacion=membership.organizacion)
