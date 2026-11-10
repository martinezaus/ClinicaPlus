from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from urllib.parse import quote

from .models import Membresia, ModuloExterno, Organizacion


@override_settings(PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
class AccesoPorPerfilTests(TestCase):
    def setUp(self):
        self.organizacion = Organizacion.objects.create(
            nombre="Hospital de acceso",
            identificador="hospital-acceso",
        )

    def crear_usuario(self, username, perfil):
        modulos_por_perfil = {
            "administrativo": ["archivo", "pulseras"],
            "medico": ["pulseras"],
            "enfermero": ["pulseras"],
            "legal": [],
        }
        usuario = get_user_model().objects.create_user(
            username=username,
            password="Prueba-segura-2026",
        )
        Membresia.objects.create(
            usuario=usuario,
            organizacion=self.organizacion,
            perfil=perfil,
            modulos=modulos_por_perfil[perfil],
        )
        return usuario

    def test_inicio_sin_sesion_abre_login(self):
        response = self.client.get(reverse("organizaciones:inicio"))

        self.assertRedirects(
            response,
            f"{reverse('organizaciones:login')}?next={quote(reverse('organizaciones:inicio'), safe='/')}",
        )

    def test_portada_raiz_muestra_login(self):
        response = self.client.get(reverse("organizaciones:login"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Iniciar sesión")

    def test_url_del_sistema_esta_montada_bajo_prefijo_clinica(self):
        self.assertEqual(reverse("organizaciones:login"), "/clinica+/")
        self.assertEqual(reverse("organizaciones:inicio"), "/clinica+/inicio/")
        self.assertEqual(
            reverse("pulseras:form"),
            "/clinica+/pulseras/",
        )
        self.assertEqual(
            reverse("archivo:buscar"),
            "/clinica+/archivo/",
        )

    def test_raiz_redirige_a_prefijo_de_clinica_y_acepta_host_configurado(self):
        response = self.client.get(
            "/",
            HTTP_HOST="conetia.sistemas.com:8083",
        )

        self.assertRedirects(response, "/clinica+/", fetch_redirect_response=False)

        response = self.client.get(
            "/clinica+/",
            HTTP_HOST="conetia.sistemas.com:8083",
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Iniciar sesión")

    def test_login_valido_muestra_nombre_de_organizacion_y_modulos(self):
        self.crear_usuario("admin-hospital", "administrativo")

        response = self.client.post(
            reverse("organizaciones:login"),
            {"username": "admin-hospital", "password": "Prueba-segura-2026"},
        )

        self.assertRedirects(response, reverse("organizaciones:inicio"))
        response = self.client.get(reverse("organizaciones:inicio"))
        self.assertContains(response, "Hospital de acceso")
        self.assertContains(response, "Expediente físico / Archivo")
        self.assertContains(response, "Admisión")
        for card in (
            "Turnos",
            "Prestaciones",
            "Estadísticas y reportes",
            "Indicadores",
            "Farmacia",
            "Configuración",
        ):
            self.assertNotContains(response, card)

    def test_cards_en_desarrollo_solo_aparecen_para_superusuario(self):
        superusuario = get_user_model().objects.create_superuser(
            username="admin-sistema",
            email="admin@example.com",
            password="Prueba-segura-2026",
        )
        self.client.force_login(superusuario)

        response = self.client.get(reverse("organizaciones:inicio"))

        for card in (
            "Turnos",
            "Prestaciones",
            "Estadísticas y reportes",
            "Farmacia",
        ):
            self.assertContains(response, card)
        self.assertNotContains(response, "Indicadores")

    def test_navegacion_solo_muestra_inicio_y_soporte(self):
        usuario = self.crear_usuario("nav-hospital", "administrativo")
        self.client.force_login(usuario)

        response = self.client.get(reverse("organizaciones:inicio"))

        self.assertEqual(
            [item["label"] for item in response.context["navigation_items"]],
            ["Inicio"],
        )
        self.assertContains(response, "Soporte")

    def test_medico_no_puede_entrar_al_archivo(self):
        usuario = self.crear_usuario("medico-hospital", "medico")
        self.client.force_login(usuario)

        response = self.client.get(reverse("archivo:buscar"))

        self.assertEqual(response.status_code, 403)

    def test_administrativo_puede_entrar_al_archivo(self):
        usuario = self.crear_usuario("archivo-hospital", "administrativo")
        self.client.force_login(usuario)

        response = self.client.get(reverse("archivo:buscar"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Hospital de acceso")

    def test_cierre_de_sesion_es_post(self):
        usuario = self.crear_usuario("salida-hospital", "enfermero")
        self.client.force_login(usuario)

        response = self.client.post(reverse("organizaciones:logout"))

        self.assertRedirects(response, reverse("organizaciones:login"))
        self.assertNotIn("_auth_user_id", self.client.session)


@override_settings(PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
class AdministracionUsuariosTests(TestCase):
    def setUp(self):
        self.organizacion = Organizacion.objects.create(
            nombre="Hospital de usuarios",
            identificador="hospital-usuarios",
        )
        self.superusuario = get_user_model().objects.create_superuser(
            username="admin-sistema",
            email="admin@example.com",
            password="Prueba-segura-2026",
        )

    def crear_usuario(self, username="usuario-existente", perfil="administrativo"):
        usuario = get_user_model().objects.create_user(
            username=username,
            password="Prueba-segura-2026",
        )
        Membresia.objects.create(
            usuario=usuario,
            organizacion=self.organizacion,
            perfil=perfil,
        )
        return usuario

    def test_card_de_administracion_solo_aparece_para_superusuarios(self):
        self.client.force_login(self.superusuario)
        response = self.client.get(reverse("organizaciones:inicio"))
        self.assertContains(response, "Configuración")
        self.assertNotContains(response, "Administración de usuarios")
        response = self.client.get(reverse("organizaciones:configuracion"))
        self.assertContains(response, "USUARIOS")

        self.client.force_login(self.crear_usuario())
        response = self.client.get(reverse("organizaciones:inicio"))
        self.assertNotContains(response, "Configuración")
        response = self.client.get(reverse("organizaciones:configuracion"))
        self.assertEqual(response.status_code, 403)

    def test_configuracion_muestra_los_tres_cards_solicitados(self):
        self.client.force_login(self.superusuario)

        response = self.client.get(reverse("organizaciones:configuracion"))

        self.assertContains(response, "USUARIOS")
        self.assertContains(response, "MÓDULOS")
        self.assertContains(response, "PARÁMETROS")

    def test_usuario_comun_no_puede_administrar_usuarios(self):
        self.client.force_login(self.crear_usuario())

        response = self.client.get(reverse("organizaciones:usuarios"))

        self.assertEqual(response.status_code, 403)

    def test_superusuario_crea_usuario_con_membresia_y_sin_privilegios_admin(self):
        modulo = ModuloExterno.objects.create(
            nombre="Sistema conectado",
            url="https://sistema.example.com/",
        )
        self.client.force_login(self.superusuario)

        response = self.client.post(
            reverse("organizaciones:usuarios"),
            {
                "username": "nuevo-usuario",
                "first_name": "Nuevo",
                "last_name": "Usuario",
                "email": "nuevo@example.com",
                "organizacion": self.organizacion.pk,
                "perfil": "medico",
                "modulos": ["pulseras", "facturacion"],
                "modulos_externos": [modulo.pk],
                "password1": "Una-clave-segura-2026",
                "password2": "Una-clave-segura-2026",
            },
        )

        self.assertRedirects(response, reverse("organizaciones:usuarios"))
        usuario = get_user_model().objects.get(username="nuevo-usuario")
        self.assertTrue(usuario.check_password("Una-clave-segura-2026"))
        self.assertFalse(usuario.is_staff)
        self.assertFalse(usuario.is_superuser)
        self.assertEqual(usuario.membresia_organizacion.organizacion, self.organizacion)
        self.assertEqual(usuario.membresia_organizacion.perfil, "medico")
        self.assertEqual(
            usuario.membresia_organizacion.modulos,
            ["pulseras", "facturacion"],
        )
        self.assertQuerySetEqual(
            usuario.membresia_organizacion.modulos_externos.all(),
            [modulo],
        )

    def test_superusuario_agrega_y_edita_un_modulo_conectado(self):
        self.client.force_login(self.superusuario)

        response = self.client.post(
            reverse("organizaciones:alta-modulo"),
            {
                "nombre": "Portal externo",
                "url": "https://portal.example.com/",
            },
        )

        self.assertRedirects(response, reverse("organizaciones:modulos"))
        modulo = ModuloExterno.objects.get(nombre="Portal externo")
        response = self.client.post(
            reverse("organizaciones:editar-modulo", args=[modulo.pk]),
            {
                "nombre": "Portal actualizado",
                "url": "https://nuevo.example.com/",
            },
        )
        self.assertRedirects(response, reverse("organizaciones:modulos"))
        modulo.refresh_from_db()
        self.assertEqual(modulo.nombre, "Portal actualizado")
        self.assertEqual(modulo.url, "https://nuevo.example.com/")

    def test_no_se_aceptan_enlaces_no_http_para_modulos(self):
        self.client.force_login(self.superusuario)

        response = self.client.post(
            reverse("organizaciones:alta-modulo"),
            {"nombre": "Enlace inválido", "url": "javascript:alert(1)"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(ModuloExterno.objects.exists())

    def test_usuario_ve_solo_modulos_externos_activos_que_tiene_asignados(self):
        asignado = ModuloExterno.objects.create(
            nombre="Portal asignado",
            url="https://portal.example.com/",
        )
        no_asignado = ModuloExterno.objects.create(
            nombre="Portal ajeno",
            url="https://otro.example.com/",
        )
        desactivado = ModuloExterno.objects.create(
            nombre="Portal desactivado",
            url="https://apagado.example.com/",
            activo=False,
        )
        usuario = self.crear_usuario()
        usuario.membresia_organizacion.modulos_externos.add(asignado, desactivado)
        self.client.force_login(usuario)

        response = self.client.get(reverse("organizaciones:inicio"))

        self.assertContains(response, "Portal asignado")
        self.assertNotContains(response, "Portal ajeno")
        self.assertNotContains(response, "Portal desactivado")
        self.assertIn(asignado, response.context["modulos_externos"])
        self.assertNotIn(
            "Portal asignado",
            [sistema["nombre"] for sistema in response.context["sistemas"]],
        )
        content = response.content.decode()
        self.assertLess(
            content.index('class="contracted-systems"'),
            content.index("Portal asignado"),
        )

    def test_editar_usuario_puede_agregar_y_quitar_modulos_externos(self):
        asignado = ModuloExterno.objects.create(
            nombre="Portal existente",
            url="https://existente.example.com/",
        )
        agregar = ModuloExterno.objects.create(
            nombre="Portal nuevo",
            url="https://nuevo.example.com/",
        )
        usuario = self.crear_usuario()
        usuario.membresia_organizacion.modulos_externos.add(asignado)
        self.client.force_login(self.superusuario)

        response = self.client.post(
            reverse("organizaciones:editar-usuario", args=[usuario.pk]),
            {
                "first_name": "",
                "last_name": "",
                "email": "",
                "organizacion": self.organizacion.pk,
                "perfil": "legal",
                "modulos": [],
                "modulos_externos": [agregar.pk],
                "activo": "on",
            },
        )

        self.assertRedirects(response, reverse("organizaciones:usuarios"))
        usuario.membresia_organizacion.refresh_from_db()
        self.assertQuerySetEqual(
            usuario.membresia_organizacion.modulos_externos.all(),
            [agregar],
        )

    def test_usuario_solo_ve_los_cards_asignados_y_no_puede_abrir_otro_modulo(self):
        usuario = self.crear_usuario("usuario-solo-admision", "medico")
        usuario.membresia_organizacion.modulos = ["pulseras"]
        usuario.membresia_organizacion.save(update_fields=["modulos"])
        self.client.force_login(usuario)

        response = self.client.get(reverse("organizaciones:inicio"))

        self.assertContains(response, "Admisión")
        self.assertNotContains(response, "Pacientes")
        self.assertNotContains(response, "Expediente físico / Archivo")
        self.assertEqual(
            self.client.get(reverse("archivo:buscar")).status_code,
            403,
        )

    def test_superusuario_puede_editar_perfil_estado_y_cards(self):
        usuario = self.crear_usuario()
        self.client.force_login(self.superusuario)

        response = self.client.post(
            reverse("organizaciones:editar-usuario", args=[usuario.pk]),
            {
                "first_name": "Actualizado",
                "last_name": "Usuario",
                "email": "actualizado@example.com",
                "organizacion": self.organizacion.pk,
                "perfil": "legal",
                "modulos": ["facturacion"],
                "activo": "on",
            },
        )

        self.assertRedirects(response, reverse("organizaciones:usuarios"))
        usuario.refresh_from_db()
        usuario.membresia_organizacion.refresh_from_db()
        self.assertEqual(usuario.first_name, "Actualizado")
        self.assertEqual(usuario.membresia_organizacion.perfil, "legal")
        self.assertEqual(usuario.membresia_organizacion.modulos, ["facturacion"])
        self.assertTrue(usuario.membresia_organizacion.puede_acceder("facturacion"))

    def test_facturacion_requiere_permiso_asignado(self):
        usuario = self.crear_usuario("usuario-sin-facturacion", "legal")
        self.client.force_login(usuario)

        response = self.client.get(reverse("organizaciones:facturacion"))

        self.assertEqual(response.status_code, 403)

    def test_dar_de_baja_desactiva_usuario_y_membresia_sin_eliminarlo(self):
        usuario = self.crear_usuario()
        self.client.force_login(self.superusuario)

        response = self.client.post(
            reverse("organizaciones:dar-de-baja-usuario", args=[usuario.pk])
        )

        self.assertRedirects(response, reverse("organizaciones:usuarios"))
        usuario.refresh_from_db()
        usuario.membresia_organizacion.refresh_from_db()
        self.assertFalse(usuario.is_active)
        self.assertFalse(usuario.membresia_organizacion.activa)
        self.assertTrue(get_user_model().objects.filter(pk=usuario.pk).exists())

    def test_restablecer_contrasena_actualiza_la_clave(self):
        usuario = self.crear_usuario()
        self.client.force_login(self.superusuario)

        response = self.client.post(
            reverse("organizaciones:restablecer-contrasena-usuario", args=[usuario.pk]),
            {
                "new_password1": "Otra-clave-segura-2026",
                "new_password2": "Otra-clave-segura-2026",
            },
        )

        self.assertRedirects(response, reverse("organizaciones:usuarios"))
        usuario.refresh_from_db()
        self.assertTrue(usuario.check_password("Otra-clave-segura-2026"))
