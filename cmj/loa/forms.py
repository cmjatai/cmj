from decimal import Decimal, ROUND_DOWN, ROUND_HALF_DOWN
from hmac import new
import logging
import re

from crispy_forms.bootstrap import FieldWithButtons, StrictButton
from crispy_forms.layout import Field

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Fieldset, HTML, Div, Submit
from django import forms
from django.contrib.postgres.forms.array import SplitArrayField, \
    SplitArrayWidget
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db.models import Q
from django.forms.models import ModelForm
from django.forms.widgets import HiddenInput, NumberInput, TextInput
from django.template.base import Template
from django.template.context import Context
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from django_filters.filters import MultipleChoiceFilter, \
    ModelMultipleChoiceFilter, CharFilter, ChoiceFilter
from django_filters.filterset import FilterSet
from numpy import full
import yaml

from cmj import loa
from cmj.loa.models import ArquivoPrestacaoContaLoa, Despesa, DespesaConsulta, EmendaLoaRegistroContabil, Entidade, Loa, EmendaLoa, EmendaLoaParlamentar, OficioAjusteLoa, PrestacaoContaLoa, PrestacaoContaRegistro, \
    RegistroAjusteLoa, RegistroAjusteLoaParlamentar, UnidadeOrcamentaria,\
    Agrupamento, quantize
from cmj.utils import normalize, DecimalField
from sapl.crispy_layout_mixin import form_actions, to_row, SaplFormLayout, SaplFormHelper
from sapl.materia.models import MateriaLegislativa, TipoMateriaLegislativa
from sapl.parlamentares.models import Parlamentar
from sapl.utils import FileFieldCheckMixin, parlamentares_ativos


logger = logging.getLogger(__name__)



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


class LoaParlModelMultipleChoiceFilter(ModelMultipleChoiceFilter):

    def get_queryset(self, request):
        if self.parent.loa.materia and self.parent.loa.materia.normajuridica():
            return self.parent.loa.parlamentares.filter(emendaloaparlamentar_set__isnull=False).distinct()
        else:
            return self.parent.loa.parlamentares.all()

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
            'yaml_obs',
            'despesa_default_deducao_saude',
            'despesa_default_deducao_diversos',
            'despesa_default_deducao_educacao'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        instance = self.instance

        if not instance or not instance.pk or not instance.materia:
            parlamentares = Parlamentar.objects.filter(ativo=True)
            despesa_default_deducao_saude = Despesa.objects.none()
            despesa_default_deducao_diversos = Despesa.objects.none()
            despesa_default_deducao_educacao = Despesa.objects.none()
        else:
            ano_materia = instance.materia.ano
            parlamentares = Parlamentar.objects.filter(
                Q(ativo=True) | Q(emendaloaparlamentar_set__emendaloa__materia__ano=ano_materia)
            ).distinct()

            despesa_default_deducao_diversos = Despesa.objects.filter(loa=instance, funcao__codigo='99', fonte__codigo__in=['100',]).order_by('fonte__codigo')
            despesa_default_deducao_educacao = Despesa.objects.filter(loa=instance, funcao__codigo='99', fonte__codigo__in=['101',]).order_by('fonte__codigo')
            despesa_default_deducao_saude = Despesa.objects.filter(loa=instance, funcao__codigo='99', fonte__codigo__in=['102',]).order_by('fonte__codigo')

        self.fields['parlamentares'].choices = [
            (p.pk, p) for p in parlamentares
        ]
        self.fields['despesa_default_deducao_diversos'].queryset = despesa_default_deducao_diversos
        self.fields['despesa_default_deducao_educacao'].queryset = despesa_default_deducao_educacao
        self.fields['despesa_default_deducao_saude'].queryset = despesa_default_deducao_saude




    def clean(self):
        cd = super().clean()

        if not cd:
            cd = self.cleaned_data

        try:
            yo = yaml.full_load(cd['yaml_obs'])
            #print(yo)
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

        if not i.materia or not i.materia.normajuridica():
            i.rcl_previa = i.receita_corrente_liquida

        # if i.disp_diversos + i.disp_saude != i.disp_total:
        #    i.disp_diversos = i.disp_total - i.disp_saude
        #    i.perc_disp_diversos = quantize(
        #        i.disp_diversos / i.receita_corrente_liquida * Decimal(100),
        #        rounding=ROUND_DOWN)

        i = super().save(commit)

        i.update_disponibilidades()

        return i



