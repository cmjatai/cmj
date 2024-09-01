
from decimal import Decimal, ROUND_DOWN, ROUND_HALF_DOWN
import logging

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Fieldset, HTML, Div
from django import forms
from django.contrib.postgres.forms.array import SplitArrayField,\
    SplitArrayWidget
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.forms.models import ModelForm
from django.forms.widgets import HiddenInput, NumberInput
from django.utils.translation import ugettext_lazy as _

from cmj.loa.models import Loa, EmendaLoa, EmendaLoaParlamentar, OficioAjusteLoa,\
    RegistroAjusteLoa, RegistroAjusteLoaParlamentar
from sapl.crispy_layout_mixin import to_row, SaplFormLayout
from sapl.materia.models import MateriaLegislativa, TipoMateriaLegislativa
from sapl.parlamentares.models import Parlamentar
from sapl.utils import FileFieldCheckMixin


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
            cleaned_data['materia'] = None


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
            i.perc_disp_total / Decimal(100),
            rounding=ROUND_DOWN
        )

        i.disp_saude = quantize(
            i.receita_corrente_liquida *
            i.perc_disp_saude / Decimal(100),
            rounding=ROUND_DOWN)

        i.disp_diversos = quantize(
            i.receita_corrente_liquida *
            i.perc_disp_diversos / Decimal(100),
            rounding=ROUND_DOWN)

        # if i.disp_diversos + i.disp_saude != i.disp_total:
        #    i.disp_diversos = i.disp_total - i.disp_saude
        #    i.perc_disp_diversos = quantize(
        #        i.disp_diversos / i.receita_corrente_liquida * Decimal(100),
        #        rounding=ROUND_DOWN)

        i = super().save(commit)

        lps = i.loaparlamentar_set.all()
        count_lps = lps.count()

        idtp = quantize(i.disp_total / Decimal(count_lps),
                        rounding=ROUND_DOWN)
        idsp = quantize(i.disp_saude / Decimal(count_lps),
                        rounding=ROUND_DOWN)
        iddp = quantize(i.disp_diversos / Decimal(count_lps),
                        rounding=ROUND_DOWN)

        # if iddp + idsp != idtp:
        #    iddp = idtp - idsp

        for lp in lps:
            lp.disp_total = idtp
            lp.disp_saude = idsp
            lp.disp_diversos = iddp
            lp.save()

        return i


class DecimalInput(NumberInput):

    def get_context(self, name, value, attrs):
        context = NumberInput.get_context(self, name, value, attrs)
        return context


class EmendaLoaValorWidget(SplitArrayWidget):
    template_name = 'widget/parlamentares_valor_form.html'

    def __init__(self, widget, parlamentares=[], user=None, **kwargs):
        super().__init__(widget, size=len(parlamentares), **kwargs)
        self.parlamentares = parlamentares
        self.user = user

    def get_context(self, name, value, attrs=None):
        context = super().get_context(name, value, attrs)

        pw = zip(self.parlamentares, context['widget']['subwidgets'])
        for p, w in pw:

            w['label'] = p.nome_parlamentar
            w['attrs']['parlamentar_id'] = p.id

            if 'class' in self.attrs and 'class' in w['attrs']:
                w['attrs']['class'] = 'decimalinput numberinput form-control text-right'
                #w['attrs']['class'] + ' ' + self.attrs['class']

            if self.user and not self.user.has_perms(
                    ('loa.add_emendaloa', 'loa.change_emendaloa')):
                op = self.user.operadorautor_set.first()
                if not op or op and op.autor.autor_related != p:
                    w['attrs']['readonly'] = 'readonly'

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
        label='Finalidade',
        required=True,
        widget=forms.Textarea(attrs={'rows': 2}))

    indicacao = forms.CharField(
        label='Indicação',
        required=False)

    parlamentares__valor = SplitArrayField(
        forms.DecimalField(
            required=False,
            max_digits=14,
            decimal_places=2,
            widget=DecimalInput
        ),
        10,
        label='Valores por Parlamentar',
        required=False
    )

    class Meta:
        model = EmendaLoa
        fields = [
            'tipo', 'fase', 'valor',
            'materia', 'tipo_materia', 'numero_materia', 'ano_materia',
            'indicacao',
            'finalidade',
            'parlamentares__valor'
        ]

    def __init__(self, *args, **kwargs):

        self.creating = kwargs['initial'].pop('creating', None)
        self.user = kwargs['initial'].pop('user', None)
        self.loa = kwargs['initial']['loa']
        self.parls = list(self.loa.parlamentares.order_by('nome_parlamentar'))
        self.full_editor = full_editor = self.user.has_perm(
            'loa.emendaloa_full_editor') and not self.user.is_superuser

        row1 = to_row([
            ('tipo', 3),
            ('fase', 4),
            ('valor', 5),
        ])

        row2 = to_row([
            ('tipo_materia', 6),
            ('numero_materia', 3),
            ('ano_materia', 3),
            ('materia', 0),
        ])

        row3 = [
            ('indicacao', 12),
            ('finalidade', 12),
        ]
        if not full_editor:
            row3.append(('parlamentares__valor', 12))

        row3 = to_row(row3)

        row_form = to_row([
            ([row1, row2, row3, ], 12)
        ])
        if not self.creating:
            row_form = to_row([
                ([row1, row2, row3, ], 7),
                (Div(css_class='container-preview'), 5)
            ])

        self.helper = FormHelper()
        self.helper.layout = SaplFormLayout(
            Fieldset(_('Identificação Básica'), row_form))

        super().__init__(*args, **kwargs)

        if self.user.operadorautor_set.exists() or not self.user.has_perms(
            ('loa.add_emendaloa', 'loa.change_emendaloa')
        ):
            self.fields['fase'].widget.attrs['disabled'] = True
            self.fields['fase'].initial = EmendaLoa.PROPOSTA
            self.fields['fase'].required = False

            self.fields['valor'].widget.attrs['disabled'] = 'disabled'
            self.fields['valor'].widget.attrs['readonly'] = 'readonly'
            self.fields['valor'].widget.attrs['class'] = 'text-right'
            self.fields['valor'].required = False

            self.fields['tipo_materia'].widget = HiddenInput()
            self.fields['numero_materia'].widget = HiddenInput()
            self.fields['ano_materia'].widget = HiddenInput()

        if full_editor:
            self.fields.pop('parlamentares__valor')
            return

        initial_pv = []
        if self.instance.pk:
            initial_pv = [[p, Decimal('0.00')] for p in self.parls]
            for i, (p, v) in enumerate(initial_pv):
                ipv = p.emendaloaparlamentar_set.filter(
                    emendaloa=self.instance).first()
                if ipv:
                    initial_pv[i][1] = ipv.valor
        self.initial['parlamentares__valor'] = list(
            map(lambda x: x[1], initial_pv))

        fpv = self.fields['parlamentares__valor']
        fpv.max_length = len(self.parls)
        fpv.size = fpv.max_length
        fpv.widget = EmendaLoaValorWidget(
            widget=self.fields['parlamentares__valor'].base_field.widget,
            parlamentares=self.parls,
            user=self.user if self.instance.pk else None,
            attrs={'class': 'text-right'}
        )

    def clean(self):
        super().clean()
        cleaned_data = self.cleaned_data

        return cleaned_data

    def save(self, commit=True):

        i_init = self.instance

        if not self.full_editor:
            soma = sum(
                list(
                    filter(
                        lambda x: x, self.cleaned_data['parlamentares__valor']
                    )
                )
            )
            i_init.valor = soma

        try:
            i = super().save(commit)
        except Exception as e:
            raise ValidationError('Erro')

        if not self.full_editor:
            i.parlamentares.clear()

            pv = zip(self.parls, self.cleaned_data['parlamentares__valor'])

            for p, v in pv:
                if not v:
                    continue
                elp = EmendaLoaParlamentar()
                elp.emendaloa = i
                elp.parlamentar = p
                elp.valor = v
                elp.save()

        return i


