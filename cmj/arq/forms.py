from crispy_forms.helper import FormHelper
from crispy_forms.layout import Fieldset
from django import forms
from django.forms.models import ModelForm
from django.utils.translation import ugettext_lazy as _

from cmj.arq.models import ArqClasse, PERFIL_ARQCLASSE
from cmj.utils import YES_NO_CHOICES
from sapl.crispy_layout_mixin import to_row, SaplFormLayout


class ArqClasseForm(ModelForm):

    perfil = forms.ChoiceField(
        label=ArqClasse._meta.get_field('perfil').verbose_name,
        choices=PERFIL_ARQCLASSE)
    descricao = forms.CharField(
        label=ArqClasse._meta.get_field('descricao').verbose_name,
        widget=forms.Textarea,
        required=False)

    parent = forms.ModelChoiceField(
        queryset=ArqClasse.objects.all(),
        widget=forms.HiddenInput(),
        required=False)

    class Meta:
        model = ArqClasse
        fields = [
            'codigo',
            'titulo',
            'perfil',
            'descricao',
            'parent',

        ]

    def __init__(self, *args, **kwargs):

        row1 = to_row([
            ('codigo', 2),
            ('titulo', 5),
            ('perfil', 2),
        ])

        row2 = to_row([
            ('descricao', 12),
        ])

        self.helper = FormHelper()
        self.helper.layout = SaplFormLayout(
            Fieldset(_('Identificação Básica'),
                     row1, row2,))

        super(ArqClasseForm, self).__init__(*args, **kwargs)
