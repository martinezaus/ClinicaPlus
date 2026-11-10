from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("pacientes", "0003_printer_calibrationprofile_printjob"),
    ]

    operations = [
        migrations.DeleteModel(name="PrintJob"),
        migrations.DeleteModel(name="CalibrationProfile"),
        migrations.DeleteModel(name="Printer"),
    ]