class EmendaLoaValorWidget(SplitArrayWidget):
    template_name = 'loa/widget/parlamentares_valor_form.html'

    def __init__(self, widget, parlamentares=[], elps=[], user=None, **kwargs):
        self.instance = kwargs.pop('instance')
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

            # if 'class' in self.attrs and 'class' in w['attrs']:
            #    w['attrs']['class'] = 'decimalinput form-control text-right'

            if self.user and not self.user.has_perms(
                    ('loa.add_emendaloa', 'loa.change_emendaloa')):

                #if self.instance.pk and self.instance.fase == EmendaLoa.LIBERACAO_CONTABIL:
                #    w['attrs']['readonly'] = 'readonly'
                #    continue

                if self.user == self.instance.owner:
                    continue

                op = self.user.operadorautor_set.first()
                if not op or op and p not in self.elps:
                    w['attrs']['readonly'] = 'readonly'

        return context


class AgrupamentoForm(ModelForm):

    busca_emendaloa = forms.CharField(
        label='Procurar por emendas cadastradas', required=False,)

    busca_despesa = forms.CharField(
        label='Buscar', required=False,
        widget=TextInput(attrs={'autocomplete': 'off', 'type': 'search'})
    )

    perc_despesa = DecimalField(
        label='Percentual da Despesa', required=False, max_digits=5, decimal_places=2,)

    despesa_codigo = forms.CharField(
        label='Código', required=False)

    despesa_orgao = forms.CharField(
        label='Orgão', required=False,)
    despesa_unidade = forms.CharField(
        label='Unidade', required=False,)

    despesa_especificacao = forms.CharField(
        label='Descrição da Ação', required=False,)

    despesa_natureza = forms.CharField(
        label='Natureza', required=False,)

    despesa_fonte = forms.CharField(
        label='Fonte', required=False,)

    ano_loa = forms.CharField(
        label='',
        widget=forms.HiddenInput(),
        required=False)

    class Meta:
        model = Agrupamento
        fields = [
            'nome',
        ]

    def __init__(self, *args, **kwargs):
        self.user = kwargs['initial'].pop('user', None)
        self.loa = kwargs['initial']['loa']
        self.full_editor = full_editor = self.user.has_perm(
            'loa.emendaloa_full_editor') and not self.user.is_superuser

        row1 = to_row([
            ('nome', 12),
            ('ano_loa', 0),
        ])

        row4_1 = to_row([
            ('busca_despesa', 3),
            ('despesa_orgao', 2),
            ('despesa_unidade', 2),
            ('despesa_natureza', 3),
            ('despesa_fonte', 2),
        ])
        row4_2 = to_row([
            ('perc_despesa', 2),
            ('despesa_codigo', 3),
            ('despesa_especificacao', 'col-4'),
            (Div(HTML('''
                <button type="button" id="clean_form_search" class="btn btn-secondary" title="Limpar Formulário de Busca">
                    <i class="fas fa-backspace"></i>
                </button>
                <button type="button" id="add_registro" class="btn btn-primary" title="Adicionar Registro Contábil">
                    <i class="fas fa-plus-circle"></i>
                </button>
            '''), css_class="btn-group btn-group"), 'col-2'),

            (Div(css_class='busca-render'), 12)

        ])

        row4_3 = to_row([
            (Div(css_class='registro-render'), 12),
        ])

        row4 = to_row([
            (Fieldset(_('Registrar Deduções e Inserções'), row4_1, row4_2, css_class='fieldset-busca-registrocontabil'), 12),
            (Fieldset(_('Registros das Despesas Orçamentárias'), row4_3), 12)
        ])

        row5_1 = to_row([
            ('busca_emendaloa', 12),
            (Div(css_class='busca-render-emendaloa'), 12),
        ])

        row5_2 = to_row([
            (Div(css_class='emendaloa-selecteds'), 12),
        ])

        row5 = to_row([
            (Fieldset(_('Busca por Emendas '), row5_1), 7),
            (Fieldset(_('Emendas Selecionadas'), row5_2), 5)
        ])

        super().__init__(*args, **kwargs)

        btns = {}
        if self.instance.pk:
            btns = {
                'cancel_label': 'Encerrar Edição',
                'save_label': 'Encerrar Edição e Concluir Registro Contábil'
            }

        self.helper = FormHelper()
        self.helper.layout = SaplFormLayout(
            Fieldset(_('Dados Gerais'), row1), row4, row5, **btns)

        self.initial['ano_loa'] = self.loa.ano
        self.initial['perc_despesa'] = Decimal('100.00')

    def save(self, commit=False):
        if not self.instance.pk:
            return ModelForm.save(self, commit=commit)

        for e in self.instance.emendas.all():
            e.fase = 17
            e.save()

        return self.instance


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

    tipo = forms.ChoiceField(
        required=True,
        choices=EmendaLoa.TIPOEMENDALOA_CHOICE
    )

    finalidade = forms.CharField(
        label='Finalidade',
        widget=forms.Textarea(attrs={'rows': 3}),
        required=True)

    indicacao = forms.CharField(
        label='Indicação',
        required=False)

    parlamentares__valor = SplitArrayField(
        DecimalField(required=False,),
        10,
        label='Valores por Parlamentar',
        required=False
    )

    parl_assinantes = forms.ModelMultipleChoiceField(
        queryset=Parlamentar.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        label='Parlamentares que Assinarão',
        required=False
    )

    # registrocontabil_set = forms.ModelChoiceField(
    #    label='',
    # required=False,
    #    queryset=EmendaLoaRegistroContabil.objects.all(),
    #    widget=forms.CheckboxSelectMultiple,
    # )

    ano_loa = forms.CharField(
        label='',
        widget=forms.HiddenInput(),
        required=False)

    busca_despesa = forms.CharField(
        label='Buscar', required=False,
        widget=TextInput(attrs={'autocomplete': 'off', 'type': 'search'})
        )

    valor_despesa = DecimalField(
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

    despesa_fonte = forms.CharField(
        label='Fonte', required=False,)

    valor = DecimalField(
        label=_('Valor Global da Emenda (R$)'), required=False)

    entidade = forms.ModelChoiceField(
        queryset=Entidade.objects.filter(ativo=True),
        label='Entidade',
        required=False,
        widget=forms.Select(
            attrs={
                'class': 'selectpicker',
                'data-live-search': 'true',
                'data-header': 'Entidades Cadastradas',
                'data-dropup-auto': 'false'
            }
        )
    )

    class Meta:
        model = EmendaLoa
        fields = [
            'tipo', 'fase', 'valor',
            'materia', 'tipo_materia', 'numero_materia', 'ano_materia',
            'prefixo_indicacao', 'indicacao',
            'prefixo_finalidade', 'finalidade',
            'parlamentares__valor', 'parl_assinantes',
            'busca_despesa', 'ano_loa', 'unidade', 'entidade'  # 'registrocontabil_set'
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
            ('entidade', 12),
            ('prefixo_indicacao', 3),
            ('unidade', 9),
            ('prefixo_finalidade', 3),
            ('finalidade', 9),
        ]

        if not full_editor:
            row3.append(('parl_assinantes', 12))
            row3.append(('parlamentares__valor', 12))

        row3 = to_row(row3)

        rows_base = [row1, row2, row3, ]

        if full_editor or self.user.is_superuser:
            row4_1 = to_row([
                ('busca_despesa', 4),

                ('despesa_orgao', 1),
                ('despesa_unidade', 2),
                ('despesa_natureza', 3),
                ('despesa_fonte', 2),
            ])
            row4_2 = to_row([

                ('valor_despesa', 3),
                ('despesa_codigo', 3),
                ('despesa_especificacao', 'col-4'),
                (Div(HTML('''
                    <button type="button" id="clean_form_search" class="btn btn-secondary" title="Limpar Formulário de Busca">
                        <i class="fas fa-backspace"></i>
                    </button>
                    <button type="button" id="add_registro" class="btn btn-primary" title="Adicionar Registro Contábil">
                        <i class="fas fa-plus-circle"></i>
                    </button>
                '''), css_class="btn-group btn-group"), 'col-2'),

                (Div(css_class='busca-render'), 12)

            ])

            row4_3 = to_row([
                (Div(css_class='registro-render'), 12),
            ])
            row4 = to_row([
                (Fieldset(_('Registrar Deduções e Inserções'), row4_1, row4_2, css_class='fieldset-busca-registrocontabil'), 12),
                (Fieldset(_('Registros das Despesas Orçamentárias'), row4_3), 12)
            ])
        else:
            row4 = []
            if not self.creating:
                row4_2 = to_row([
                    (Div(css_class='registro-render btn-delete-d-none'), 12),
                ])

                row4 = to_row([
                    (Fieldset(_('Registros das Despesas Orçamentárias'), row4_2), 12)
                ])

        if row4:
            rows_base.append(row4)

        row_form = to_row([
            (rows_base, 12)
        ])

        if not self.creating:
            row_form = to_row([
                (rows_base, 8 if full_editor else 6),
                (Div(css_class='container-preview'), 4 if full_editor else 6)
            ])

        super().__init__(*args, **kwargs)

        self.helper = FormHelper()

        btns = {}
        if full_editor:
            btns = {
                'actions': form_actions(
                    label='CONCLUIR EDIÇÃO CONTÁBIL E FINALIZAR',
                    name="submit_concluir",
                    more=[
                        Submit('submit_devolver', 'DEVOLVER PARA CORREÇÃO', css_class='btn btn-secondary', title='Devolver para Correção'),
                    ],
                    disabled=False
                )

            }

        self.helper.layout = SaplFormLayout(Fieldset(_('Dados Gerais'), row_form), **btns)

        self.initial['ano_loa'] = self.loa.ano
        if full_editor or self.user.is_superuser:
            if self.instance.pk:
                self.initial['valor_despesa'] = self.instance.valor

        self.fields['parl_assinantes'].choices = [
            (p.id, str(p)) for p in
            self.loa.parlamentares.all()]

        self.fields['unidade'].choices = [
            (u.id, str(u)) for u in
            UnidadeOrcamentaria.objects.filter(
                loa=self.loa,
                recebe_emenda_impositiva=True
            ).order_by('especificacao')]

        def get_entidade_choice(e):
            nome = e.nome_fantasia[:60].strip()
            nome = nome + '&nbsp;' * (60 - len(nome))

            tipo_entidade = str(e.tipo_entidade.descricao[:40].strip()) if e.tipo_entidade else ''
            tipo_entidade = tipo_entidade + '&nbsp;' * (40 - len(tipo_entidade))

            cnes_cnpj = f' {"CNES:" if e.cnes else "CNPJ:"} {e.cnes or e.cpfcnpj or ""}'
            cnes_cnpj = cnes_cnpj + '&nbsp;' * (25 - len(cnes_cnpj))

            html = mark_safe(f'{nome} - {cnes_cnpj}')

            return e.id, html

        self.fields['entidade'].choices = [('', '-------')] + [
            get_entidade_choice(e) for e in
            Entidade.objects.filter(ativo=True).order_by('nome_fantasia')
            ]

        if not self.user.has_perm('loa.add_emendaloa'):
            self.fields['tipo_materia'].widget = HiddenInput()
            self.fields['numero_materia'].widget = HiddenInput()
            self.fields['ano_materia'].widget = HiddenInput()

            self.fields['valor'].widget.attrs['readonly'] = 'readonly'
            self.fields['valor'].required = False

            if not full_editor:
                if self.creating:
                    self.fields['fase'].choices = EmendaLoa.FASE_CHOICE[:1]
                else:
                    self.fields['fase'].choices = EmendaLoa.FASE_CHOICE[:2]


                if self.instance.fase > EmendaLoa.PROPOSTA_LIBERADA:
                    #self.fields['prefixo_indicacao'].widget.attrs['readonly'] = 'readonly'
                    #self.fields['prefixo_finalidade'].widget.attrs['readonly'] = 'readonly'
                    #self.fields['finalidade'].widget.attrs['readonly'] = 'readonly'

                    self.fields['indicacao'].widget.attrs['readonly'] = 'readonly' # campo obsoleto

                    self.fields['tipo'].choices = [(self.instance.tipo, self.instance.get_tipo_display())]
                    self.fields['fase'].choices = [(self.instance.fase, self.instance.get_fase_display())]
                    self.fields['unidade'].choices = [(self.instance.unidade.id, str(self.instance.unidade))]
                    if self.instance.entidade:
                        self.fields['entidade'].choices = [(self.instance.entidade.id, str(self.instance.entidade))]
                    else:
                        self.fields['entidade'].choices = [('', '-------')]

            else:
                self.fields['fase'].widget.attrs['class'] = 'is-invalid'
                self.fields['fase'].choices = EmendaLoa.FASE_CHOICE[2:4]

        if full_editor:
            self.fields.pop('parlamentares__valor')
            self.fields.pop('parl_assinantes')
            return

        initial_pa = []
        initial_pv = []
        if self.instance.pk:
            initial_pv = [[p, Decimal('0.00')] for p in self.parls]
            for i, (p, v) in enumerate(initial_pv):
                ipv = p.emendaloaparlamentar_set.filter(
                    emendaloa=self.instance).first()
                if ipv:
                    initial_pv[i][1] = ipv.valor
                    initial_pa.append(p)

        self.initial['parlamentares__valor'] = list(
            map(lambda x: x[1], initial_pv))

        self.initial['parl_assinantes'] = initial_pa

        elps = list(map(lambda x: x[0], filter(lambda y: y[1], initial_pv)))

        fpv = self.fields['parlamentares__valor']
        fpv.max_length = len(self.parls)
        fpv.size = fpv.max_length
        fpv.widget = EmendaLoaValorWidget(
            widget=self.fields['parlamentares__valor'].base_field.widget,
            parlamentares=self.parls,
            user=self.user if self.instance.pk else None,
            elps=elps,
            attrs={'class': 'text-right'},
            instance=self.instance
        )

    def clean(self):
        super().clean()
        cleaned_data = self.cleaned_data

        if cleaned_data['tipo'] != '0':
            if 'parlamentares__valor'in cleaned_data:
                if not self.user.is_superuser and self.user.operadorautor_set.exists():
                    pv = {k: v for k, v in zip(
                        self.parls, self.cleaned_data['parlamentares__valor'])}

                    p = self.user.operadorautor_set.first().autor.autor_related
                    if not pv[p]:
                        raise ValidationError(
                            f'É obrigatório o preenchimento do valor ligado a seu Parlamentar: {p}.')
        else:
            if not 'valor' in cleaned_data or not cleaned_data['valor'] or cleaned_data['valor'] <= Decimal('0.00'):
                raise ValidationError(
                    f'Em Emendas Modificativas você deve informar o Valor Global da Emenda.')
            if not 'parl_assinantes' in cleaned_data:
                if not self.user.is_superuser and self.user.operadorautor_set.exists():
                    raise ValidationError(
                        f'Você deve selecionar ao menos o seu parlamentar')
            else:
                if not self.user.is_superuser and self.user.operadorautor_set.exists():
                    pv = self.cleaned_data['parl_assinantes']

                    p = self.user.operadorautor_set.first().autor.autor_related
                    if not p in pv:
                        raise ValidationError(
                            f'É obrigatório selecionar ao menos o seu parlamentar: {p}.')

        return cleaned_data

    def save(self, commit=True):

        i_init = self.instance

        created = not i_init.pk

        if created:
            i_init.owner = self.user
            i_init.metadata = {
                'style': {
                    'lineHeight': 150,
                    'espacoAssinatura': 1
                }
            }

        if 'parlamentares__valor' in self.cleaned_data and self.cleaned_data['tipo'] not in ('0', 0):
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

        #if created:
        #    i.save()

        if not self.full_editor:
            if 'parlamentares__valor' in self.cleaned_data and self.cleaned_data['tipo'] not in ('0', 0):
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
            elif 'parl_assinantes' in self.cleaned_data:
                i.parlamentares.clear()
                for p in self.cleaned_data['parl_assinantes']:
                    elp = EmendaLoaParlamentar()
                    elp.emendaloa = i
                    elp.parlamentar = p
                    elp.valor = Decimal('1.00')
                    elp.save()
                i.save()

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
        DecimalField(required=False, max_digits=14, decimal_places=2,), 10,
        label='Valores por Parlamentar',
        help_text='Valores negativos sem seleção de emenda são meramente informativos com a finalidade de concentração em outro item.',
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
            (e.pk, f'{e.materia.epigrafe_short if e.materia else ""} - {e}') for e in self.emendas
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
            attrs={'class': 'text-right'},
            instance=self.instance
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

    tipo = MultipleChoiceFilter(
        required=False,
        choices=EmendaLoa.TIPOEMENDALOA_CHOICE,
        label=_('Tipos'),
        widget=forms.CheckboxSelectMultiple
    )

    fase = MultipleChoiceFilter(
        required=False,
        choices=EmendaLoa.FASE_CHOICE,
        label=_('Fases'),
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'small'})
    )

    agrupamento = MultipleChoiceFilter(
        required=False,
        label=_('Totalizar listagem por:'),
        choices=list(
            {
                'despesa__orgao': 'Órgãos',
                'despesa__unidade': 'Unidades Orçamentárias',
                'despesa__funcao': 'Funções',
                'despesa__subfuncao': 'SubFunções',
                'despesa__programa': 'Programas',
                'despesa__acao': 'Ações',
                'despesa__natureza': 'Natureza da Despesa',
                'despesa__fonte': 'Fonte de Recursos',
            }.items()),
        method='filter_agrupamento',
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'small'})
    )

    tipo_agrupamento = ChoiceFilter(
        required=False,
        label=_('Via de Totalização:'),
        widget=forms.RadioSelect,
        empty_label=None,
        choices=list(
            {
                'insercao': 'Via Dotações de Inserção',
                'deducao': 'Via Dotações de Dedução',
                'sem_registro': 'Via Valor da Emenda',
            }.items()),
        method='filter_tipo_agrupamento')

    parlamentares = LoaParlModelMultipleChoiceFilter(
        queryset=Parlamentar.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        help_text='Clique nos parlamentares para adicionar ou remover do filtro.',
    )

    finalidade = CharFilter(label='Busca por termos',
                            help_text='Os Termos informados serão buscados nos campos finalidade ou Unidade Orçamentária',
                            method='filter_finalidade')

    class Meta:

        class Form(forms.Form):
            crispy_field_template = (
                'fase',
                'parlamentares',
                'tipo',
                'finalidade',
                'tipo_agrupamento',
                'agrupamento'
            )

        model = EmendaLoa
        fields = ['fase', 'parlamentares', 'tipo', 'indicacao',  'finalidade',
                  'tipo_agrupamento',
                  'agrupamento']
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
                '<div><div class="custom-control custom-checkbox">',
                '<div class="container-avatar d-flex justify-content-center w-100"><div class="custom-control custom-checkbox">',
                html, count=1)

            help_text_parlamentares = f'<small id="id_parlamentares_helptext" class="form-text text-muted">{form.fields["parlamentares"].help_text}</small>\n</div>'
            help_reverse = help_text_parlamentares.split('\n')
            html = re.sub(
                help_text_parlamentares,
                f'{help_reverse[1]}\n{help_reverse[0]}',
                html, count=1)

            html_parts = []
            for n in re.finditer(r'<input.+name="(\w+)".+value="(\d+)".*><label.*>(.*)</label>', html):
                html_parts.append([n.start(), n.end(), list(n.groups())])

            html_parts.reverse()
            label_layout = """{% load cropping common_tags %}
            <span class="avatar avatar6 {{active}}" >
                <img src="{% cropped_thumbnail p "fotografia_cropping" %}" alt="{{p.nome_parlamentar}}" title="{{p.nome_parlamentar}}">
            </span>
            """
            template = Template(label_layout)

            for x1, x2, (key, idp, nome) in html_parts:
                if key in ('fase', 'tipo', 'finalidade'):
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

    def filter_agrupamento(self, queryset, field_name, value):
        return queryset

    def filter_tipo_agrupamento(self, queryset, field_name, value):
        return queryset

    def filter_finalidade(self, queryset, field_name, value):

        query = value

        query = query.split(' ')
        if query:
            q = Q()
            for item in query:
                if not item:
                    continue
                q &= (Q(unidade__especificacao__icontains=item) |
                      Q(entidade__razao_social__icontains=item) |
                      Q(entidade__nome_fantasia__icontains=item) |
                      Q(entidade__cnes__icontains=item) |
                      Q(entidade__cpfcnpj__icontains=item) |
                      Q(finalidade__icontains=item))

            if q:
                queryset = queryset.filter(q)
        return queryset

    def __init__(self, *args, **kwargs):

        self.loa = kwargs.pop('loa')
        super().__init__(*args, **kwargs)

        finalidade_field = FieldWithButtons(
            Field('finalidade',
                    placeholder=_('Informe termos a filtrar...')),
            StrictButton(
                _('Filtrar'), css_class='btn-secondary',
                type='button'
            )
        )
        row = to_row(
            [
                (
                    to_row(
                        [
                            (Fieldset(_('Pesquisa de Emendas Parlamentares')), 12),
                            ('parlamentares', 12),
                            ('fase', 4),
                            (
                                to_row([
                                    ('tipo', 12),
                                    (finalidade_field, 12),
                                ]),
                                'col-md-8 p-0'
                            ),
                        ]
                    ),
                    8
                ),
                (
                    Div(
                        to_row(
                            [
                                (Fieldset(_('Listagem em PDF')), 12),
                                ('agrupamento', 12),
                                ('tipo_agrupamento', 12),
                                (HTML(
                                    '''<small class="text-info font-italic">
                                            Primeiro filtre como preferir
                                            nos controles à esquerda,
                                            depois selecione como totalizar e,
                                            aí sim, clique em "Gerar PDF".
                                        </small>
                                    '''), 8),
                                (
                                    Submit('pdf', 'Gerar PDF',
                                           css_class='btn btn-primary'),
                                    4
                                )
                            ]
                        ),
                        css_class="relatorio-select form-group",
                    ),
                    4
                ),
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

        #self.form.initial['tipo_agrupamento'] = 'insercao'
        #self.form.fields['tipo_agrupamento'].initial = 'insercao'

        if not self.loa.materia or not self.loa.materia.em_tramitacao:
            self.form.fields['fase'].choices = EmendaLoa.FASE_CHOICE[5:]
        else:
            self.form.fields['fase'].choices = EmendaLoa.FASE_CHOICE[:5]
        self.form.fields['tipo'].choices = EmendaLoa.TIPOEMENDALOA_CHOICE

class PrestacaoContaLoaForm(ModelForm):

    arquivos_cadastrados = forms.ModelMultipleChoiceField(
        label='Arquivos da Prestação de Contas',
        queryset=ArquivoPrestacaoContaLoa.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        help_text='Desmarque para excluir arquivos vinculados à prestação de contas.'
    )

    arquivos = forms.FileField(
        required=False,
        label=_('Arquivos para Upload')
    )

    data_envio = forms.DateField(
        label='Data de Envio',
        required=True
    )

    class Meta:
        model = PrestacaoContaLoa
        fields = [
            'data_envio',
            'epigrafe',
            'arquivos',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance.pk:
            self.fields['arquivos_cadastrados'].queryset = ArquivoPrestacaoContaLoa.objects.filter(
                prestacao_conta=self.instance
            )
            self.fields['arquivos_cadastrados'].initial = self.fields['arquivos_cadastrados'].queryset
        else:
            self.fields['arquivos_cadastrados'].queryset = ArquivoPrestacaoContaLoa.objects.none()


        self.fields['arquivos'].widget.attrs.update(
            {'multiple': 'multiple'})

    def save(self, commit = ...):
        inst = super().save(commit)

        new_files = []
        if 'arquivos' in self.files:
            for f in self.files.getlist('arquivos'):
                a = ArquivoPrestacaoContaLoa()
                a.prestacao_conta = inst
                a.arquivo = f
                a.descricao = f.name
                a.save()
                new_files.append(a.id)

        # remove arquivos não selecionados
        if inst.pk:
            arquivos_selecionados = self.cleaned_data.get('arquivos_cadastrados')
            for a in inst.arquivoprestacaocontaloa_set.exclude(id__in=new_files):
                if a not in arquivos_selecionados:
                    a.delete()

        return inst

class PrestacaoContaRegistroForm(ModelForm):

    registro_ajuste = forms.ModelChoiceField(
        queryset=RegistroAjusteLoa.objects.all(),
        label='Registro de Ajuste Técnico',
        required=False,
        widget=forms.Select(
            attrs={
                'class': 'selectpicker',
                'data-live-search': 'true',
                'data-header': 'Registros Técnicos Cadastrados',
                'data-dropup-auto': 'false'
            }
        )
    )

    emendaloa = forms.ModelChoiceField(
        queryset=EmendaLoa.objects.all(),
        label='Emendas da LOA',
        required=False,
        widget=forms.Select(
            attrs={
                'class': 'selectpicker',
                'data-live-search': 'true',
                'data-header': 'Emendas Cadastradas',
                'data-dropup-auto': 'false'
            }
        )
    )

    class Meta:
        model = PrestacaoContaRegistro
        fields = [
            'registro_ajuste',
            'situacao',
            'emendaloa',
            'detalhamento',
        ]
    def __init__(self, *args, **kwargs):
        loa = kwargs['initial'].pop('loa')
        super().__init__(*args, **kwargs)

        self.fields['emendaloa'].queryset = EmendaLoa.objects.filter(loa=loa)
        self.fields['registro_ajuste'].queryset = RegistroAjusteLoa.objects.filter(
            oficio_ajuste_loa__loa=loa)

        self.fields['emendaloa'].choices = [('', '---------')] + [
            (e.pk, f'{e.materia.epigrafe_short if e.materia else ""} - {str(e.unidade)} - {str(e)[:100]}') for e in self.fields['emendaloa'].queryset
        ]

        self.fields['registro_ajuste'].choices = [('', '---------')] + [
            (r.pk, f'{r.oficio_ajuste_loa.epigrafe if r.oficio_ajuste_loa else ""} - {r.str_valor} - {str(r.descricao)[:100]}') for r in self.fields['registro_ajuste'].queryset
        ]

    def clean(self):
        cleaned_data = super().clean()

        if not cleaned_data.get('registro_ajuste') and not cleaned_data.get('emendaloa'):
            raise ValidationError(
                'Você deve selecionar um Registro de Ajuste Técnico ou uma Emenda da LOA para vincular ao registro da prestação de contas.'
            )

        return cleaned_data