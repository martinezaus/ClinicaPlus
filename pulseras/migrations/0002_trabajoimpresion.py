import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("pulseras", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="TrabajoImpresion",
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
                ("copias", models.PositiveSmallIntegerField()),
                (
                    "estado",
                    models.CharField(
                        choices=[
                            ("pending", "Pendiente"),
                            ("sent", "Enviado a la cola"),
                            ("error", "Error"),
                        ],
                        default="pending",
                        max_length=10,
                    ),
                ),
                ("error", models.TextField(blank=True)),
                ("creado_en", models.DateTimeField(auto_now_add=True)),
                (
                    "impresora",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="trabajos",
                        to="pulseras.impresorapulsera",
                    ),
                ),
                (
                    "solicitado_por",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="trabajos_impresion_pulsera",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "trabajo de impresión",
                "verbose_name_plural": "trabajos de impresión",
                "ordering": ("-creado_en",),
            },
        ),
    ]
