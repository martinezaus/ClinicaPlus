import django.db.models.deletion
from django.db import migrations, models


def asignar_organizacion_existente(apps, schema_editor):
    Organizacion = apps.get_model("organizaciones", "Organizacion")
    Paciente = apps.get_model("pacientes", "Paciente")
    organizacion = Organizacion.objects.using(schema_editor.connection.alias).get(
        identificador="organizacion-principal"
    )
    Paciente.objects.using(schema_editor.connection.alias).filter(
        organizacion__isnull=True
    ).update(organizacion=organizacion)


class Migration(migrations.Migration):

    dependencies = [
        ("organizaciones", "0001_initial"),
        ("pacientes", "0004_remove_legacy_printer_models"),
    ]

    operations = [
        migrations.AddField(
            model_name="paciente",
            name="organizacion",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="pacientes",
                to="organizaciones.organizacion",
            ),
        ),
        migrations.RunPython(asignar_organizacion_existente, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="paciente",
            name="organizacion",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="pacientes",
                to="organizaciones.organizacion",
            ),
        ),
        migrations.AlterField(
            model_name="paciente",
            name="historio_clinica",
            field=models.CharField(max_length=20),
        ),
        migrations.AddConstraint(
            model_name="paciente",
            constraint=models.UniqueConstraint(
                fields=("organizacion", "historio_clinica"),
                name="paciente_hc_unica_por_organizacion",
            ),
        ),
    ]
