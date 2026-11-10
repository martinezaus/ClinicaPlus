from django.contrib import admin

from organizaciones.models import Membresia
from .models import ImpresoraPulsera, PerfilMedioPulsera, TrabajoImpresion


class PerfilMedioPulseraInline(admin.TabularInline):
    model = PerfilMedioPulsera
    extra = 0


@admin.register(ImpresoraPulsera)
class ImpresoraPulseraAdmin(admin.ModelAdmin):
    list_display = ("nombre", "modelo", "driver", "servicio", "cola_sistema", "activa")
    list_filter = ("driver", "servicio", "activa")
    search_fields = ("nombre", "modelo", "servicio", "cola_sistema")
    inlines = (PerfilMedioPulseraInline,)

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
        if not request.user.is_superuser:
            obj.organizacion = request.user.membresia_organizacion.organizacion
        super().save_model(request, obj, form, change)


@admin.register(TrabajoImpresion)
class TrabajoImpresionAdmin(admin.ModelAdmin):
    list_display = ("creado_en", "impresora", "tipo", "copias", "estado", "solicitado_por")
    list_filter = ("estado", "tipo", "impresora", "creado_en")
    search_fields = ("impresora__nombre", "error", "solicitado_por__username")
    readonly_fields = (
        "impresora",
        "tipo",
        "copias",
        "estado",
        "error",
        "solicitado_por",
        "creado_en",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        if request.user.is_superuser:
            return queryset
        try:
            membership = request.user.membresia_organizacion
        except Membresia.DoesNotExist:
            return queryset.none()
        return queryset.filter(impresora__organizacion=membership.organizacion)
