import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


def crear_organizacion_principal(apps, schema_editor):
    Organizacion = apps.get_model("organizaciones", "Organizacion")
    Organizacion.objects.using(schema_editor.connection.alias).get_or_create(
        identificador="organizacion-principal",
        defaults={"nombre": "Organización principal", "activa": True},
    )


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Organizacion",
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
                ("nombre", models.CharField(max_length=160)),
                ("identificador", models.SlugField(max_length=100, unique=True)),
                ("activa", models.BooleanField(default=True)),
                ("creada_en", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "verbose_name": "organización",
                "verbose_name_plural": "organizaciones",
                "ordering": ("nombre",),
            },
        ),
        migrations.CreateModel(
            name="Membresia",
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
                    "perfil",
                    models.CharField(
                        choices=[
                            ("administrativo", "Administrativo"),
                            ("medico", "Médico"),
                            ("enfermero", "Enfermero"),
                            ("legal", "Legal"),
                        ],
                        max_length=20,
                    ),
                ),
                ("activa", models.BooleanField(default=True)),
                (
                    "organizacion",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="membresias",
                        to="organizaciones.organizacion",
                    ),
                ),
                (
                    "usuario",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="membresia_organizacion",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "membresía de usuario",
                "verbose_name_plural": "membresías de usuarios",
            },
        ),
        migrations.RunPython(crear_organizacion_principal, migrations.RunPython.noop),
    ]
