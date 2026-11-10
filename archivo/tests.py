from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from organizaciones.models import Membresia, Organizacion
from .models import ExpedienteFisico, PrestamoExpediente
from pacientes.models import Paciente


class BusquedaExpedienteTests(TestCase):
    def setUp(self):
        self.organizacion = Organizacion.objects.create(
            nombre="Hospital de prueba",
            identificador="hospital-prueba",
        )
        user = get_user_model().objects.create_user(
            username="archivo",
            password="clave-segura",
        )
        Membresia.objects.create(
            usuario=user,
            organizacion=self.organizacion,
            perfil="administrativo",
            modulos=["archivo"],
        )
        self.client.force_login(user)
        self.paciente_con_hc = Paciente.objects.create(
            organizacion=self.organizacion,
            documento="30123456",
            historia_clinica="HC-4521",
            apellido_nombre="Pérez, María",
            fecha_nacimiento="1990-04-20",
        )
        self.expediente_con_hc = ExpedienteFisico.objects.create(
            paciente=self.paciente_con_hc,
            pasillo="A",
            estanteria="3",
            estante="2",
        )
        self.paciente_sin_hc = Paciente.objects.create(
            organizacion=self.organizacion,
            documento="28987654",
            historia_clinica="",
            apellido_nombre="Gómez, Juan",
            fecha_nacimiento="1988-02-10",
        )
        ExpedienteFisico.objects.create(
            paciente=self.paciente_sin_hc,
        )

    def test_busca_por_dni(self):
        response = self.client.post(reverse("archivo:buscar"), {"identificador": "30123456"})

        self.assertContains(response, "Pérez, María")
        self.assertContains(response, "Pasillo A")
        self.assertContains(response, "Estantería 3")
        self.assertContains(response, "Estante 2")

    def test_no_devuelve_expedientes_de_otra_organizacion(self):
        otra = Organizacion.objects.create(
            nombre="Otro hospital",
            identificador="otro-hospital",
        )
        paciente_otra = Paciente.objects.create(
            organizacion=otra,
            documento="99999999",
            historia_clinica="HC-999",
            apellido_nombre="Paciente de otra organización",
            fecha_nacimiento="1990-04-20",
        )
        ExpedienteFisico.objects.create(
            paciente=paciente_otra,
        )

        response = self.client.post(
            reverse("archivo:buscar"),
            {"identificador": "99999999"},
        )

        self.assertContains(response, "No encontramos coincidencias.")
        self.assertNotContains(response, "Paciente de otra organización")

    def test_busca_por_numero_interno(self):
        response = self.client.post(reverse("archivo:buscar"), {"identificador": "HC-4521"})

        self.assertContains(response, "Pérez, María")

    def test_busca_por_nombre_y_ofrece_abrir_ficha(self):
        response = self.client.post(
            reverse("archivo:buscar"),
            {"identificador": "Pérez"},
        )

        self.assertContains(response, "Pérez, María")
        self.assertContains(response, "Abrir ficha del paciente")

    def test_si_no_hay_expediente_busca_en_registro_general_y_ofrece_alta(self):
        Paciente.objects.create(
            organizacion=self.organizacion,
            apellido_nombre="García, Sofía",
            documento="27111222",
            fecha_nacimiento="1990-04-20",
            historia_clinica="HC-7788",
        )

        response = self.client.post(
            reverse("archivo:buscar"),
            {"identificador": "27111222"},
        )

        self.assertContains(response, "García, Sofía")
        self.assertContains(response, "todavía no tiene un expediente físico")
        self.assertContains(response, "Dar de alta este expediente en Archivo")

    def test_alta_desde_paciente_existente_precarga_paciente(self):
        paciente = Paciente.objects.create(
            organizacion=self.organizacion,
            apellido_nombre="García, Sofía",
            documento="27111222",
            fecha_nacimiento="1990-04-20",
            historia_clinica="HC-7788",
        )
        response = self.client.get(
            reverse("archivo:alta"),
            {"paciente_id": paciente.pk},
        )

        self.assertContains(
            response,
            f'<input type="hidden" name="paciente" value="{paciente.pk}"',
            html=False,
        )

    def test_alta_separa_seleccion_de_paciente_y_ubicacion_fisica(self):
        Paciente.objects.create(
            organizacion=self.organizacion,
            documento="27111222",
            apellido_nombre="García, Sofía",
            fecha_nacimiento="1990-04-20",
        )
        response = self.client.get(reverse("archivo:alta"))

        self.assertContains(response, 'class="card intake-card patient-selection-card"')
        self.assertContains(response, 'class="card intake-card physical-location-card"')
        self.assertContains(
            response,
            "García, Sofía · DNI 27111222",
            html=False,
        )
        self.assertContains(
            response,
            f'<input type="hidden" name="paciente" value="{Paciente.objects.get(documento="27111222").pk}"',
            html=False,
        )
        self.assertContains(response, "Completá los datos que utiliza este archivo.")
        self.assertContains(response, "Guardar expediente")
        self.assertContains(response, "Cancelar")

    def test_alta_no_renderiza_una_lista_completa_de_pacientes(self):
        for indice in range(5):
            Paciente.objects.create(
                organizacion=self.organizacion,
                documento=f"2898765{indice}",
                apellido_nombre=f"Pendiente {indice}",
            )

        response = self.client.get(reverse("archivo:alta"))

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "<option")
        self.assertContains(response, 'id="patient-search"')

    def test_busqueda_para_alta_devuelve_solo_pacientes_pendientes_de_la_organizacion(self):
        pendiente = Paciente.objects.create(
            organizacion=self.organizacion,
            documento="27111222",
            apellido_nombre="García, Sofía",
        )
        otra = Organizacion.objects.create(
            nombre="Otra clínica",
            identificador="otra-clinica",
        )
        Paciente.objects.create(
            organizacion=otra,
            documento="27111223",
            apellido_nombre="García, Sofía Otra",
        )

        response = self.client.get(
            reverse("archivo:buscar_pacientes_para_alta"),
            {"q": "García"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [item["id"] for item in response.json()["resultados"]],
            [pendiente.pk],
        )

    def test_caratula_muestra_datos_del_paciente_y_ubicacion(self):
        response = self.client.get(
            reverse("archivo:caratula", args=(self.paciente_con_hc.pk,))
        )

        self.assertContains(response, "Carátula de historia clínica")
        self.assertContains(response, self.paciente_con_hc.apellido_nombre)
        self.assertContains(response, "Archivo A")
        self.assertContains(response, "Imprimir carátula")

    def test_alta_muestra_ayuda_si_todos_los_pacientes_ya_tienen_expediente(self):
        response = self.client.get(reverse("archivo:alta"))

        self.assertContains(response, "No hay pacientes pendientes de alta")
        self.assertContains(response, "Buscar paciente en Archivo")
        self.assertNotContains(response, '<select name="paciente"')

    def test_alta_de_paciente_que_ya_tiene_expediente_abre_su_ficha(self):
        response = self.client.get(
            reverse("archivo:alta"),
            {"paciente_id": self.paciente_con_hc.pk},
        )

        self.assertRedirects(
            response,
            reverse("archivo:ficha", args=(self.expediente_con_hc.pk,)),
        )

    def test_editar_ubicacion_actualiza_expediente_existente(self):
        response = self.client.post(
            reverse("archivo:editar_ubicacion", args=(self.expediente_con_hc.pk,)),
            {
                "pasillo": "C",
                "estanteria": "8",
                "estante": "4",
                "referencia_ubicacion": "Caja clínica",
            },
        )

        self.assertRedirects(
            response,
            reverse("archivo:ficha", args=(self.expediente_con_hc.pk,)),
        )
        self.expediente_con_hc.refresh_from_db()
        self.assertEqual(
            self.expediente_con_hc.ubicacion_completa,
            "Archivo A · Pasillo C · Estantería 8 · Estante 4 · Caja clínica",
        )

    def test_ficha_muestra_ubicacion_y_estado_del_paciente(self):
        PrestamoExpediente.objects.create(
            expediente=self.expediente_con_hc,
            entregado_por="Laura Archivo",
            retirado_por="Carlos Guardia",
            servicio="Guardia",
            profesional="Dra. Ana López",
        )

        response = self.client.get(
            reverse(
                "archivo:ficha",
                args=(self.expediente_con_hc.pk,),
            )
        )

        self.assertContains(response, "Ficha del paciente")
        self.assertContains(response, "Pasillo")
        self.assertContains(response, "Estantería")
        self.assertContains(response, "Laura Archivo")
        self.assertContains(response, "La historia está prestada actualmente")

    def test_ficha_identifica_acciones_y_ubicacion_fisica(self):
        response = self.client.get(
            reverse("archivo:ficha", args=(self.expediente_con_hc.pk,))
        )

        self.assertContains(response, "Modificar datos del paciente")
        self.assertContains(response, "Editar ubicación física")
        self.assertContains(response, "Ubicación física")
        self.assertContains(response, "Enviar al Archivo Pasivo")

    def test_envia_expediente_activo_a_archivo_pasivo(self):
        response = self.client.post(
            reverse("archivo:enviar_a_pasivo", args=(self.expediente_con_hc.pk,))
        )

        self.assertRedirects(
            response,
            reverse("archivo:ficha", args=(self.expediente_con_hc.pk,)),
        )
        self.expediente_con_hc.refresh_from_db()
        self.assertEqual(self.expediente_con_hc.archivo, "P")

    def test_no_envia_a_pasivo_un_expediente_con_prestamo_activo(self):
        PrestamoExpediente.objects.create(
            expediente=self.expediente_con_hc,
            entregado_por="Laura Archivo",
            retirado_por="Carlos Guardia",
            servicio="Guardia",
            profesional="Dra. Ana López",
        )

        response = self.client.post(
            reverse("archivo:enviar_a_pasivo", args=(self.expediente_con_hc.pk,)),
            follow=True,
        )

        self.assertRedirects(
            response,
            reverse("archivo:ficha", args=(self.expediente_con_hc.pk,)),
        )
        self.expediente_con_hc.refresh_from_db()
        self.assertEqual(self.expediente_con_hc.archivo, "A")
        self.assertContains(response, "No se puede enviar al Archivo Pasivo")

    def test_no_permite_prestar_expediente_pasivo(self):
        self.expediente_con_hc.archivo = "P"
        self.expediente_con_hc.save(update_fields=("archivo",))

        response = self.client.post(
            reverse("archivo:prestar", args=(self.expediente_con_hc.pk,)),
            {
                "entregado_por": "Laura Archivo",
                "retirado_por": "Carlos Guardia",
                "servicio": "Guardia",
                "profesional": "Dra. Ana López",
            },
        )

        self.assertRedirects(
            response,
            reverse("archivo:ficha", args=(self.expediente_con_hc.pk,)),
        )
        self.assertFalse(PrestamoExpediente.objects.filter(expediente=self.expediente_con_hc).exists())

    def test_permite_busqueda_por_dni_sin_numero_interno(self):
        response = self.client.post(reverse("archivo:buscar"), {"identificador": "28987654"})

        self.assertContains(response, "Gómez, Juan")
        self.assertContains(response, "No utiliza / no registrado")

    def test_muestra_mensaje_si_no_hay_resultados(self):
        response = self.client.post(reverse("archivo:buscar"), {"identificador": "00000000"})

        self.assertContains(response, "No encontramos coincidencias.")

    def test_alta_registra_expediente_con_ubicacion(self):
        paciente = Paciente.objects.create(
            organizacion=self.organizacion,
            apellido_nombre="López, Carla",
            documento="27123456",
            fecha_nacimiento="1990-04-20",
            historia_clinica="HC-900",
        )
        response = self.client.post(
            reverse("archivo:alta"),
            {
                "paciente": paciente.pk,
                "pasillo": "B",
                "estanteria": "12",
                "estante": "4",
                "referencia_ubicacion": "Caja 2",
            },
        )

        self.assertRedirects(response, reverse("archivo:buscar"))
        expediente = ExpedienteFisico.objects.get(paciente=paciente)
        self.assertEqual(
            expediente.ubicacion_completa,
            "Archivo A · Pasillo B · Estantería 12 · Estante 4 · Caja 2",
        )

    def test_alta_permite_organizacion_sin_numero_interno(self):
        paciente = Paciente.objects.create(
            organizacion=self.organizacion,
            apellido_nombre="López, Carla",
            documento="27123456",
            fecha_nacimiento="1990-04-20",
            historia_clinica="",
        )
        response = self.client.post(
            reverse("archivo:alta"),
            {
                "paciente": paciente.pk,
                "pasillo": "",
                "estanteria": "",
                "estante": "",
                "referencia_ubicacion": "",
            },
        )

        self.assertRedirects(response, reverse("archivo:buscar"))
        expediente = ExpedienteFisico.objects.get(paciente=paciente)
        self.assertEqual(expediente.paciente.historia_clinica, "")

    def test_alta_valida_datos_requeridos(self):
        response = self.client.post(
            reverse("archivo:alta"),
            {"paciente": "", "pasillo": ""},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(ExpedienteFisico.objects.count(), 2)


class PrestamoExpedienteTests(TestCase):
    def setUp(self):
        self.organizacion = Organizacion.objects.create(
            nombre="Hospital préstamo",
            identificador="hospital-prestamo",
        )
        user = get_user_model().objects.create_user(
            username="archivo-prestamos",
            password="clave-segura",
        )
        Membresia.objects.create(
            usuario=user,
            organizacion=self.organizacion,
            perfil="administrativo",
            modulos=["archivo"],
        )
        self.client.force_login(user)
        paciente = Paciente.objects.create(
            organizacion=self.organizacion,
            documento="30123456",
            historia_clinica="HC-4521",
            apellido_nombre="Pérez, María",
            fecha_nacimiento="1990-04-20",
        )
        self.expediente = ExpedienteFisico.objects.create(
            paciente=paciente,
            pasillo="A",
            estanteria="3",
            estante="2",
        )
        self.datos_prestamo = {
            "entregado_por": "Laura Archivo",
            "retirado_por": "Carlos Guardia",
            "servicio": "Guardia pediátrica",
            "profesional": "Dra. Ana López",
        }

    def test_registra_prestamo_con_responsables_y_destino(self):
        response = self.client.post(
            reverse("archivo:prestar", args=(self.expediente.pk,)),
            self.datos_prestamo,
        )

        prestamo = PrestamoExpediente.objects.get(expediente=self.expediente)
        self.assertRedirects(
            response,
            reverse("archivo:historial", args=(self.expediente.pk,)),
        )
        self.assertEqual(prestamo.entregado_por, "Laura Archivo")
        self.assertEqual(prestamo.retirado_por, "Carlos Guardia")
        self.assertEqual(prestamo.servicio, "Guardia pediátrica")
        self.assertEqual(prestamo.profesional, "Dra. Ana López")
        self.assertIsNone(prestamo.fecha_devolucion)

    def test_no_permite_prestar_otra_vez_antes_de_devolucion(self):
        PrestamoExpediente.objects.create(
            expediente=self.expediente,
            **self.datos_prestamo,
        )

        response = self.client.post(
            reverse("archivo:prestar", args=(self.expediente.pk,)),
            self.datos_prestamo,
        )

        self.assertRedirects(
            response,
            reverse("archivo:historial", args=(self.expediente.pk,)),
        )
        self.assertEqual(PrestamoExpediente.objects.count(), 1)

    def test_registra_devolucion_y_la_muestra_en_historial(self):
        prestamo = PrestamoExpediente.objects.create(
            expediente=self.expediente,
            **self.datos_prestamo,
        )

        response = self.client.post(
            reverse("archivo:devolver", args=(prestamo.pk,)),
        )

        prestamo.refresh_from_db()
        self.assertRedirects(
            response,
            reverse("archivo:historial", args=(self.expediente.pk,)),
        )
        self.assertIsNotNone(prestamo.fecha_devolucion)
        self.assertContains(
            self.client.get(reverse("archivo:historial", args=(self.expediente.pk,))),
            "Registrar préstamo",
        )

    def test_busqueda_muestra_actividad_reciente_y_acceso_a_historial(self):
        PrestamoExpediente.objects.create(
            expediente=self.expediente,
            **self.datos_prestamo,
        )

        response = self.client.post(
            reverse("archivo:buscar"),
            {"identificador": self.expediente.paciente.documento},
        )

        self.assertContains(response, "Laura Archivo")
        self.assertContains(response, "Ver historial")
        self.assertContains(response, "Prestado actualmente")
