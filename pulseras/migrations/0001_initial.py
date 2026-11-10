from django.db import migrations, models
import django.db.models.deletion


def crear_impresoras_base(apps, schema_editor):
    Impresora = apps.get_model("pulseras", "ImpresoraPulsera")
    Impresora.objects.using(schema_editor.connection.alias).bulk_create(
        (
            Impresora(
                nombre="Zebra Guardia Adulto",
                modelo="Zebra (modelo por confirmar)",
                driver="zpl",
                servicio="Guardia adultos",
                activa=False,
            ),
            Impresora(
                nombre="Zebra Guardia Pediátrica",
                modelo="Zebra (modelo por confirmar)",
                driver="zpl",
                servicio="Guardia pediátrica",
                activa=False,
            ),
            Impresora(
                nombre="TSC TDP-225 Pediatría",
                modelo="TSC TDP-225",
                driver="tspl",
                servicio="Pabellón de pediatría",
                dpi=203,
                activa=False,
            ),
        )
    )


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="ImpresoraPulsera",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("nombre", models.CharField(max_length=100)),
                ("modelo", models.CharField(max_length=100)),
                (
                    "driver",
                    models.CharField(
                        choices=[("zpl", "Zebra / ZPL"), ("tspl", "TSC / TSPL")],
                        max_length=8,
                    ),
                ),
                (
                    "cola_sistema",
                    models.CharField(
                        blank=True,
                        help_text="Debe coincidir con el nombre que muestra Windows en Impresoras y escáneres.",
                        max_length=160,
                        verbose_name="nombre exacto de impresora en Windows",
                    ),
                ),
                ("servicio", models.CharField(blank=True, max_length=100)),
                (
                    "dpi",
                    models.PositiveSmallIntegerField(
                        default=203,
                        help_text="Resolución configurada para el modelo.",
                    ),
                ),
                ("activa", models.BooleanField(default=False)),
            ],
            options={
                "verbose_name": "impresora de pulseras",
                "verbose_name_plural": "impresoras de pulseras",
                "ordering": ("servicio", "nombre"),
            },
        ),
        migrations.CreateModel(
            name="PerfilMedioPulsera",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "tipo",
                    models.CharField(
                        choices=[("adulto", "Adulto"), ("pediatrico", "Pediátrico")],
                        max_length=12,
                    ),
                ),
                (
                    "ancho_mm",
                    models.DecimalField(
                        decimal_places=1,
                        help_text="Ancho de la pulsera montada en la impresora.",
                        max_digits=6,
                        verbose_name="ancho de impresión (mm)",
                    ),
                ),
                (
                    "largo_mm",
                    models.DecimalField(
                        decimal_places=1,
                        help_text="Largo de cada pulsera / etiqueta en dirección de avance.",
                        max_digits=6,
                        verbose_name="largo de etiqueta (mm)",
                    ),
                ),
                (
                    "sensor",
                    models.CharField(
                        choices=[
                            ("gap", "Separación / gap"),
                            ("black_mark", "Marca negra"),
                            ("continuous", "Continuo"),
                        ],
                        default="gap",
                        max_length=12,
                    ),
                ),
                (
                    "separacion_mm",
                    models.DecimalField(
                        decimal_places=1,
                        default=2,
                        help_text="Distancia entre pulseras; no se usa en modo continuo.",
                        max_digits=5,
                        verbose_name="separación o marca (mm)",
                    ),
                ),
                (
                    "rotacion",
                    models.PositiveSmallIntegerField(
                        choices=[(0, "0°"), (90, "90°")],
                        default=90,
                    ),
                ),
                ("oscuridad", models.PositiveSmallIntegerField(default=8)),
                ("velocidad", models.PositiveSmallIntegerField(default=4)),
                (
                    "desplazamiento_mm",
                    models.DecimalField(
                        decimal_places=1,
                        default=0,
                        max_digits=5,
                        verbose_name="desplazamiento vertical (mm)",
                    ),
                ),
                (
                    "impresora",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="perfiles",
                        to="pulseras.impresorapulsera",
                    ),
                ),
            ],
            options={
                "verbose_name": "perfil de cinta",
                "verbose_name_plural": "perfiles de cintas",
                "ordering": ("tipo",),
                "constraints": [
                    models.UniqueConstraint(
                        fields=("impresora", "tipo"),
                        name="un_perfil_por_tipo_e_impresora",
                    ),
                    models.CheckConstraint(
                        condition=models.Q(("ancho_mm__gt", 0)),
                        name="ancho_medio_pulsera_positivo",
                    ),
                    models.CheckConstraint(
                        condition=models.Q(("largo_mm__gt", 0)),
                        name="largo_medio_pulsera_positivo",
                    ),
                ],
            },
        ),
        migrations.RunPython(crear_impresoras_base, migrations.RunPython.noop),
    ]
