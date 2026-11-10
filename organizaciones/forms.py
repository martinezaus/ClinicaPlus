from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import (
    AuthenticationForm,
    SetPasswordForm,
    UserCreationForm,
)
from django.db.models import Q

from .models import Membresia, ModuloExterno, Organizacion


class AccesoForm(AuthenticationForm):
    username = forms.CharField(
        label="Usuario",
        widget=forms.TextInput(
            attrs={"autofocus": True, "autocomplete": "username"}
        ),
    )
    password = forms.CharField(
        label="Contraseña",
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "current-password"}),
    )


class AltaUsuarioForm(UserCreationForm):
    organizacion = forms.ModelChoiceField(
        label="Organización",
        queryset=Organizacion.objects.filter(activa=True),
    )
    perfil = forms.ChoiceField(label="Perfil", choices=Membresia.PERFIL_CHOICES)
    modulos = forms.MultipleChoiceField(
        label="Módulos de Clínica+",
        choices=Membresia.MODULOS_CHOICES,
        required=False,
        widget=forms.CheckboxSelectMultiple,
        help_text="Archivo habilita Pacientes y Expediente físico / Archivo.",
    )
    modulos_externos = forms.ModelMultipleChoiceField(
        label="Módulos conectados",
        queryset=ModuloExterno.objects.filter(activo=True),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        help_text="Los permisos internos de cada sistema externo se gestionan allí.",
    )

    class Meta(UserCreationForm.Meta):
        model = get_user_model()
        fields = ("username", "first_name", "last_name", "email")
        labels = {
            "username": "Usuario",
            "first_name": "Nombre",
            "last_name": "Apellido",
            "email": "Correo electrónico",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if not isinstance(field.widget, forms.CheckboxSelectMultiple):
                field.widget.attrs.setdefault("class", "form-control")


class EditarUsuarioForm(forms.Form):
    first_name = forms.CharField(label="Nombre", max_length=150, required=False)
    last_name = forms.CharField(label="Apellido", max_length=150, required=False)
    email = forms.EmailField(label="Correo electrónico", required=False)
    organizacion = forms.ModelChoiceField(
        label="Organización",
        queryset=Organizacion.objects.filter(activa=True),
    )
    perfil = forms.ChoiceField(label="Perfil", choices=Membresia.PERFIL_CHOICES)
    modulos = forms.MultipleChoiceField(
        label="Módulos de Clínica+",
        choices=Membresia.MODULOS_CHOICES,
        required=False,
        widget=forms.CheckboxSelectMultiple,
        help_text="Archivo habilita Pacientes y Expediente físico / Archivo.",
    )
    modulos_externos = forms.ModelMultipleChoiceField(
        label="Módulos conectados",
        queryset=ModuloExterno.objects.none(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        help_text="Los permisos internos de cada sistema externo se gestionan allí.",
    )
    activo = forms.BooleanField(label="Usuario activo", required=False)

    def __init__(self, *args, usuario, membresia, **kwargs):
        self.usuario = usuario
        self.membresia = membresia
        initial = {
            "first_name": usuario.first_name,
            "last_name": usuario.last_name,
            "email": usuario.email,
            "organizacion": membresia.organizacion_id,
            "perfil": membresia.perfil,
            "modulos": membresia.modulos,
            "modulos_externos": membresia.modulos_externos.all(),
            "activo": usuario.is_active and membresia.activa,
        }
        initial.update(kwargs.pop("initial", {}))
        super().__init__(*args, initial=initial, **kwargs)
        self.fields["modulos_externos"].queryset = ModuloExterno.objects.filter(
            Q(activo=True) | Q(membresias=membresia)
        ).distinct()

    def save(self):
        self.usuario.first_name = self.cleaned_data["first_name"]
        self.usuario.last_name = self.cleaned_data["last_name"]
        self.usuario.email = self.cleaned_data["email"]
        self.usuario.is_active = self.cleaned_data["activo"]
        self.usuario.save(
            update_fields=["first_name", "last_name", "email", "is_active"]
        )

        self.membresia.organizacion = self.cleaned_data["organizacion"]
        self.membresia.perfil = self.cleaned_data["perfil"]
        self.membresia.modulos = self.cleaned_data["modulos"]
        self.membresia.activa = self.cleaned_data["activo"]
        self.membresia.save(
            update_fields=["organizacion", "perfil", "modulos", "activa"]
        )
        self.membresia.modulos_externos.set(
            self.cleaned_data["modulos_externos"]
        )
        return self.usuario


class ModuloExternoForm(forms.ModelForm):
    class Meta:
        model = ModuloExterno
        fields = ("nombre", "url")
        labels = {
            "nombre": "Nombre del sistema",
            "url": "Enlace para ingresar",
        }
        widgets = {
            "url": forms.URLInput(attrs={"placeholder": "https://sistema.ejemplo.com"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "form-control")


class RestablecerContrasenaForm(SetPasswordForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "form-control")
