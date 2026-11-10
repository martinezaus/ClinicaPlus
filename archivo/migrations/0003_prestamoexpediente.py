import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("archivo", "0002_ubicacion_estructurada"),
    ]

    operations = [
        migrations.CreateModel(
            name="PrestamoExpediente",
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
                ("entregado_por", models.CharField(max_length=120, verbose_name="entregado por")),
                ("retirado_por", models.CharField(max_length=120, verbose_name="retirado por")),
                ("servicio", models.CharField(max_length=120, verbose_name="servicio solicitante")),
                (
                    "profesional",
                    models.CharField(
                        max_length=120,
                        verbose_name="Dr./Dra. para quien se solicita",
                    ),
                ),
                ("fecha_prestamo", models.DateTimeField(auto_now_add=True)),
                ("fecha_devolucion", models.DateTimeField(blank=True, null=True)),
                (
                    "expediente",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="prestamos",
                        to="archivo.expedientefisico",
                    ),
                ),
            ],
            options={
                "verbose_name": "préstamo de expediente",
                "verbose_name_plural": "préstamos de expedientes",
                "ordering": ("-fecha_prestamo",),
                "constraints": [
                    models.UniqueConstraint(
                        condition=models.Q(("fecha_devolucion__isnull", True)),
                        fields=("expediente",),
                        name="un_solo_prestamo_activo_por_expediente",
                    )
                ],
            },
        ),
    ]
