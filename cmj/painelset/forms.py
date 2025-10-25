
from os import name
from django import forms
from cmj.painelset.models import Cronometro, Evento, Individuo, RoleChoices
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Fieldset
from django.utils.translation import gettext_lazy as _
from image_cropping.widgets import get_attrs

from sapl.crispy_layout_mixin import SaplFormLayout, SaplFormHelper, to_row
from sapl.parlamentares.models import Parlamentar

class EventoForm(forms.ModelForm):

    # Adicionando campo duration ao formulário para no save criar o cronômetro
    duration = forms.DurationField(
        label=_("Duração prevista deste tipo de Evento"),
        required=True,
        help_text=_("Duração planejada do cronômetro para este evento (formato: HH:MM:SS)"),
        widget=forms.TextInput(attrs={'class': 'hora_hms'}),
        )

    individuos_extras = forms.IntegerField(
        label=_("Número de indivíduos extras"),
        required=True,
        initial=0,
        min_value=0,
        max_value=50,
        help_text=_("Número de indivíduos, além dos vinculados a parlamentares e tribunas, que este evento terá"),
    )

    tribunas = forms.IntegerField(
        label=_("Número de tribunas"),
        required=True,
        initial=0,
        min_value=0,
        max_value=5,
        help_text=_("Número de tribunas que este evento terá"),
    )

    vincular_parlamentares = forms.BooleanField(
        label=_("Vincular parlamentares"),
        required=False,
        initial=True,
        help_text=_("Se marcado, permite vincular indivíduos a parlamentares ativos."),
    )

    class Meta:
        model = Evento
        fields = [
            'name',
            'description',
            'duration',
            'start_previsto',
            'ips_mesas',
            'comunicar_com_mesas',
            ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        row1 = to_row([
            ('name', 6),
            ('start_previsto', 3),
            ('duration', 3),
            ('vincular_parlamentares', 4),
            ('tribunas', 4),
            ('individuos_extras', 4),
            ('comunicar_com_mesas', 3),
            ('ips_mesas', 9),
            ('description', 12),
        ])

        evento = self.instance
        if evento and evento.pk:
            self.fields['duration'].initial = evento.duration
            self.fields['individuos_extras'].initial = evento.individuos.filter(parlamentar__isnull=True, role=RoleChoices.INDIVIDUO).count()
            self.fields['tribunas'].initial = evento.individuos.filter(role=RoleChoices.TRIBUNA).count()
            self.fields['vincular_parlamentares'].initial = evento.individuos.filter(parlamentar__isnull=False).exists()

        self.helper = SaplFormHelper()
        self.helper.layout = SaplFormLayout(
            Fieldset(_('Dados Gerais'), row1), )

    def save(self, commit=True):

        evento = super().save(commit=commit)

        duration = self.cleaned_data.get('duration')
        individuos_extras = self.cleaned_data.get('individuos_extras')
        tribunas = self.cleaned_data.get('tribunas')
        vincular_parlamentares = self.cleaned_data.get('vincular_parlamentares')

        if vincular_parlamentares:
            parlamentares = Parlamentar.objects.filter(ativo=True).order_by('nome_parlamentar')
            for p in parlamentares:
                individuo, created = Individuo.objects.get_or_create(
                    name=p.nome_parlamentar,
                    role=RoleChoices.PARLAMENTAR,
                    evento=evento,
                    parlamentar=p,
                )

        qs_tribunas = Individuo.objects.filter(role=RoleChoices.TRIBUNA, evento=evento)
        for i in range(qs_tribunas.count() + 1, tribunas + 1):
            individuo, created = Individuo.objects.get_or_create(
                name=f'Tribuna {i}',
                role=RoleChoices.TRIBUNA,
                evento=evento,
            )

        qs_individuos_extras = Individuo.objects.filter(role=RoleChoices.INDIVIDUO, evento=evento)
        for i in range(qs_individuos_extras.count() + 1, individuos_extras + 1):
            individuo, created = Individuo.objects.get_or_create(
                name=f'Indivíduo {i}',
                role=RoleChoices.INDIVIDUO,
                evento=evento,
            )

        evento.individuos.reset_ordem()

        return evento

class IndividuoForm(forms.ModelForm):

    class Meta:
        model = Individuo
        fields = [
            'name',
            'role',
            'order',
            'canal',
            'microfone_sempre_ativo',
            'ips_mesas',
            'fotografia',
            'fotografia_cropping',
            'parlamentar',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        fotografia = self.fields['fotografia'].widget
        fotografia.attrs.update(
            get_attrs(self.instance.fotografia, 'fotografia')
        )
        if 'class' in fotografia.attrs:
            fotografia.attrs.pop('class')
