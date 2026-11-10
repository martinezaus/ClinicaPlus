import django.db.models.deletion
from django.db import migrations, models


def vincular_pacientes_existentes(apps, schema_editor):
    alias = schema_editor.connection.alias
    ExpedienteFisico = apps.get_model("archivo", "ExpedienteFisico")
    Paciente = apps.get_model("pacientes", "Paciente")
    vinculados = set()
    errores = []

    for expediente in ExpedienteFisico.objects.using(alias).all().iterator():
        pacientes_hc = []
        if expediente.numero_hc:
            pacientes_hc = list(
                Paciente.objects.using(alias).filter(
                    organizacion_id=expediente.organizacion_id,
                    historia_clinica=expediente.numero_hc,
                )[:2]
            )
        pacientes_documento = list(
            Paciente.objects.using(alias).filter(
                organizacion_id=expediente.organizacion_id,
                documento=expediente.dni,
            )[:2]
        )

        if len(pacientes_hc) > 1 or len(pacientes_documento) > 1:
            errores.append(f"expediente #{expediente.pk}: coincidencia ambigua")
            continue

        paciente_hc = pacientes_hc[0] if pacientes_hc else None
        paciente_documento = pacientes_documento[0] if pacientes_documento else None
        if paciente_hc and paciente_documento and paciente_hc.pk != paciente_documento.pk:
            errores.append(
                f"expediente #{expediente.pk}: historia clínica y documento apuntan a pacientes distintos"
            )
            continue

        paciente = paciente_hc or paciente_documento
        if paciente is None:
            errores.append(f"expediente #{expediente.pk}: no tiene paciente coincidente")
            continue
        if paciente.documento != expediente.dni:
            errores.append(f"expediente #{expediente.pk}: el documento no coincide")
            continue
        if expediente.numero_hc and paciente.historia_clinica != expediente.numero_hc:
            errores.append(f"expediente #{expediente.pk}: la historia clínica no coincide")
            continue
        if paciente.pk in vinculados:
            errores.append(f"expediente #{expediente.pk}: el paciente ya está vinculado a otro expediente")
            continue

        expediente.paciente_id = paciente.pk
        expediente.save(using=alias, update_fields=["paciente"])
        vinculados.add(paciente.pk)

    if errores:
        ejemplos = "; ".join(errores[:20])
        raise RuntimeError(
            "No se pudieron vincular todos los expedientes con seguridad. "
            "Corregí las coincidencias y volvé a ejecutar la migración. "
            f"Problemas: {ejemplos}"
        )


class Migration(migrations.Migration):

    dependencies = [
        ("archivo", "0005_expedientefisico_archivo"),
        ("pacientes", "0007_historia_clinica_opcional"),
    ]

    operations = [
        migrations.AddField(
            model_name="expedientefisico",
            name="paciente",
            field=models.OneToOneField(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="expediente_fisico",
                to="pacientes.paciente",
            ),
        ),
        migrations.RunPython(vincular_pacientes_existentes, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="expedientefisico",
            name="paciente",
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="expediente_fisico",
                to="pacientes.paciente",
            ),
        ),
        migrations.RemoveConstraint(
            model_name="expedientefisico",
            name="expediente_hc_unico_por_organizacion",
        ),
        migrations.AlterField(
            model_name="expedientefisico",
            name="archivo",
            field=models.CharField(
                choices=[("A", "Archivo Activo"), ("P", "Archivo Pasivo")],
                default="A",
                max_length=1,
                verbose_name="archivo",
            ),
        ),
        migrations.RemoveField(model_name="expedientefisico", name="organizacion"),
        migrations.RemoveField(model_name="expedientefisico", name="dni"),
        migrations.RemoveField(model_name="expedientefisico", name="numero_hc"),
        migrations.RemoveField(model_name="expedientefisico", name="apellido_nombre"),
        migrations.AlterModelOptions(
            name="expedientefisico",
            options={
                "ordering": ("paciente__apellido_nombre",),
                "verbose_name": "expediente físico",
                "verbose_name_plural": "expedientes físicos",
            },
        ),
    ]
