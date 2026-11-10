from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("pacientes", "0008_remove_paciente_paciente_hc_unica_por_organizacion_and_more"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="paciente",
            name="area",
        ),
    ]
