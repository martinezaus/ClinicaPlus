from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("archivo", "0001_initial"),
    ]

    operations = [
        migrations.RenameField(
            model_name="expedientefisico",
            old_name="ubicacion",
            new_name="referencia_ubicacion",
        ),
        migrations.AlterField(
            model_name="expedientefisico",
            name="referencia_ubicacion",
            field=models.CharField(
                blank=True,
                help_text="Dato adicional para conservar o aclarar una ubicación.",
                max_length=120,
                verbose_name="otra referencia de ubicación",
            ),
        ),
        migrations.AddField(
            model_name="expedientefisico",
            name="pasillo",
            field=models.CharField(blank=True, max_length=80, verbose_name="pasillo"),
        ),
        migrations.AddField(
            model_name="expedientefisico",
            name="estanteria",
            field=models.CharField(blank=True, max_length=80, verbose_name="estantería"),
        ),
        migrations.AddField(
            model_name="expedientefisico",
            name="estante",
            field=models.CharField(blank=True, max_length=80, verbose_name="estante / nivel"),
        ),
    ]
