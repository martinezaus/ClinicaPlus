from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied

from .models import Membresia


def requiere_modulo(modulo):
    def decorator(view_func):
        @login_required
        @wraps(view_func)
        def wrapped(request, *args, **kwargs):
            if request.user.is_superuser:
                if request.organizacion is None:
                    raise PermissionDenied("No hay una organización activa configurada.")
            else:
                try:
                    membresia = request.user.membresia_organizacion
                except Membresia.DoesNotExist:
                    raise PermissionDenied("El usuario no tiene un perfil de organización activo.")
                if not membresia.puede_acceder(modulo):
                    raise PermissionDenied("Tu perfil no tiene acceso a este módulo.")
                request.organizacion = membresia.organizacion
            return view_func(request, *args, **kwargs)

        return wrapped

    return decorator
