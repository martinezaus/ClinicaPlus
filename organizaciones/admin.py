from django.contrib import admin

from .models import Membresia, Organizacion


@admin.register(Organizacion)
class OrganizacionAdmin(admin.ModelAdmin):
    list_display = ("nombre", "identificador", "activa")
    search_fields = ("nombre", "identificador")
    list_filter = ("activa",)
    fields = ("nombre", "identificador", "logo", "activa")

    def has_module_permission(self, request):
        return request.user.is_superuser


@admin.register(Membresia)
class MembresiaAdmin(admin.ModelAdmin):
    list_display = ("usuario", "organizacion", "perfil", "activa")
    list_filter = ("perfil", "organizacion", "activa")
    search_fields = ("usuario__username", "usuario__first_name", "usuario__last_name")
    autocomplete_fields = ("usuario", "organizacion")

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        if request.user.is_superuser:
            return queryset
        try:
            membership = request.user.membresia_organizacion
        except Membresia.DoesNotExist:
            return queryset.none()
        return queryset.filter(organizacion=membership.organizacion)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "organizacion" and not request.user.is_superuser:
            try:
                membership = request.user.membresia_organizacion
            except Membresia.DoesNotExist:
                kwargs["queryset"] = Organizacion.objects.none()
            else:
                kwargs["queryset"] = Organizacion.objects.filter(
                    pk=membership.organizacion_id
                )
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def save_model(self, request, obj, form, change):
        if not request.user.is_superuser:
            obj.organizacion = request.user.membresia_organizacion.organizacion
        super().save_model(request, obj, form, change)
