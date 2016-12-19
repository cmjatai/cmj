from crispy_forms.helper import FormHelper
from crispy_forms.layout import Fieldset
from django import forms
from django.forms.models import ModelForm
from django.utils.translation import ugettext_lazy as _

from crispy_layout_mixin import to_row, SaplFormLayout
from sigad import models
from sigad.models import Documento, Classe


class UpLoadImportFileForm(forms.Form):
    import_file = forms.FileField(
        required=True,
        label=_('Arquivo formato ODF para Importanção')
    )

    def __init__(self, *args, **kwargs):
        super(UpLoadImportFileForm, self).__init__(*args, **kwargs)
        self.fields['import_file'].widget.attrs.update(
            {'multiple': 'multiple'})

error_messages = {
    'required': _('Este campo é obrigatório'),
    'invalid': _('Formato inválido.')
}


class ClasseForm(ModelForm):

    codigo = forms.IntegerField(
        label=Classe._meta.get_field('codigo').verbose_name)
    nome = forms.CharField(
        label=Classe._meta.get_field('nome').verbose_name)
    visibilidade = forms.ChoiceField(
        label=Classe._meta.get_field('visibilidade').verbose_name,
        choices=models.VISIBILIDADE_STATUS)
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

    class Meta:
        model = Classe
        fields = ['codigo',
                  'nome',
                  'visibilidade',
                  'perfil',
                  'descricao',
                  'parent'
                  ]

    def __init__(self, *args, **kwargs):

        row1 = to_row([
            ('codigo', 3),
            ('nome', 9),
        ])

        row2 = to_row([
            ('perfil', 6),
            ('visibilidade', 6),
        ])
        row3 = to_row([
            ('descricao', 12),
        ])

        self.helper = FormHelper()
        self.helper.layout = SaplFormLayout(

            Fieldset(_('Identificação Básica'),
                     row1, row2, row3,
                     css_class="large-12"))

        super(ClasseForm, self).__init__(*args, **kwargs)


class DocumentoForm(ModelForm):

    titulo = forms.CharField(label=_('Título'))
    descricao = forms.CharField(
        label=_('Descrição'),
        widget=forms.Textarea,
        required=False)
    texto = forms.CharField(
        label='Texto',
        widget=forms.Textarea,
        required=False)

    privacidade = forms.ChoiceField(
        required=True,
        label=_('Privacidade'),
        choices=models.VISIBILIDADE_STATUS,
        widget=forms.Select())

    data = forms.DateField(
        label=_('Data do Documento'),
        input_formats=['%d/%m/%Y'],
        required=True,
        widget=forms.DateInput(
            format='%d/%m/%Y'),
        error_messages=error_messages
    )
    medias_file = forms.FileField(
        required=False,
        label=_('Mídias deste Documento')
    )

    parent = forms.ModelChoiceField(queryset=Documento.objects.all(),
                                    widget=forms.HiddenInput(),
                                    required=False)

    pk = forms.IntegerField(widget=forms.HiddenInput(),
                            required=False)

    class Meta:
        model = Documento
        fields = ['titulo',
                  'data_documento',
                  'data_publicacao',
                  'hora_publicacao',
                  'descricao',
                  'texto',
                  'privacidade',
                  'parent',
                  'pk'
                  ]

    def __init__(self, *args, **kwargs):

        self.helper = FormHelper()
        self.helper.layout = SaplFormLayout(
            to_row([
                ('titulo', 6),
                ('data', 3),
                ('privacidade', 3),
            ]),
            to_row([
                ('descricao', 12)
            ]),
            to_row([
                ('texto', 12),
            ]),
            to_row([
                ('medias_file', 12),
            ])
        )

        super(DocumentoForm, self).__init__(*args, **kwargs)
        self.fields['medias_file'].widget.attrs.update(
            {'multiple': 'multiple'})
