
from decimal import Decimal, ROUND_DOWN, ROUND_HALF_DOWN
import logging

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Fieldset
from django import forms
from django.contrib.postgres.forms.array import SplitArrayField,\
    SplitArrayWidget
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.forms.fields import MultiValueField
from django.forms.models import ModelForm
from django.utils.translation import ugettext_lazy as _

from cmj.loa.models import Loa, EmendaLoa, EmendaLoaParlamentar
from sapl.crispy_layout_mixin import to_row, SaplFormLayout
from sapl.materia.models import MateriaLegislativa, TipoMateriaLegislativa
from sapl.parlamentares.models import Parlamentar


logger = logging.getLogger(__name__)


def quantize(value, decimal_places='0.01', rounding=ROUND_HALF_DOWN) -> Decimal:
    return value.quantize(
        Decimal(decimal_places),
        rounding=rounding
    )


class MateriaCheckFormMixin:

    def clean(self):

        cleaned_data = super().clean()
        if not self.is_valid():
            return cleaned_data

        materia = cleaned_data['numero_materia']
        ano_materia = cleaned_data['ano_materia']
        tipo_materia = cleaned_data['tipo_materia']

        if materia and ano_materia and tipo_materia:
            try:
                logger.debug("Tentando obter MateriaLegislativa %s nº %s/%s." %
                             (tipo_materia, materia, ano_materia))
                materia = MateriaLegislativa.objects.get(
                    numero=materia,
                    ano=ano_materia,
                    tipo=tipo_materia)
            except ObjectDoesNotExist:
                msg = _('A matéria %s nº %s/%s não existe no cadastro'
                        ' de matérias legislativas.' % (tipo_materia, materia, ano_materia))
                logger.error('A MateriaLegislativa %s nº %s/%s não existe no cadastro'
                             ' de matérias legislativas.' % (tipo_materia, materia, ano_materia))
                raise ValidationError(msg)
            else:
                logger.info("MateriaLegislativa %s nº %s/%s obtida com sucesso." %
                            (tipo_materia, materia, ano_materia))
                cleaned_data['materia'] = materia

        else:
            campos = [materia, tipo_materia, ano_materia]
            if campos.count(None) + campos.count('') < len(campos):
                msg = _(
                    'Preencha todos os campos relacionados à Matéria Legislativa')
                logger.error('Algum campo relacionado à MatériaLegislativa %s nº %s/%s \
                                não foi preenchido.' % (tipo_materia, materia, ano_materia))
                raise ValidationError(msg)


class LoaForm(MateriaCheckFormMixin, ModelForm):

    tipo_materia = forms.ModelChoiceField(
        label=_('Tipo Matéria'),
        required=False,
        queryset=TipoMateriaLegislativa.objects.all(),
        empty_label='Selecione',
    )

    numero_materia = forms.CharField(
        label='Número Matéria', required=False)

    ano_materia = forms.CharField(
        label='Ano Matéria',
        required=False)

    materia = forms.ModelChoiceField(
        required=False,
        widget=forms.HiddenInput(),
        queryset=MateriaLegislativa.objects.all())

    parlamentares = forms.ModelMultipleChoiceField(
        required=True,
        widget=forms.CheckboxSelectMultiple(),
        queryset=Parlamentar.objects.all())

    class Meta:
        model = Loa
        fields = [
            'ano',
            'materia', 'tipo_materia', 'numero_materia', 'ano_materia',
            'receita_corrente_liquida',
            'publicado',
            'perc_disp_total',
            'perc_disp_saude',
            'perc_disp_diversos',
            'parlamentares'
        ]

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        self.fields['parlamentares'].choices = [
            (p.pk, p) for p in Parlamentar.objects.filter(ativo=True)
        ]

    def save(self, commit=True):

        i = self.instance

        i.disp_total = quantize(
            i.receita_corrente_liquida *
            i.perc_disp_total / Decimal(100))

        i.disp_saude = quantize(
            i.receita_corrente_liquida *
            i.perc_disp_saude / Decimal(100))

        i.disp_diversos = quantize(
            i.receita_corrente_liquida *
            i.perc_disp_diversos / Decimal(100))

        if i.disp_diversos + i.disp_saude != i.disp_total:
            i.disp_diversos = i.disp_total - i.disp_saude
            i.perc_disp_diversos = quantize(
                i.disp_diversos / i.receita_corrente_liquida * Decimal(100))

        i = super().save(commit)

        lps = i.loaparlamentar_set.all()
        count_lps = lps.count()

        idtp = quantize(i.disp_total / Decimal(count_lps))
        idsp = quantize(i.disp_saude / Decimal(count_lps))
        iddp = quantize(i.disp_diversos / Decimal(count_lps))

        if iddp + idsp != idtp:
            iddp = idtp - idsp

        for lp in lps:
            lp.disp_total = idtp
            lp.disp_saude = idsp
            lp.disp_diversos = iddp
            lp.save()

        return i


