from django.contrib import admin
from organizaciones.models import Membresia
from .models import Paciente


@admin.register(Paciente)
class PacienteAdmin(admin.ModelAdmin):
    list_display = ("apellido_nombre", "documento", "historia_clinica")
    search_fields = ("apellido_nombre", "documento", "historia_clinica")

    def get_exclude(self, request, obj=None):
        return ("organizacion",) if not request.user.is_superuser else ()

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        if request.user.is_superuser:
            return queryset
        try:
            membership = request.user.membresia_organizacion
        except Membresia.DoesNotExist:
            return queryset.none()
        return queryset.filter(organizacion=membership.organizacion)

    def save_model(self, request, obj, form, change):
        if not change and not request.user.is_superuser:
            obj.organizacion = request.user.membresia_organizacion.organizacion
        super().save_model(request, obj, form, change)
