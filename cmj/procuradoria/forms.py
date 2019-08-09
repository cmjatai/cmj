
import logging

from crispy_forms.bootstrap import FormActions
from crispy_forms.layout import Submit, Layout, Fieldset
from django import forms
from django.core.exceptions import ValidationError
from django.forms.models import ModelForm
from django.utils import timezone
import django_filters

from cmj.crispy_layout_mixin import to_row, SaplFormLayout
from cmj.procuradoria.models import DocumentoProcuradoria
from cmj.settings.medias import MAX_DOC_UPLOAD_SIZE
from cmj.utils import choice_anos_com_documentoprocuradoria
from sapl.crispy_layout_mixin import SaplFormHelper
from sapl.utils import AnoNumeroOrderingFilter, FilterOverridesMetaMixin,\
    FileFieldCheckMixin


class DocumentoProcuradoriaFilterSet(django_filters.FilterSet):

    ano = django_filters.ChoiceFilter(
        required=False,
        label='Ano',
        choices=choice_anos_com_documentoprocuradoria)

    ementa = django_filters.CharFilter(
        label=_('Contem na Ementa'),
        lookup_expr='icontains')

    interessado = django_filters.CharFilter(
        label=_('Contem no Interessado'),
        lookup_expr='icontains')

    o = AnoNumeroOrderingFilter(help_text='')

    class Meta(FilterOverridesMetaMixin):
        model = DocumentoProcuradoria
        fields = ['tipo',
                  'numero',
                  'ano',
                  'data',
                  'ementa'
                  'interessado']

    def __init__(self, *args, **kwargs):
        super(DocumentoProcuradoriaFilterSet, self).__init__(*args, **kwargs)

        row1 = to_row(
            [('tipo', 8),
             ('o', 4), ])

        row2 = to_row(
            [('numero', 4),
             ('ano', 4),
             ('data', 4)])

        row3 = to_row(
            [('interessado', 6),
             ('assunto', 6)])

        buttons = FormActions(

            Submit('pesquisar', _('Pesquisar'), css_class='float-right',
                   onclick='return true;'),
            css_class='form-group row justify-content-between',
        )

        self.form.helper = SaplFormHelper()
        self.form.helper.form_method = 'GET'
        self.form.helper.layout = Layout(
            Fieldset(_('Pesquisar Documento'),
                     row1, row2,
                     row3,
                     buttons,)
        )


class DocumentoProcuradoriaForm(FileFieldCheckMixin, ModelForm):

    logger = logging.getLogger(__name__)

    data = forms.DateField(initial=timezone.now)

    class Meta:
        model = DocumentoProcuradoria
        fields = ['tipo',
                  'numero',
                  'ano',
                  'data',
                  'ementa',
                  'interessado',
                  'observacao',
                  'resumo',
                  'texto_integral'
                  ]

    def clean(self):
        super(DocumentoProcuradoriaForm, self).clean()

        cleaned_data = self.cleaned_data

        if not self.is_valid():
            return cleaned_data

        numero_documento = int(self.cleaned_data['numero'])
        tipo_documento = int(self.data['tipo'])
        ano_documento = int(self.data['ano'])

        # não permite atualizar para numero/ano/tipo existente
        if self.instance.pk:
            mudanca_doc = numero_documento != self.instance.numero \
                or ano_documento != self.instance.ano \
                or tipo_documento != self.instance.tipo.pk

        if not self.instance.pk or mudanca_doc:
            doc_exists = DocumentoProcuradoria.objects.filter(numero=numero_documento,
                                                              tipo=tipo_documento,
                                                              ano=ano_documento).exists()
            if doc_exists:
                self.logger.error("DocumentoProcuradoria (numero={}, tipo={} e ano={}) já existe."
                                  .format(numero_documento, tipo_documento, ano_documento))
                raise ValidationError(_('Documento já existente'))

        texto_integral = self.cleaned_data.get('texto_integral', False)

        if texto_integral and texto_integral.size > MAX_DOC_UPLOAD_SIZE:
            raise ValidationError("O arquivo Texto Integral deve ser menor que {0:.1f} mb, o tamanho atual desse arquivo é {1:.1f} mb"
                                  .format((MAX_DOC_UPLOAD_SIZE / 1024) / 1024, (texto_integral.size / 1024) / 1024))

        return self.cleaned_data

    def __init__(self, *args, **kwargs):

        row1 = to_row(
            [('tipo', 5), ('numero', 2), ('ano', 2), ('data', 3), ])

        row3 = to_row(
            [('ementa', 12)])

        row4 = to_row(
            [('interessado', 8)])

        row5 = to_row(
            [('texto_integral', 12)])

        row6 = to_row(
            [('observacao', 12)])

        row7 = to_row(
            [('resumo', 12)])

        self.helper = SaplFormHelper()
        self.helper.layout = SaplFormLayout(
            Fieldset(_('Identificação Básica'),
                     row1, row3, row4, row5),
            Fieldset(_('Outras Informações'),
                     row6, row7))
        super(DocumentoProcuradoriaForm, self).__init__(
            *args, **kwargs)
