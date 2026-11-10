from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="ExpedienteFisico",
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
                ("dni", models.CharField(db_index=True, max_length=20)),
                (
                    "numero_hc",
                    models.CharField(
                        blank=True,
                        db_index=True,
                        max_length=30,
                        null=True,
                        verbose_name="número interno de historia clínica",
                    ),
                ),
                (
                    "apellido_nombre",
                    models.CharField(max_length=120, verbose_name="apellido y nombre"),
                ),
                (
                    "ubicacion",
                    models.CharField(
                        blank=True,
                        help_text="Por ejemplo: pabellón, estante, caja o sector.",
                        max_length=120,
                        verbose_name="ubicación física",
                    ),
                ),
            ],
            options={
                "verbose_name": "expediente físico",
                "verbose_name_plural": "expedientes físicos",
                "ordering": ("apellido_nombre",),
            },
        ),
    ]
