from django.core.exceptions import ValidationError
from django.conf import settings
from django.db import models


class ImpresoraPulsera(models.Model):
    DRIVER_CHOICES = (
        ("zpl", "Zebra / ZPL"),
        ("tspl", "TSC / TSPL"),
    )

    nombre = models.CharField(max_length=100)
    organizacion = models.ForeignKey(
        "organizaciones.Organizacion",
        on_delete=models.PROTECT,
        related_name="impresoras_pulsera",
    )
    modelo = models.CharField(max_length=100)
    driver = models.CharField(max_length=8, choices=DRIVER_CHOICES)
    cola_sistema = models.CharField(
        "nombre exacto de impresora en Windows",
        max_length=160,
        blank=True,
        help_text="Debe coincidir con el nombre que muestra Windows en Impresoras y escáneres.",
    )
    servicio = models.CharField(max_length=100, blank=True)
    dpi = models.PositiveSmallIntegerField(
        default=203,
        help_text="Resolución configurada para el modelo.",
    )
    activa = models.BooleanField(default=False)

    class Meta:
        ordering = ("servicio", "nombre")
        verbose_name = "impresora de pulseras"
        verbose_name_plural = "impresoras de pulseras"

    def __str__(self):
        return self.nombre


class PerfilMedioPulsera(models.Model):
    TIPO_CHOICES = (
        ("adulto", "Adulto"),
        ("pediatrico", "Pediátrico"),
    )
    SENSOR_CHOICES = (
        ("gap", "Separación / gap"),
        ("black_mark", "Marca negra"),
        ("continuous", "Continuo"),
    )
    ROTATION_CHOICES = (
        (0, "0°"),
        (90, "90°"),
    )

    impresora = models.ForeignKey(
        ImpresoraPulsera,
        on_delete=models.CASCADE,
        related_name="perfiles",
    )
    tipo = models.CharField(max_length=12, choices=TIPO_CHOICES)
    ancho_mm = models.DecimalField(
        "ancho de impresión (mm)",
        max_digits=6,
        decimal_places=1,
        help_text="Ancho de la pulsera montada en la impresora.",
    )
    largo_mm = models.DecimalField(
        "largo de etiqueta (mm)",
        max_digits=6,
        decimal_places=1,
        help_text="Largo de cada pulsera / etiqueta en dirección de avance.",
    )
    sensor = models.CharField(
        max_length=12,
        choices=SENSOR_CHOICES,
        default="gap",
    )
    separacion_mm = models.DecimalField(
        "separación o marca (mm)",
        max_digits=5,
        decimal_places=1,
        default=2,
        help_text="Distancia entre pulseras; no se usa en modo continuo.",
    )
    rotacion = models.PositiveSmallIntegerField(
        choices=ROTATION_CHOICES,
        default=90,
    )
    oscuridad = models.PositiveSmallIntegerField(default=8)
    velocidad = models.PositiveSmallIntegerField(default=4)
    desplazamiento_mm = models.DecimalField(
        "desplazamiento vertical (mm)",
        max_digits=5,
        decimal_places=1,
        default=0,
    )

    class Meta:
        ordering = ("tipo",)
        constraints = [
            models.UniqueConstraint(
                fields=("impresora", "tipo"),
                name="un_perfil_por_tipo_e_impresora",
            ),
            models.CheckConstraint(
                condition=models.Q(ancho_mm__gt=0),
                name="ancho_medio_pulsera_positivo",
            ),
            models.CheckConstraint(
                condition=models.Q(largo_mm__gt=0),
                name="largo_medio_pulsera_positivo",
            ),
        ]
        verbose_name = "perfil de cinta"
        verbose_name_plural = "perfiles de cintas"

    def clean(self):
        super().clean()
        if self.impresora_id and self.impresora.driver == "tspl" and self.oscuridad > 15:
            raise ValidationError(
                {"oscuridad": "La densidad TSPL debe estar entre 0 y 15."}
            )
        if self.impresora_id and self.impresora.driver == "zpl" and self.oscuridad > 30:
            raise ValidationError(
                {"oscuridad": "La oscuridad ZPL debe estar entre 0 y 30."}
            )
        if self.separacion_mm is not None and self.separacion_mm < 0:
            raise ValidationError(
                {"separacion_mm": "La separación no puede ser negativa."}
            )

    def __str__(self):
        return f"{self.impresora} — {self.get_tipo_display()}"


class TrabajoImpresion(models.Model):
    STATUS_CHOICES = (
        ("pending", "Pendiente"),
        ("sent", "Enviado a la cola"),
        ("error", "Error"),
    )

    impresora = models.ForeignKey(
        ImpresoraPulsera,
        on_delete=models.PROTECT,
        related_name="trabajos",
    )
    tipo = models.CharField(max_length=12, choices=PerfilMedioPulsera.TIPO_CHOICES)
    copias = models.PositiveSmallIntegerField()
    estado = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default="pending",
    )
    error = models.TextField(blank=True)
    solicitado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="trabajos_impresion_pulsera",
    )
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-creado_en",)
        verbose_name = "trabajo de impresión"
        verbose_name_plural = "trabajos de impresión"

    def __str__(self):
        return f"{self.get_tipo_display()} — {self.impresora} — {self.creado_en:%Y-%m-%d %H:%M}"
