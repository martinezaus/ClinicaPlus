from django.db import models
from django.db.models import Q

class Paciente(models.Model):
    id = models.AutoField(primary_key=True)  # ID del HIS
    apellido_nombre = models.CharField(max_length=120)
    documento = models.CharField(max_length=10, blank=True, db_index=True)
    fecha_nacimiento = models.DateField(blank=True, null=True)
    historia_clinica = models.CharField(max_length=20, blank=True)
    alergias = models.CharField(max_length=200, blank=True)
    organizacion = models.ForeignKey(
        "organizaciones.Organizacion",
        on_delete=models.PROTECT,
        related_name="pacientes",
    )


    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("organizacion", "historia_clinica", "documento", "apellido_nombre"),
                condition=~Q(historia_clinica=""),
                name="paciente_hc_unica_por_organizacion",
            )
        ]


    def __str__(self):
        return f"{self.apellido_nombre} — {self.documento}"
