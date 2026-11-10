import django.db.models.deletion
from django.db import migrations, models
from django.db.models import Q


def asignar_organizacion_existente(apps, schema_editor):
    Organizacion = apps.get_model("organizaciones", "Organizacion")
    ExpedienteFisico = apps.get_model("archivo", "ExpedienteFisico")
    organizacion = Organizacion.objects.using(schema_editor.connection.alias).get(
        identificador="organizacion-principal"
    )
    ExpedienteFisico.objects.using(schema_editor.connection.alias).filter(
        organizacion__isnull=True
    ).update(organizacion=organizacion)


class Migration(migrations.Migration):

    dependencies = [
        ("archivo", "0003_prestamoexpediente"),
        ("organizaciones", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="expedientefisico",
            name="organizacion",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="expedientes_fisicos",
                to="organizaciones.organizacion",
            ),
        ),
        migrations.RunPython(asignar_organizacion_existente, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="expedientefisico",
            name="organizacion",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="expedientes_fisicos",
                to="organizaciones.organizacion",
            ),
        ),
        migrations.AddConstraint(
            model_name="expedientefisico",
            constraint=models.UniqueConstraint(
                condition=Q(numero_hc__isnull=False) & ~Q(numero_hc=""),
                fields=("organizacion", "numero_hc"),
                name="expediente_hc_unico_por_organizacion",
            ),
        ),
    ]
