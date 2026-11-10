import django.db.models.deletion
from django.db import migrations, models


def asignar_organizacion_existente(apps, schema_editor):
    Organizacion = apps.get_model("organizaciones", "Organizacion")
    ImpresoraPulsera = apps.get_model("pulseras", "ImpresoraPulsera")
    organizacion = Organizacion.objects.using(schema_editor.connection.alias).get(
        identificador="organizacion-principal"
    )
    ImpresoraPulsera.objects.using(schema_editor.connection.alias).filter(
        organizacion__isnull=True
    ).update(organizacion=organizacion)


class Migration(migrations.Migration):

    dependencies = [
        ("organizaciones", "0001_initial"),
        ("pulseras", "0002_trabajoimpresion"),
    ]

    operations = [
        migrations.AddField(
            model_name="impresorapulsera",
            name="organizacion",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="impresoras_pulsera",
                to="organizaciones.organizacion",
            ),
        ),
        migrations.RunPython(asignar_organizacion_existente, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="impresorapulsera",
            name="organizacion",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="impresoras_pulsera",
                to="organizaciones.organizacion",
            ),
        ),
    ]
