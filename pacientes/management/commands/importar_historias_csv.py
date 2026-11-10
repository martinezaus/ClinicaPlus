import csv
import re
from collections import defaultdict
from contextlib import nullcontext
from datetime import datetime

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from archivo.models import ExpedienteFisico
from organizaciones.models import Organizacion
from pacientes.models import Paciente


def normalizar_nombre(value):
    return re.sub(r"\s+", " ", (value or "").strip()).casefold()


def normalizar_documento(value):
    value = (value or "").strip()
    return "" if not value or re.fullmatch(r"0+", value) else value


def parsear_fecha(value):
    value = (value or "").strip()
    if not value:
        return None
    for formato in ("%m/%d/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(value, formato).date()
        except ValueError:
            pass
    raise ValueError("fecha no reconocida")


class Command(BaseCommand):
    help = "Importa pacientes y estados de archivo desde HISTORIA_1.csv."

    def add_arguments(self, parser):
        parser.add_argument("archivo_csv")
        parser.add_argument("--organizacion", default="organizacion-principal")
        parser.add_argument(
            "--commit",
            action="store_true",
            help="Guarda cambios. Sin esta opción solo muestra una vista previa.",
        )

    def handle(self, *args, **options):
        try:
            organizacion = Organizacion.objects.get(identificador=options["organizacion"])
        except Organizacion.DoesNotExist as exc:
            raise CommandError("No existe la organización indicada.") from exc

        grupos = defaultdict(list)
        errores = defaultdict(int)
        ruta = options["archivo_csv"]
        try:
            with open(ruta, encoding="utf-8-sig", newline="") as fuente:
                reader = csv.DictReader(fuente)
                requeridas = {"DNI", "HC", "Apellido y Nombre", "Archivo", "FNAC"}
                if not reader.fieldnames or not requeridas.issubset(reader.fieldnames):
                    raise CommandError("El CSV no contiene todas las columnas requeridas.")
                for numero_fila, fila in enumerate(reader, start=2):
                    nombre = re.sub(r"\s+", " ", (fila.get("Apellido y Nombre") or "").strip())
                    documento = normalizar_documento(fila.get("DNI"))
                    hc = (fila.get("HC") or "").strip()
                    estado = (fila.get("Archivo") or "").strip().upper()
                    try:
                        fecha = parsear_fecha(fila.get("FNAC"))
                    except ValueError:
                        errores["fecha no válida"] += 1
                        continue
                    if not nombre:
                        errores["sin nombre"] += 1
                        continue
                    if estado not in {"A", "P", "D"}:
                        errores["estado vacío o no reconocido"] += 1
                        continue
                    if not hc:
                        errores["sin HC"] += 1
                        continue
                    clave = (normalizar_nombre(nombre), documento, hc)
                    grupos[clave].append(
                        {"nombre": nombre, "documento": documento, "hc": hc,
                         "estado": estado, "fecha": fecha, "fila": numero_fila}
                    )
        except OSError as exc:
            raise CommandError("No se pudo leer el archivo CSV indicado.") from exc

        pacientes = list(Paciente.objects.filter(organizacion=organizacion))
        por_clave = {
            (normalizar_nombre(p.apellido_nombre), p.documento, p.historia_clinica): p
            for p in pacientes
        }
        preparados = []
        conflictos_estado = 0
        conflictos_fecha = 0
        duplicados = 0
        for clave, filas in grupos.items():
            duplicados += len(filas) - 1
            estados = {fila["estado"] for fila in filas}
            fechas = {fila["fecha"] for fila in filas if fila["fecha"] is not None}
            if len(estados) != 1:
                conflictos_estado += 1
                continue
            if len(fechas) > 1:
                conflictos_fecha += 1
                fecha = None
            else:
                fecha = next(iter(fechas), None)
            preparado = (clave, filas[0], next(iter(estados)), fecha)
            preparados.append(preparado)

        nuevos = existentes = 0
        pacientes_nuevos = []
        pacientes_actualizados = []
        expedientes_nuevos = []
        expedientes_actualizados = []
        expedientes_por_paciente = {
            expediente.paciente_id: expediente
            for expediente in ExpedienteFisico.objects.filter(
                paciente__organizacion=organizacion
            )
        }
        for clave, fila, estado, fecha in preparados:
            paciente = por_clave.get(clave)
            if paciente:
                existentes += 1
            else:
                nuevos += 1
                paciente = Paciente(
                    organizacion=organizacion,
                    apellido_nombre=fila["nombre"],
                    documento=fila["documento"],
                    historia_clinica=fila["hc"],
                )
                pacientes_nuevos.append(paciente)
            # Preserve a previously recorded date if the source has conflicting dates.
            if fecha is not None:
                paciente.fecha_nacimiento = fecha
            paciente.apellido_nombre = paciente.apellido_nombre or fila["nombre"]
            paciente.documento = fila["documento"]
            paciente.historia_clinica = fila["hc"]
            if paciente.pk:
                pacientes_actualizados.append(paciente)
            por_clave[clave] = paciente

            expediente = expedientes_por_paciente.get(paciente.pk) if paciente.pk else None
            if expediente:
                expediente.archivo = estado
                expedientes_actualizados.append(expediente)
            else:
                expedientes_nuevos.append((paciente, estado))

        contexto = transaction.atomic() if options["commit"] else nullcontext()
        with contexto:
            if options["commit"]:
                Paciente.objects.bulk_create(pacientes_nuevos, batch_size=1000)
                Paciente.objects.bulk_update(
                    pacientes_actualizados,
                    ("apellido_nombre", "documento", "historia_clinica", "fecha_nacimiento"),
                    batch_size=1000,
                )
                ExpedienteFisico.objects.bulk_update(
                    expedientes_actualizados, ("archivo",), batch_size=1000
                )
                ExpedienteFisico.objects.bulk_create(
                    [ExpedienteFisico(paciente=paciente, archivo=estado)
                     for paciente, estado in expedientes_nuevos],
                    batch_size=1000,
                )

        self.stdout.write("Vista previa" if not options["commit"] else "Importación completada")
        self.stdout.write(f"Grupos de identidad listos: {len(preparados)}")
        self.stdout.write(f"Pacientes nuevos: {nuevos}")
        self.stdout.write(f"Pacientes existentes: {existentes}")
        self.stdout.write(f"Filas repetidas consolidadas: {duplicados}")
        self.stdout.write(f"Identidades apartadas por estado contradictorio: {conflictos_estado}")
        self.stdout.write(f"Identidades con fecha contradictoria (se conservaría sin fecha nueva): {conflictos_fecha}")
        for motivo, cantidad in sorted(errores.items()):
            self.stdout.write(f"Filas apartadas ({motivo}): {cantidad}")
        if not options["commit"]:
            self.stdout.write("No se guardaron cambios. Para importar, volver a ejecutar con --commit.")
