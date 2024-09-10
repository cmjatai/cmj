
from decimal import Decimal, ROUND_DOWN, ROUND_HALF_DOWN
import logging
import re

from crispy_forms.bootstrap import FormActions
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Fieldset, HTML, Div, Button, Submit, Layout
from django import forms
from django.contrib.postgres.forms.array import SplitArrayField,\
    SplitArrayWidget
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.forms.models import ModelForm
from django.forms.widgets import HiddenInput, NumberInput
from django.template.base import Template
from django.template.context import Context
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _
from django_filters.filters import ChoiceFilter, MultipleChoiceFilter,\
    ModelMultipleChoiceFilter, CharFilter
from django_filters.filterset import FilterSet
import yaml

from cmj.loa.models import Loa, EmendaLoa, EmendaLoaParlamentar, OficioAjusteLoa,\
    RegistroAjusteLoa, RegistroAjusteLoaParlamentar, EmendaLoaRegistroContabil
from sapl.crispy_layout_mixin import to_row, SaplFormLayout, SaplFormHelper
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
        required=False,
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
            'parlamentares',
            'yaml_obs'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['parlamentares'].choices = [
            (p.pk, p) for p in Parlamentar.objects.filter(ativo=True)
        ]

    def clean(self):
        cd = super().clean()

        if not cd:
            cd = self.cleaned_data

        try:
            yo = yaml.full_load(cd['yaml_obs'])
            print(yo)
        except Exception as e:
            raise ValidationError(
                'Erro na validação das observações de Rodapé.')

        return cd

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

        if count_lps:
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
    template_name = 'loa/widget/parlamentares_valor_form.html'

    def __init__(self, widget, parlamentares=[], elps=[], user=None, **kwargs):
        super().__init__(widget, size=len(parlamentares), **kwargs)
        self.parlamentares = parlamentares
        self.elps = elps
        self.user = user

    def get_context(self, name, value, attrs=None):
        context = super().get_context(name, value, attrs)

        pw = zip(self.parlamentares, context['widget']['subwidgets'])
        for p, w in pw:

            w['label'] = p.nome_parlamentar
            w['attrs']['parlamentar_id'] = p.id

            if 'class' in self.attrs and 'class' in w['attrs']:
                w['attrs']['class'] = 'decimalinput numberinput form-control text-right'

            if self.user and not self.user.has_perms(
                    ('loa.add_emendaloa', 'loa.change_emendaloa')):
                op = self.user.operadorautor_set.first()
                if not op or op and p not in self.elps:
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
        required=True)

    indicacao = forms.CharField(
        label='Indicação',
        required=False)

    parlamentares__valor = SplitArrayField(
        forms.DecimalField(
            required=False,
            min_value=Decimal('0.00'),
            max_digits=14,
            decimal_places=2,
            widget=DecimalInput
        ),
        10,
        label='Valores por Parlamentar',
        required=False
    )

    # registrocontabil_set = forms.ModelChoiceField(
    #    label='',
    # required=False,
    #    queryset=EmendaLoaRegistroContabil.objects.all(),
    #    widget=forms.CheckboxSelectMultiple,
    #)

    ano_loa = forms.CharField(
        label='',
        widget=forms.HiddenInput(),
        required=False)

    busca_despesa = forms.CharField(
        label='Buscar', required=False,)

    valor_despesa = forms.DecimalField(
        label='Valor da Despesa', required=False, max_digits=14, decimal_places=2,)

    despesa_codigo = forms.CharField(
        label='Código', required=False,)

    despesa_orgao = forms.CharField(
        label='Orgão', required=False,)
    despesa_unidade = forms.CharField(
        label='Unidade', required=False,)

    despesa_especificacao = forms.CharField(
        label='Descrição da Ação', required=False,)

    despesa_natureza = forms.CharField(
        label='Natureza', required=False,)

    class Meta:
        model = EmendaLoa
        fields = [
            'tipo', 'fase', 'valor',
            'materia', 'tipo_materia', 'numero_materia', 'ano_materia',
            'prefixo_indicacao', 'indicacao',
            'prefixo_finalidade', 'finalidade',
            'parlamentares__valor',
            'busca_despesa', 'ano_loa',  # 'registrocontabil_set'
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
            ('fase', 5),
            ('valor', 4),

            ('ano_loa', 0),
        ])

        row2 = to_row([
            ('tipo_materia', 6),
            ('numero_materia', 3),
            ('ano_materia', 3),
            ('materia', 0),
        ])

        row3 = [
            ('prefixo_indicacao', 3),
            ('indicacao', 9),
            ('prefixo_finalidade', 3),
            ('finalidade', 9),
        ]

        if not full_editor:
            row3.append(('parlamentares__valor', 12))

        row3 = to_row(row3)

        rows_base = [row1, row2, row3, ]

        if full_editor or self.user.is_superuser:
            row4_1 = to_row([
                ('busca_despesa', 3),

                ('despesa_orgao', 2),
                ('despesa_unidade', 2),
                ('despesa_codigo', 3),
                ('despesa_natureza', 2),
                ('valor_despesa', 3),
                ('despesa_especificacao', 'col'),
                (HTML('''
                    <button type="button" id="add_registro" class="btn btn-primary">+</button>
                '''), 'col-1'),


                (Div(css_class='busca-render'), 12)

            ])
            row4_2 = to_row([
                (Div(css_class='registro-render'), 12),
            ])

            row4 = to_row([
                (Fieldset(_('Registrar Deduções e Inserções'), row4_1), 12),
                (Fieldset(_('Registros das Despesas Orçamentárias'), row4_2), 12)
            ])

            rows_base.append(row4)

        row_form = to_row([
            (rows_base, 12)
        ])
        if not self.creating:
            row_form = to_row([
                (rows_base, 7),
                (Div(css_class='container-preview'), 5)
            ])

        self.helper = FormHelper()
        btns = {
            'cancel_label': None,
            'save_label': 'Encerrar Edição'
        } if full_editor else {}
        self.helper.layout = SaplFormLayout(
            Fieldset(_('Dados Gerais'), row_form), **btns)

        super().__init__(*args, **kwargs)

        self.initial['ano_loa'] = self.loa.ano

        if not self.user.is_superuser and (
            self.user.operadorautor_set.exists() or not self.user.has_perms(
                ('loa.add_emendaloa', 'loa.change_emendaloa'))):
            self.fields['fase'].choices = EmendaLoa.FASE_CHOICE[
                :1 if self.creating else 2]

            if full_editor and self.instance.pk and self.instance.fase < EmendaLoa.APROVACAO_LEGISLATIVA:
                self.fields['fase'].widget.attrs['class'] = 'is-invalid'
                self.fields['fase'].choices = EmendaLoa.FASE_CHOICE[:4]

            if self.instance.pk and self.instance.fase >= EmendaLoa.APROVACAO_LEGISLATIVA:
                self.fields['fase'].choices = EmendaLoa.FASE_CHOICE

            self.fields['valor'].widget.attrs['disabled'] = 'disabled'
            self.fields['valor'].widget.attrs['readonly'] = 'readonly'
            self.fields['valor'].widget.attrs['class'] = 'text-right'
            self.fields['valor'].required = False

            self.fields['tipo_materia'].widget = HiddenInput()
            self.fields['numero_materia'].widget = HiddenInput()
            self.fields['ano_materia'].widget = HiddenInput()

        if full_editor or self.user.is_superuser:
            if self.instance.pk:
                self.initial['valor_despesa'] = Decimal('0.00')

                #rclist = self.instance.registrocontabil_set.all()
                # self.fields['registrocontabil_set'].choices = [
                #    (rc.id, str(rc)) for rc in rclist]
                # self.initial['registrocontabil_set'] = rclist.values_list(
                #    'id', flat=True)

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

        elps = list(map(lambda x: x[0], filter(lambda y: y[1], initial_pv)))

        fpv = self.fields['parlamentares__valor']
        fpv.max_length = len(self.parls)
        fpv.size = fpv.max_length
        fpv.widget = EmendaLoaValorWidget(
            widget=self.fields['parlamentares__valor'].base_field.widget,
            parlamentares=self.parls,
            user=self.user if self.instance.pk else None,
            elps=elps,
            attrs={'class': 'text-right'}
        )

    def clean(self):
        super().clean()
        cleaned_data = self.cleaned_data

        if 'parlamentares__valor'in cleaned_data:
            if not self.user.is_superuser and self.user.operadorautor_set.exists():
                pv = {k: v for k, v in zip(
                    self.parls, self.cleaned_data['parlamentares__valor'])}

                p = self.user.operadorautor_set.first().autor.autor_related
                if not pv[p]:
                    raise ValidationError(
                        f'É obrigatório o preenchimento do valor ligado a seu Parlamentar: {p}.')

        return cleaned_data

    def save(self, commit=True):

        i_init = self.instance

        if 'parlamentares__valor' in self.cleaned_data:
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
            if 'parlamentares__valor' in self.cleaned_data:
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


