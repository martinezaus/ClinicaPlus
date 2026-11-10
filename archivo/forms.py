from django import forms

from pacientes.models import Paciente
from .models import ExpedienteFisico, PrestamoExpediente


class BusquedaExpedienteForm(forms.Form):
    identificador = forms.CharField(
        label="DNI o número interno de historia clínica",
        max_length=30,
        widget=forms.TextInput(
            attrs={
                "autocomplete": "off",
                "autofocus": True,
                "placeholder": "DNI, número de HC o apellido y nombre",
            }
        ),
    )


class AltaExpedienteForm(forms.ModelForm):
    def __init__(self, *args, organizacion=None, **kwargs):
        super().__init__(*args, **kwargs)
        pacientes = Paciente.objects.filter(expediente_fisico__isnull=True)
        if organizacion is not None:
            pacientes = pacientes.filter(organizacion=organizacion)
        paciente_id = (
            self.data.get(self.add_prefix("paciente"))
            if self.is_bound
            else self.initial.get("paciente")
        )
        if not paciente_id and not self.is_bound:
            pendientes = list(
                pacientes.order_by("pk").values_list("pk", flat=True)[:2]
            )
            self.pacientes_disponibles = bool(pendientes)
            if len(pendientes) == 1:
                paciente_id = pendientes[0]
                self.initial["paciente"] = paciente_id
        else:
            self.pacientes_disponibles = True

        if paciente_id and str(paciente_id).isdecimal():
            pacientes = pacientes.filter(pk=paciente_id)
        else:
            pacientes = pacientes.none()
        self.fields["paciente"].queryset = pacientes

    class Meta:
        model = ExpedienteFisico
        fields = (
            "paciente",
            "pasillo",
            "estanteria",
            "estante",
            "referencia_ubicacion",
        )
        widgets = {
            "paciente": forms.HiddenInput(),
            "referencia_ubicacion": forms.TextInput(
                attrs={"placeholder": "Sector, caja u otra referencia"}
            ),
        }


class UbicacionExpedienteForm(forms.ModelForm):
    class Meta:
        model = ExpedienteFisico
        fields = ("pasillo", "estanteria", "estante", "referencia_ubicacion")
        widgets = {
            "referencia_ubicacion": forms.TextInput(
                attrs={"placeholder": "Sector, caja u otra referencia"}
            ),
        }


class PrestamoExpedienteForm(forms.ModelForm):
    class Meta:
        model = PrestamoExpediente
        fields = ("entregado_por", "retirado_por", "servicio", "profesional")