class EmendaLoaValorWidget(SplitArrayWidget):
    template_name = 'widget/parlamentares_valor_form.html'

    def __init__(self, widget, parlamentares=[], **kwargs):
        super().__init__(widget, size=len(parlamentares), **kwargs)
        self.parlamentares = parlamentares

    def get_context(self, name, value, attrs=None):
        context = super().get_context(name, value, attrs)

        pw = zip(self.parlamentares, context['widget']['subwidgets'])
        for p, w in pw:
            w['label'] = p.nome_parlamentar
            if 'class' in self.attrs:
                w['attrs']['class'] += ' ' + self.attrs['class']
        return context


class EmendaLoaForm(MateriaCheckFormMixin, ModelForm):

    tipo_materia = forms.ModelChoiceField(
        label=_('Tipo Matéria'),
        required=False,
        queryset=TipoMateriaLegislativa.objects.all(),
        empty_label='Selecione',
    )

    numero_materia = forms.CharField(
        label='Número Matéria', required=False)

    ano_materia = forms.CharField(
        label='Ano Matéria',
        required=False)

    materia = forms.ModelChoiceField(
        required=False,
        widget=forms.HiddenInput(),
        queryset=MateriaLegislativa.objects.all())

    finalidade = forms.CharField(
        label='Finalidade', required=True)

    parlamentares__valor = SplitArrayField(
        forms.DecimalField(required=False, max_digits=14,
                           decimal_places=2,), 10,
        label='Valores por Parlamentar',
        required=False
    )

    class Meta:
        model = EmendaLoa
        fields = [
            'tipo',
            'fase',
            'materia', 'tipo_materia', 'numero_materia', 'ano_materia',
            'valor',
            'finalidade',
            'parlamentares__valor'
        ]

    def __init__(self, *args, **kwargs):

        row1 = to_row([
            ('tipo', 2),
            ('fase', 3),
            ('tipo_materia', 3),
            ('numero_materia', 2),
            ('ano_materia', 2),
            ('materia', 0),
        ])

        row2 = to_row([
            ('valor', 3),
            ('finalidade', 9),
        ])

        row3 = to_row([
            ('parlamentares__valor', 12),
        ])

        self.helper = FormHelper()
        self.helper.layout = SaplFormLayout(
            Fieldset(_('Dados Gerais'),
                     row1, row2, row3,))

        super().__init__(*args, **kwargs)

        self.loa = kwargs['initial']['loa']
        self.parlamentares = self.loa.parlamentares.order_by(
            'nome_parlamentar')

        initial_pv = []
        if self.instance.pk:
            initial_pv = [[p, Decimal('0.00')] for p in self.parlamentares]
            for i, (p, v) in enumerate(initial_pv):
                ipv = p.emendaloaparlamentar_set.filter(
                    emendaloa=self.instance).first()
                if ipv:
                    initial_pv[i][1] = ipv.valor
        self.initial['parlamentares__valor'] = list(
            map(lambda x: x[1], initial_pv))

        fpv = self.fields['parlamentares__valor']
        fpv.max_length = self.parlamentares.count()
        fpv.widget = EmendaLoaValorWidget(
            widget=self.fields['parlamentares__valor'].base_field.widget,
            parlamentares=list(self.parlamentares),
            attrs={'class': 'text-right'}
        )

        # self.fields['parlamentares'].choices = [
        #    (p.pk, p) for p in parlamentares
        #]

    def clean(self):
        super().clean()
        cleaned_data = self.cleaned_data

        soma = sum(
            list(
                filter(
                    lambda x: x, cleaned_data['parlamentares__valor']
                )
            )
        )

        if soma != cleaned_data['valor']:
            msg = _('A Soma dos Valores Por Parlamentar não '
                    'coincide com o Valor Global da emenda')
            logger.error(msg)
            raise ValidationError(msg)
        return cleaned_data

    def save(self, commit=True):
        try:
            i = super().save(commit)
        except Exception as e:
            raise ValidationError('erro')
        i.parlamentares.clear()

        pv = zip(self.parlamentares, self.cleaned_data['parlamentares__valor'])

        for p, v in pv:
            if not v:
                continue
            elp = EmendaLoaParlamentar()
            elp.emendaloa = i
            elp.parlamentar = p
            elp.valor = v
            elp.save()

        return i