class EmendaLoaFilterSet(FilterSet):

    class LoaParlModelMultipleChoiceFilter(ModelMultipleChoiceFilter):
        def get_queryset(self, request):
            return self.parent.loa.parlamentares.all()

    fase = MultipleChoiceFilter(
        required=False,
        choices=EmendaLoa.FASE_CHOICE,
        label=_('Fases'),
        widget=forms.CheckboxSelectMultiple
    )

    parlamentares = LoaParlModelMultipleChoiceFilter(
        queryset=Parlamentar.objects.all(),
        widget=forms.CheckboxSelectMultiple
    )

    class Meta:
        class Form(forms.Form):
            crispy_field_template = 'fase', 'parlamentares'
        model = EmendaLoa
        fields = ['fase', 'parlamentares', 'indicacao']
        form = Form

    class ELSaplFormHelper(SaplFormHelper):

        def render_layout(self, form, context, template_pack=None):
            html = super().render_layout(form, context)
            html = html.replace('\n', ' ')
            while '  ' in html:
                html = html.replace('  ', ' ')
            html = html.replace(' > ', '>')
            html = html.replace('> ', '>')
            html = html.replace(' <', '<')
            html = re.sub(r'(</)(\w*)(>)', '\\1\\2\\3\n', html)

            html = re.sub(
                '<div class="">',
                '<div class="container-avatar d-flex justify-content-center w-100">',
                html, count=1)

            html_parts = []
            for n in re.finditer(r'<input.+name="(\w+)".+value="(\d+)"><label.*>(.*)</label>', html):
                html_parts.append([n.start(), n.end(), list(n.groups())])

            html_parts.reverse()
            label_layout = """{% load cropping common_tags %}
            <span class="avatar avatar6 {{active}}" >
                <img src="{% cropped_thumbnail p "fotografia_cropping" %}" alt="{{p.nome_parlamentar}}" title="{{p.nome_parlamentar}}">
            </span>
            """
            template = Template(label_layout)

            for x1, x2, (key, idp, nome) in html_parts:
                if key == 'fase':
                    continue
                lp = len(nome)

                p = Parlamentar.objects.get(pk=idp)
                ctx = {'p': p,
                       'active': 'active' if 'checked' in html[x1:x2] else ''}
                context = Context()
                context.update(ctx)
                trendered = template.render(context=context)
                html = html[:x2 - 8 - lp] + trendered + html[x2 - 8:]
            return mark_safe(html)

    def __init__(self, *args, **kwargs):

        self.loa = kwargs.pop('loa')
        super().__init__(*args, **kwargs)

        row = to_row(
            [
                ('parlamentares', 12),
                ('fase', 12),
            ]
        )

        fields = [row, ]
        self.form.helper = EmendaLoaFilterSet.ELSaplFormHelper()
        self.form.helper.form_method = 'GET'
        self.form.helper.form_class = 'container'
        self.form.helper.layout = SaplFormLayout(
            *fields,
            cancel_label=None,
            save_label=_('Filtrar')
        )

        if self.loa.materia and self.loa.materia.normajuridica():
            self.form.fields['fase'].choices = EmendaLoa.FASE_CHOICE[4:]
        else:
            self.form.fields['fase'].choices = EmendaLoa.FASE_CHOICE[:4]
