from crispy_forms.helper import FormHelper
from crispy_forms.layout import Fieldset
from django import forms
from django.forms.models import ModelForm
from django.utils.translation import ugettext_lazy as _

from cmj.arq.models import ArqClasse, PERFIL_ARQCLASSE, ArqDoc, ARQCLASSE_FISICA,\
    ARQCLASSE_LOGICA
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
            ('titulo', 7),
            ('perfil', 3),
        ])

        row2 = to_row([
            ('descricao', 12),
        ])

        self.helper = FormHelper()
        self.helper.layout = SaplFormLayout(
            Fieldset(_('Identificação Básica'),
                     row1, row2,))

        super(ArqClasseForm, self).__init__(*args, **kwargs)


class ArqDocForm(ModelForm):

    classe_logica = forms.ModelChoiceField(
        queryset=ArqClasse.objects.filter(perfil=ARQCLASSE_LOGICA),
        required=False)

    classe_estrutural = forms.ModelChoiceField(
        queryset=ArqClasse.objects.filter(perfil=ARQCLASSE_FISICA),
        required=True)

    class Meta:
        model = ArqDoc
        fields = [
            'codigo',
            'data',
            'titulo',
            'descricao',
            'classe_logica',
            'classe_estrutural',
            'arquivo'

        ]

    def __init__(self, *args, **kwargs):

        row1 = to_row([
            ('codigo', 2),
            ('data', 3),
            ('titulo', 7),
        ])

        row2 = to_row([
            ('classe_logica', 6),
            ('classe_estrutural', 6),
        ])

        row3 = to_row([
            ('arquivo', 12),
        ])

        row4 = to_row([
            ('descricao', 12),
        ])

        self.helper = FormHelper()
        self.helper.layout = SaplFormLayout(
            Fieldset(_('Identificação Básica'),
                     row1, row2, row3, row4,))

        super(ArqDocForm, self).__init__(*args, **kwargs)
