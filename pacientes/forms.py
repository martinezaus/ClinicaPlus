from django import forms

from .models import Paciente


class PacienteForm(forms.ModelForm):
    fecha_nacimiento = forms.DateField(
        label="Fecha de nacimiento",
        required=False,
        input_formats=("%Y-%m-%d",),
        widget=forms.DateInput(
            format="%Y-%m-%d",
            attrs={"type": "date"},
        ),
    )

    class Meta:
        model = Paciente
        fields = (
            "apellido_nombre",
            "documento",
            "fecha_nacimiento",
            "historia_clinica",
            "alergias",
        )
        widgets = {
            "alergias": forms.Textarea(attrs={"rows": 3}),
        }
        labels = {
            "apellido_nombre": "Apellido y nombre",
            "documento": "DNI / documento",
            "fecha_nacimiento": "Fecha de nacimiento",
            "historia_clinica": "Número de historia clínica",
            "alergias": "Alergias y observaciones clínicas",
        }
