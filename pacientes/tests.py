from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from organizaciones.models import Membresia, Organizacion
from .models import Paciente


class ListaPacientesTests(TestCase):
    def setUp(self):
        self.organizacion = Organizacion.objects.create(
            nombre="Hospital de pacientes",
            identificador="hospital-pacientes",
        )
        user = get_user_model().objects.create_user(
            username="pacientes",
            password="test-password-123",
        )
        Membresia.objects.create(
            usuario=user,
            organizacion=self.organizacion,
            perfil="administrativo",
            modulos=["archivo"],
        )
        self.client.force_login(user)
        self.paciente = Paciente.objects.create(
            organizacion=self.organizacion,
            documento="30123456",
            historia_clinica="HC-4521",
            apellido_nombre="Pérez, María",
        )

    def test_lista_no_muestra_area_y_ofrece_imprimir_caratula(self):
        response = self.client.get(reverse("pacientes:index"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "<th>Paciente</th>")
        self.assertContains(response, "Imprimir carátula")
        self.assertContains(
            response,
            reverse("archivo:caratula", args=(self.paciente.pk,)),
        )
        self.assertNotContains(response, "<th>Área</th>", html=False)
        self.assertNotIn("area", {field.name for field in Paciente._meta.fields})
