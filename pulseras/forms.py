from django import forms

from .models import ImpresoraPulsera, PerfilMedioPulsera


class PulseraForm(forms.Form):
    TIPO_CHOICES = (
        ("adulto", "Adulto"),
        ("pediatrico", "Pediátrico"),
    )

    tipo = forms.ChoiceField(label="Tipo de pulsera", choices=TIPO_CHOICES)
    apellido_nombre = forms.CharField(label="Apellido y nombre", max_length=120)
    documento = forms.CharField(
        label="DNI",
        max_length=20,
        widget=forms.TextInput(attrs={"inputmode": "numeric"}),
    )
    fecha_nacimiento = forms.DateField(
        label="Fecha de nacimiento",
        widget=forms.DateInput(attrs={"type": "date"}),
    )
    historia_clinica = forms.CharField(
        label="Número de historia clínica",
        max_length=20,
        required=False,
        help_text="Opcional cuando la organización identifica al paciente solo por DNI.",
    )
    servicio = forms.CharField(label="Servicio o sala", max_length=50)
    alergias = forms.CharField(label="Alergias", max_length=200, required=False)
    impresora = forms.ModelChoiceField(
        label="Impresora",
        queryset=ImpresoraPulsera.objects.all(),
        required=False,
        empty_label="Seleccioná una impresora para imprimir",
        help_text="Se muestran todos los equipos cargados; los que falten configurar no podrán imprimir.",
    )
    copias = forms.IntegerField(
        label="Copias",
        min_value=1,
        max_value=3,
        initial=1,
        help_text="Máximo 3 pulseras por envío.",
    )

    def __init__(self, *args, organizacion=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["impresora"].queryset = (
            ImpresoraPulsera.objects.filter(organizacion=organizacion)
            if organizacion
            else ImpresoraPulsera.objects.none()
        )
        tipo_display = dict(PerfilMedioPulsera.TIPO_CHOICES)
        opciones = []
        for impresora in self.fields["impresora"].queryset.prefetch_related("perfiles"):
            perfiles = list(impresora.perfiles.all())
            tamaños = ", ".join(tipo_display[perfil.tipo] for perfil in perfiles)
            estado = []
            if not impresora.activa:
                estado.append("inactiva")
            if not impresora.cola_sistema.strip():
                estado.append("falta nombre de cola Windows")
            if not perfiles:
                estado.append("faltan medidas")
            descripcion = " · ".join(
                parte
                for parte in (impresora.modelo, tamaños or "sin perfiles", ", ".join(estado))
                if parte
            )
            opciones.append(
                (
                    impresora.pk,
                    f"{impresora.nombre} — {descripcion}",
                )
            )
        self.fields["impresora"].choices = [
            ("", "Seleccioná una impresora para imprimir")
        ] + opciones

    def clean(self):
        cleaned_data = super().clean()
        impresora = cleaned_data.get("impresora")
        tipo = cleaned_data.get("tipo")
        imprimir = self.data.get("accion") == "imprimir"
        if imprimir and not impresora:
            self.add_error("impresora", "Seleccioná la impresora donde imprimir.")
        if imprimir and impresora:
            if not impresora.activa:
                self.add_error("impresora", "La impresora está inactiva.")
            if not impresora.cola_sistema.strip():
                self.add_error(
                    "impresora",
                    "Falta configurar el nombre exacto de la cola de Windows.",
                )
            if tipo and not PerfilMedioPulsera.objects.filter(
                impresora=impresora,
                tipo=tipo,
                ancho_mm__gt=0,
                largo_mm__gt=0,
            ).exists():
                self.add_error(
                    "impresora",
                    "Esta impresora no tiene medidas configuradas para el tamaño elegido.",
                )
        for field in (
            "apellido_nombre",
            "documento",
            "historia_clinica",
            "servicio",
            "alergias",
        ):
            value = cleaned_data.get(field, "")
            if any(ord(character) < 32 for character in value):
                self.add_error(field, "El texto no puede contener caracteres de control.")
        return cleaned_data
