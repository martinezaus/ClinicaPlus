from django.conf import settings
from django.core.validators import FileExtensionValidator, URLValidator
from django.db import models


class Organizacion(models.Model):
    nombre = models.CharField(max_length=160)
    identificador = models.SlugField(max_length=100, unique=True)
    logo = models.FileField(
        upload_to="organizaciones/logos/",
        blank=True,
        validators=[FileExtensionValidator(["png", "jpg", "jpeg", "webp"])],
        help_text="Logo de la organización en PNG, JPG o WebP.",
    )
    activa = models.BooleanField(default=True)
    creada_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("nombre",)
        verbose_name = "organización"
        verbose_name_plural = "organizaciones"

    def __str__(self):
        return self.nombre


class ModuloExterno(models.Model):
    nombre = models.CharField(max_length=100)
    url = models.URLField(
        max_length=500,
        validators=[URLValidator(schemes=["http", "https"])],
    )
    activo = models.BooleanField(default=True)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("nombre",)
        verbose_name = "módulo externo"
        verbose_name_plural = "módulos externos"

    def __str__(self):
        return self.nombre


class Membresia(models.Model):
    PERFIL_CHOICES = (
        ("administrativo", "Administrativo"),
        ("medico", "Médico"),
        ("enfermero", "Enfermería"),
        ("legal", "Legal"),
    )
    MODULOS_CHOICES = (
        ("archivo", "Archivo y pacientes"),
        ("pulseras", "Admisión"),
        ("facturacion", "Facturación"),
    )

    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="membresia_organizacion",
    )
    organizacion = models.ForeignKey(
        Organizacion,
        on_delete=models.PROTECT,
        related_name="membresias",
    )
    perfil = models.CharField(max_length=20, choices=PERFIL_CHOICES)
    modulos = models.JSONField(default=list, blank=True)
    modulos_externos = models.ManyToManyField(
        ModuloExterno,
        blank=True,
        related_name="membresias",
    )
    activa = models.BooleanField(default=True)

    class Meta:
        verbose_name = "membresía de usuario"
        verbose_name_plural = "membresías de usuarios"

    def __str__(self):
        return f"{self.usuario} — {self.get_perfil_display()} — {self.organizacion}"

    def puede_acceder(self, modulo):
        return (
            self.activa
            and self.organizacion.activa
            and modulo in self.modulos
        )