class OficioAjusteLoaForm(FileFieldCheckMixin, ModelForm):

    class Meta:
        model = OficioAjusteLoa
        fields = [
            'epigrafe',
            'parlamentares',
            'arquivo'
        ]

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        self.loa = kwargs['initial']['loa']
        self.parlamentares = self.loa.parlamentares.order_by(
            'nome_parlamentar')

        self.fields['parlamentares'].choices = [
            (p.pk, p) for p in self.parlamentares
        ]


class RegistroAjusteLoaForm(ModelForm):

    emendaloa = forms.ModelChoiceField(
        required=False,
        queryset=EmendaLoa.objects.all())

    parlamentares__valor = SplitArrayField(
        forms.DecimalField(required=False, max_digits=14,
                           decimal_places=2,), 10,
        label='Valores por Parlamentar',
        required=False
    )

    class Meta:
        model = RegistroAjusteLoa
        fields = [
            'parlamentares__valor',
            'tipo',
            'emendaloa',
            'descricao'
        ]

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        self.oficioajusteloa = kwargs['initial']['oficioajusteloa']
        self.parlamentares = self.oficioajusteloa.parlamentares.all()

        self.emendas = set()
        for p in self.parlamentares:
            emendas = p.emendaloaparlamentar_set.filter(
                emendaloa__loa=self.oficioajusteloa.loa
            ).order_by('emendaloa__materia')
            self.emendas.update(map(lambda e: e.emendaloa, emendas))

        self.fields['emendaloa'].choices = [('', '---------')] + [
            (e.pk, f'{e} - {e.materia.epigrafe_short if e.materia else ""}') for e in self.emendas
        ]

        initial_pv = []
        if self.instance.pk:
            initial_pv = [[p, Decimal('0.00')] for p in self.parlamentares]
            for i, (p, v) in enumerate(initial_pv):
                ipv = p.registroajusteloaparlamentar_set.filter(
                    registro=self.instance).first()
                if ipv:
                    initial_pv[i][1] = ipv.valor
        self.initial['parlamentares__valor'] = list(
            map(lambda x: x[1], initial_pv))

        fpv = self.fields['parlamentares__valor']
        fpv.max_length = self.parlamentares.count()
        fpv.size = self.parlamentares.count()
        fpv.widget = EmendaLoaValorWidget(
            widget=self.fields['parlamentares__valor'].base_field.widget,
            parlamentares=list(self.parlamentares),
            user=None,
            attrs={'class': 'text-right'}
        )

    def save(self, commit=True):

        i_init = self.instance

        soma = sum(
            list(
                filter(
                    lambda x: x, self.cleaned_data['parlamentares__valor']
                )
            )
        )

        try:
            i = super().save(commit)
        except Exception as e:
            raise ValidationError('Erro')

        i.parlamentares_valor.clear()

        pv = zip(self.parlamentares, self.cleaned_data['parlamentares__valor'])

        for p, v in pv:
            if not v:
                continue
            r = RegistroAjusteLoaParlamentar()
            r.registro = i
            r.parlamentar = p
            r.valor = v
            r.save()

        return i
