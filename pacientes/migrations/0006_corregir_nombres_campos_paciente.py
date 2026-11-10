from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("pacientes", "0005_organizacion_y_hc_por_organizacion"),
    ]

    operations = [
        migrations.RenameField(
            model_name="paciente",
            old_name="fecha_naciemiento",
            new_name="fecha_nacimiento",
        ),
        migrations.RenameField(
            model_name="paciente",
            old_name="historio_clinica",
            new_name="historia_clinica",
        ),
    ]
