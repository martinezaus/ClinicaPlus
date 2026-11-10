from django.db import migrations, models
from django.db.models import Q


class Migration(migrations.Migration):

    dependencies = [
        ("pacientes", "0006_corregir_nombres_campos_paciente"),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name="paciente",
            name="paciente_hc_unica_por_organizacion",
        ),
        migrations.AlterField(
            model_name="paciente",
            name="historia_clinica",
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AddConstraint(
            model_name="paciente",
            constraint=models.UniqueConstraint(
                condition=~Q(historia_clinica=""),
                fields=("organizacion", "historia_clinica"),
                name="paciente_hc_unica_por_organizacion",
            ),
        ),
    ]
