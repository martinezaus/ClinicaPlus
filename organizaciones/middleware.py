from .models import Membresia, Organizacion


class OrganizacionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.organizacion = None
        if request.user.is_authenticated:
            try:
                membresia = request.user.membresia_organizacion
            except Membresia.DoesNotExist:
                membresia = None

            if membresia and membresia.activa and membresia.organizacion.activa:
                request.organizacion = membresia.organizacion
            elif request.user.is_superuser:
                request.organizacion = Organizacion.objects.filter(activa=True).first()

        return self.get_response(request)
