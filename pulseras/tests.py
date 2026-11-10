from datetime import date
from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse

from organizaciones.models import Membresia, Organizacion
from .forms import PulseraForm
from .models import ImpresoraPulsera, PerfilMedioPulsera, TrabajoImpresion
from .printing import ImpresionError, construir_comando


class PulseraTests(TestCase):
    def setUp(self):
        self.organizacion = Organizacion.objects.create(
            nombre="Clínica de prueba",
            identificador="clinica-prueba",
        )
        from django.contrib.auth import get_user_model

        user = get_user_model().objects.create_user(
            username="enfermeria",
            password="clave-segura",
        )
        Membresia.objects.create(
            usuario=user,
            organizacion=self.organizacion,
            perfil="enfermero",
        )
        self.client.force_login(user)
        ImpresoraPulsera.objects.bulk_create(
            [
                ImpresoraPulsera(
                    nombre="Zebra Guardia Adulto",
                    organizacion=self.organizacion,
                    modelo="Zebra",
                    driver="zpl",
                    servicio="Guardia adultos",
                    activa=False,
                ),
                ImpresoraPulsera(
                    nombre="Zebra Guardia Pediátrica",
                    organizacion=self.organizacion,
                    modelo="Zebra",
                    driver="zpl",
                    servicio="Guardia pediátrica",
                    activa=False,
                ),
                ImpresoraPulsera(
                    nombre="TSC TDP-225 Pediatría",
                    organizacion=self.organizacion,
                    modelo="TSC TDP-225",
                    driver="tspl",
                    servicio="Pabellón de pediatría",
                    activa=False,
                ),
            ]
        )

    def crear_impresora(self, driver="zpl", tipo="pediatrico"):
        impresora = ImpresoraPulsera.objects.create(
            nombre="Impresora de prueba",
            organizacion=self.organizacion,
            modelo="Modelo de prueba",
            driver=driver,
            cola_sistema="Impresora de prueba",
            servicio="Guardia",
            activa=True,
        )
        perfil = PerfilMedioPulsera.objects.create(
            impresora=impresora,
            tipo=tipo,
            ancho_mm=Decimal("25"),
            largo_mm=Decimal("280"),
            sensor="gap",
        )
        return impresora, perfil


    def test_muestra_formulario(self):
        response = self.client.get(reverse("pulseras:form"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Adulto")
        self.assertContains(response, "Pediátrico")
        self.assertContains(response, "No hay una impresora lista")
        self.assertContains(response, "Zebra Guardia Adulto")
        self.assertContains(response, "TSC TDP-225 Pediatría")

    def test_actualiza_vista_previa_sin_numero_interno(self):
        impresora, _ = self.crear_impresora()
        response = self.client.post(
            reverse("pulseras:form"),
            {
                "tipo": "pediatrico",
                "apellido_nombre": "Pérez, Ana",
                "documento": "30123456",
                "fecha_nacimiento": "2020-05-10",
                "historia_clinica": "",
                "servicio": "Guardia pediátrica",
                "alergias": "",
                "impresora": impresora.pk,
                "copias": 1,
                "accion": "vista_previa",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Pérez, Ana")
        self.assertContains(response, "DNI 30123456")
        self.assertContains(response, "25.0 × 280.0 mm")
        self.assertNotContains(response, "HC ")

    def test_rechaza_tipo_de_pulsera_desconocido(self):
        impresora, _ = self.crear_impresora(tipo="adulto")
        form = PulseraForm(
            {
                "tipo": "neonatal",
                "apellido_nombre": "Pérez, Ana",
                "documento": "30123456",
                "fecha_nacimiento": "2020-05-10",
                "historia_clinica": "",
                "servicio": "Pediatría",
                "alergias": "",
                "impresora": "",
                "copias": 1,
            }
        )

        self.assertFalse(form.is_valid())

    @patch("pulseras.views.enviar_a_windows")
    def test_envia_zpl_a_cola_windows(self, enviar):
        impresora, perfil = self.crear_impresora()
        response = self.client.post(
            reverse("pulseras:form"),
            {
                "tipo": "pediatrico",
                "apellido_nombre": "Pérez, Ana",
                "documento": "30123456",
                "fecha_nacimiento": "2020-05-10",
                "historia_clinica": "HC-12",
                "servicio": "Pediatría",
                "alergias": "Penicilina",
                "impresora": impresora.pk,
                "copias": 2,
                "accion": "imprimir",
            },
        )

        enviar.assert_called_once()
        queue_name, payload = enviar.call_args.args
        self.assertEqual(queue_name, "Impresora de prueba")
        self.assertIn(b"^MNY", payload)
        self.assertIn(b"^PQ2", payload)
        self.assertIn(b"\\44\\4E\\49", payload)
        self.assertContains(response, "Trabajo enviado a la cola")
        self.assertEqual(perfil.tipo, "pediatrico")
        trabajo = TrabajoImpresion.objects.get()
        self.assertEqual(trabajo.estado, "sent")
        self.assertEqual(trabajo.impresora, impresora)
        self.assertEqual(trabajo.copias, 2)
        self.assertEqual(trabajo.tipo, "pediatrico")

    def test_rechaza_impresora_sin_perfil_para_tamano_seleccionado(self):
        impresora, _ = self.crear_impresora(tipo="adulto")
        form = PulseraForm(
            {
                "tipo": "pediatrico",
                "apellido_nombre": "Pérez, Ana",
                "documento": "30123456",
                "fecha_nacimiento": "2020-05-10",
                "historia_clinica": "",
                "servicio": "Pediatría",
                "alergias": "",
                "impresora": impresora.pk,
                "copias": 1,
                "accion": "imprimir",
            }
        )

        self.assertFalse(form.is_valid())
        self.assertIn("impresora", form.errors)

    def test_muestra_impresoras_cargadas_aunque_no_estan_configuradas(self):
        ImpresoraPulsera.objects.create(
            nombre="Zebra Guardia",
            organizacion=self.organizacion,
            modelo="Zebra",
            driver="zpl",
            activa=True,
        )
        response = self.client.get(reverse("pulseras:form"))

        self.assertContains(response, "Impresoras cargadas")
        self.assertContains(response, "Zebra Guardia")
        self.assertContains(response, "falta configurar la cola de Windows")
        self.assertContains(response, "falta configurar la medida adulto")

    def test_no_muestra_impresoras_de_otra_organizacion(self):
        otra = Organizacion.objects.create(
            nombre="Otra clínica",
            identificador="otra-clinica",
        )
        ImpresoraPulsera.objects.create(
            nombre="Impresora privada",
            organizacion=otra,
            modelo="Zebra",
            driver="zpl",
        )

        response = self.client.get(reverse("pulseras:form"))

        self.assertContains(response, "Zebra Guardia Adulto")
        self.assertNotContains(response, "Impresora privada")

    @patch("pulseras.views.enviar_a_windows", side_effect=ImpresionError("cola desconectada"))
    def test_muestra_error_de_impresion(self, enviar):
        impresora, _ = self.crear_impresora()
        response = self.client.post(
            reverse("pulseras:form"),
            {
                "tipo": "pediatrico",
                "apellido_nombre": "Pérez, Ana",
                "documento": "30123456",
                "fecha_nacimiento": "2020-05-10",
                "historia_clinica": "",
                "servicio": "Pediatría",
                "alergias": "",
                "impresora": impresora.pk,
                "copias": 1,
                "accion": "imprimir",
            },
        )

        enviar.assert_called_once()
        self.assertContains(response, "cola desconectada")
        trabajo = TrabajoImpresion.objects.get()
        self.assertEqual(trabajo.estado, "error")
        self.assertEqual(trabajo.error, "cola desconectada")

    def test_construye_comando_tspl_con_su_tamano_y_copias(self):
        impresora, perfil = self.crear_impresora(driver="tspl")
        data = {
            "apellido_nombre": 'Pérez "Ana"',
            "documento": "30123456",
            "fecha_nacimiento": date(2020, 5, 10),
            "historia_clinica": "",
            "servicio": "Pediatría",
            "alergias": "",
        }

        payload = construir_comando(data, perfil, 2)

        self.assertEqual(impresora.driver, "tspl")
        self.assertIn(b"SIZE 25.0 mm,280.0 mm", payload)
        self.assertIn(b"PRINT 1,2", payload)
        self.assertIn(b"Pediatr", payload)
