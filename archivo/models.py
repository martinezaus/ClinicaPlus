from django.db import models
from django.db.models import Q
from django.utils import timezone


class ExpedienteFisico(models.Model):
    paciente = models.OneToOneField(
        "pacientes.Paciente",
        on_delete=models.PROTECT,
        related_name="expediente_fisico",
    )
    archivo = models.CharField(
        "archivo",
        max_length=1,
        choices=[("A", "Archivo Activo"), ("P", "Archivo Pasivo"), ("D", "Desaparecida")],
        default="A",
    )
    pasillo = models.CharField("pasillo", max_length=80, blank=True)
    estanteria = models.CharField("estantería", max_length=80, blank=True)
    estante = models.CharField("estante / nivel", max_length=80, blank=True)
    referencia_ubicacion = models.CharField(
        "otra referencia de ubicación",
        max_length=120,
        blank=True,
        help_text="Dato adicional para conservar o aclarar una ubicación.",
    )

    class Meta:
        ordering = ("paciente__apellido_nombre",)
        verbose_name = "expediente físico"
        verbose_name_plural = "expedientes físicos"

    def __str__(self):
        identificador = self.paciente.historia_clinica or self.paciente.documento
        return f"{self.paciente.apellido_nombre} — {identificador}"

    @property
    def ubicacion_completa(self):
        partes = [
            f"Archivo {self.archivo}" if self.archivo else "",
            f"Pasillo {self.pasillo}" if self.pasillo else "",
            f"Estantería {self.estanteria}" if self.estanteria else "",
            f"Estante {self.estante}" if self.estante else "",
            self.referencia_ubicacion,
        ]
        return " · ".join(parte for parte in partes if parte)


class PrestamoExpediente(models.Model):
    expediente = models.ForeignKey(
        ExpedienteFisico,
        on_delete=models.PROTECT,
        related_name="prestamos",
    )
    entregado_por = models.CharField("entregado por", max_length=120)
    retirado_por = models.CharField("retirado por", max_length=120)
    servicio = models.CharField("servicio solicitante", max_length=120)
    profesional = models.CharField("Dr./Dra. para quien se solicita", max_length=120)
    fecha_prestamo = models.DateTimeField(auto_now_add=True)
    fecha_devolucion = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ("-fecha_prestamo",)
        constraints = [
            models.UniqueConstraint(
                fields=("expediente",),
                condition=Q(fecha_devolucion__isnull=True),
                name="un_solo_prestamo_activo_por_expediente",
            )
        ]
        verbose_name = "préstamo de expediente"
        verbose_name_plural = "préstamos de expedientes"

    def __str__(self):
        return f"{self.expediente} — {self.servicio}"

    @property
    def dias_prestado(self):
        fecha_fin = self.fecha_devolucion or timezone.now()
        return max((fecha_fin.date() - self.fecha_prestamo.date()).days, 0)

    @property
    def ultima_actividad(self):
        return self.fecha_devolucion or self.fecha_prestamo
