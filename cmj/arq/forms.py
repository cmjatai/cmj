from crispy_forms.helper import FormHelper
from crispy_forms.layout import Fieldset
from django import forms
from django.forms.models import ModelForm
from django.utils.translation import ugettext_lazy as _

from cmj.utils import YES_NO_CHOICES
from sapl.crispy_layout_mixin import to_row, SaplFormLayout


"""
class ClasseForm(ModelForm):

    visibilidade = forms.ChoiceField(
        label=Classe._meta.get_field('visibilidade').verbose_name,
        choices=Documento.VISIBILIDADE_STATUS)
    perfil = forms.ChoiceField(
        label=Classe._meta.get_field('perfil').verbose_name,
        choices=models.PERFIL_CLASSE)
    descricao = forms.CharField(
        label=Classe._meta.get_field('descricao').verbose_name,
        widget=forms.Textarea,
        required=False)

    parent = forms.ModelChoiceField(
        queryset=Classe.objects.all(),
        widget=forms.HiddenInput(),
        required=False)

    url_redirect = forms.CharField(
        label=Classe._meta.get_field('url_redirect').verbose_name,
        required=False)

    class Meta:
        model = Classe
        fields = [
            'codigo',
            'titulo',
            'apelido',
            'visibilidade',
            'perfil',
            'descricao',
            'parent',
            'tipo_doc_padrao',
            'template_doc_padrao',
            'template_classe',
            'parlamentar',
            'list_in_mapa',
            'list_in_inf',
            'list_in_menu',
            'url_redirect'

        ]

    def __init__(self, *args, **kwargs):

        row1 = to_row([
            ('codigo', 2),
            ('titulo', 3),
            ('apelido', 3),
            ('perfil', 2),
            ('parlamentar', 2),
        ])

        row2 = to_row([
            ('visibilidade', 2),
            ('template_classe', 3),
            ('tipo_doc_padrao', 4),
            ('template_doc_padrao', 3),
        ])
        row4 = to_row([
            ('descricao', 12),
        ])
        row3 = to_row([
            ('list_in_mapa', 3),
            ('list_in_inf', 3),
            ('list_in_menu', 3),
            ('url_redirect', 3),
        ])

        self.helper = FormHelper()
        self.helper.layout = SaplFormLayout(
            Fieldset(_('Identificação Básica'),
                     row1, row2, row3, row4))

        super(ClasseForm, self).__init__(*args, **kwargs)
"""
