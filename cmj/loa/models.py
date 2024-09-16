import csv
from datetime import datetime
from decimal import Decimal
from io import StringIO

from bs4 import BeautifulSoup as bs
from django.contrib.postgres.fields.jsonb import JSONField
from django.core.serializers.json import DjangoJSONEncoder
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.db.models import manager
from django.db.models.aggregates import Sum
from django.db.models.deletion import PROTECT, CASCADE
from django.utils import formats
from django.utils.translation import ugettext_lazy as _

from cmj.utils import texto_upload_path
from sapl.materia.models import MateriaLegislativa
from sapl.parlamentares.models import Parlamentar
from sapl.utils import PortalFileField, OverwriteStorage


PERCENTAGE_VALIDATOR = [MinValueValidator(0), MaxValueValidator(100)]


class Loa(models.Model):

    ano = models.PositiveSmallIntegerField(verbose_name=_('Ano'))

    materia = models.OneToOneField(
        MateriaLegislativa,
        blank=True, null=True, default=None,
        verbose_name=_('Matéria Legislativa'),
        related_name='loa',
        on_delete=PROTECT)

    receita_corrente_liquida = models.DecimalField(
        max_digits=14, decimal_places=2, default=Decimal('0.00'),
        verbose_name=_('Receita Corrente Líquida - RCL (R$)'),
    )

    perc_disp_total = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal('0.00'),
        validators=PERCENTAGE_VALIDATOR,
        verbose_name=_('Disp. Global da RCL (%)'),
    )

    perc_disp_saude = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal('0.00'),
        validators=PERCENTAGE_VALIDATOR,
        verbose_name=_('Disp. Saúde da RCL (%)'),
    )

    perc_disp_diversos = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal('0.00'),
        validators=PERCENTAGE_VALIDATOR,
        verbose_name=_('Disp. Diversos da RCL (%)'),
    )

    disp_total = models.DecimalField(
        max_digits=14, decimal_places=2, default=Decimal('0.00'),
        validators=PERCENTAGE_VALIDATOR,
        verbose_name=_('Disp. Global da RCL (R$)'),
    )

    disp_saude = models.DecimalField(
        max_digits=14, decimal_places=2, default=Decimal('0.00'),
        validators=PERCENTAGE_VALIDATOR,
        verbose_name=_('Disp. Saúde da RCL (R$)'),
    )

    disp_diversos = models.DecimalField(
        max_digits=14, decimal_places=2, default=Decimal('0.00'),
        validators=PERCENTAGE_VALIDATOR,
        verbose_name=_('Disp. Diversos da RCL (R$)'),
    )

    parlamentares = models.ManyToManyField(
        Parlamentar,
        through='LoaParlamentar',
        related_name='loa_set',

        verbose_name=_('Parlamentares'),
        through_fields=(
            'loa',
            'parlamentar'))

    yaml_obs = models.TextField(
        verbose_name=_('Observações de Rodapé (yaml format)'),
        blank=True, null=True, default='')

    publicado = models.BooleanField(
        default=False, verbose_name=_('Publicado?'))

    #descricao = models.CharField(max_length=50, verbose_name=_('Descrição'))

    class Meta:
        verbose_name = _('LOA - Emendas Impositivas')
        verbose_name_plural = _('LOA - Emendas Impositivas')
        ordering = ['-id']

    def __str__(self):
        nj = self.materia.normajuridica() if self.materia else ''
        descr = nj or (self.materia or '')
        return f'LOA {self.ano} - {descr}'


class LoaParlamentar(models.Model):

    loa = models.ForeignKey(
        Loa,
        verbose_name=_('LOA - Emendas Impositivas'),
        related_name='loaparlamentar_set',
        on_delete=CASCADE)

    parlamentar = models.ForeignKey(
        Parlamentar,
        related_name='loaparlamentar_set',
        verbose_name=_('Parlamentar - Emendas Impositivas'),
        on_delete=CASCADE)

    disp_total = models.DecimalField(
        max_digits=14, decimal_places=2, default=Decimal('0.00'),
        validators=PERCENTAGE_VALIDATOR,
        verbose_name=_('Disp. Global da RCL (R$)'),
    )

    disp_saude = models.DecimalField(
        max_digits=14, decimal_places=2, default=Decimal('0.00'),
        validators=PERCENTAGE_VALIDATOR,
        verbose_name=_('Disp. Saúde da RCL (R$)'),
    )

    disp_diversos = models.DecimalField(
        max_digits=14, decimal_places=2, default=Decimal('0.00'),
        validators=PERCENTAGE_VALIDATOR,
        verbose_name=_('Disp. Diversos da RCL (R$)'),
    )

    def __str__(self):
        return f'{self.parlamentar} - {self.disp_total} - {self.disp_saude} - {self.disp_diversos}'

    class Meta:
        verbose_name = _('Valores do Parlamentar')
        verbose_name_plural = _('Valores dos Parlamentares')
        ordering = ['id']


class EmendaLoa(models.Model):

    SAUDE = 10
    DIVERSOS = 99
    TIPOEMENDALOA_CHOICE = (
        (SAUDE, _('Saúde')),
        (DIVERSOS, _('Áreas Diversas'))
    )

    PROPOSTA = 10
    PROPOSTA_LIBERADA = 12
    EDICAO_CONTABIL = 15
    LIBERACAO_CONTABIL = 17
    APROVACAO_LEGISLATIVA = 20
    APROVACAO_LEGAL = 30
    IMPEDIMENTO_TECNICO = 40
    IMPEDIMENTO_OFICIADO = 50
    FASE_CHOICE = (
        (PROPOSTA, _('Proposta Legislativa')),
        (PROPOSTA_LIBERADA, _('Proposta Liberada para Edição Contábil')),
        (EDICAO_CONTABIL, _('Em edição pela Contabilidade')),
        (LIBERACAO_CONTABIL, _('Liberado pela Contabilidade')),
        (APROVACAO_LEGISLATIVA, _('Aprovada no Processo Legislativo')),
        (APROVACAO_LEGAL, _('Aprovada')),
        (IMPEDIMENTO_TECNICO, _('Impedimento Técnico')),
        (IMPEDIMENTO_OFICIADO, _('Impedimento Técnico Oficiado'))
    )

    metadata = JSONField(
        verbose_name=_('Metadados'),
        blank=True, null=True, default=dict, encoder=DjangoJSONEncoder)

    tipo = models.PositiveSmallIntegerField(
        choices=TIPOEMENDALOA_CHOICE,
        default=99, verbose_name=_('Área de aplicação'))

    fase = models.PositiveSmallIntegerField(
        choices=FASE_CHOICE,
        default=10, verbose_name=_('Fase'))

    indicacao = models.TextField(
        verbose_name=_('Indicação'),
        blank=True, null=True, default=None)

    finalidade = models.TextField(
        verbose_name=_("Finalidade"))

    prefixo_indicacao = models.CharField(
        verbose_name=_('Prefixo da Indicação'), max_length=30,
        blank=True, default='o(a)')

    prefixo_finalidade = models.CharField(
        verbose_name=_("Prefixo da Finalidade"), max_length=30,
        blank=True, default='destinado a')

    loa = models.ForeignKey(
        Loa,
        verbose_name=_('Loa - Emendas Impositivas'),
        related_name='emendaloa_set',
        on_delete=CASCADE)

    materia = models.OneToOneField(
        MateriaLegislativa,
        blank=True, null=True, default=None,
        verbose_name=_('Matéria Legislativa'),
        # related_name='emendaloa',
        on_delete=PROTECT)

    valor = models.DecimalField(
        max_digits=14, decimal_places=2, default=Decimal('0.00'),
        verbose_name=_('Valor Global da Emenda (R$)'),
    )

    parlamentares = models.ManyToManyField(
        Parlamentar,
        through='EmendaLoaParlamentar',
        related_name='emendaloa_set',

        verbose_name=_('Parlamentares'),
        through_fields=(
            'emendaloa',
            'parlamentar'))

    @property
    def valor_computado(self):
        soma_ajustes = RegistroAjusteLoaParlamentar.objects.filter(
            registro__emendaloa=self
        ).aggregate(Sum('valor'))

        valor = self.valor + (soma_ajustes['valor__sum'] or Decimal('0.00'))
        valor_str = formats.number_format(valor, force_grouping=True)
        return valor_str

    def __str__(self):
        valor_str = formats.number_format(self.valor, force_grouping=True)
        return f'R$ {valor_str} - {self.finalidade}'

    class Meta:
        verbose_name = _('Emenda Impositiva')
        verbose_name_plural = _('Emendas Impositivas')
        ordering = ['id']

        permissions = (
            (
                'emendaloa_full_editor',
                _('Edição completa de Emendas Impositivas.')
            ),
        )

    def atualiza_valor(self):
        soma_dict = self.emendaloaparlamentar_set.aggregate(Sum('valor'))
        self.valor = soma_dict['valor__sum'] or Decimal('0.00')
        return self

    @property
    def totais_contabeis(self):
        deducoes = self.registrocontabil_set.filter(
            valor__lt=Decimal('0.00')
        ).aggregate(deducoes=Sum('valor'))

        insercoes = self.registrocontabil_set.filter(
            valor__gt=Decimal('0.00')
        ).aggregate(insercoes=Sum('valor'))

        deducoes = deducoes['deducoes'] or Decimal('0.00')
        insercoes = insercoes['insercoes'] or Decimal('0.00')

        divergencia_registros = insercoes + deducoes
        divergencia_emenda = self.valor - insercoes

        return {
            'soma_deducoes': deducoes,
            'soma_insercoes': insercoes,
            'divergencia_registros': divergencia_registros,
            'divergencia_emenda': divergencia_emenda,
            'valor_emendaloa': self.valor
        }


class EmendaLoaParlamentar(models.Model):

    emendaloa = models.ForeignKey(
        EmendaLoa,
        verbose_name=_('Emenda Impositiva'),
        related_name='emendaloaparlamentar_set',
        on_delete=CASCADE)

    parlamentar = models.ForeignKey(
        Parlamentar,
        related_name='emendaloaparlamentar_set',
        verbose_name=_('Parlamentar'),
        on_delete=CASCADE)

    valor = models.DecimalField(
        max_digits=14, decimal_places=2, default=Decimal('0.00'),
        verbose_name=_('Valor por Parlamentar (R$)'),
    )

    def __str__(self):
        valor_str = formats.number_format(self.valor, force_grouping=True)
        return f'R$ {valor_str} - {self.parlamentar.nome_parlamentar}'

    class Meta:
        verbose_name = _('Participação Parlamentar na Emenda Impositiva')
        verbose_name_plural = _(
            'Participações Parlamentares na Emenda Impositiva')
        ordering = ['id']


def ajuste_upload_path(instance, filename):
    return texto_upload_path(instance, filename, subpath=instance.loa.ano)


class OficioAjusteLoa(models.Model):

    FIELDFILE_NAME = ('arquivo',)

    loa = models.ForeignKey(
        Loa,
        verbose_name=_('Loa - Emendas Impositivas'),
        related_name='ajusteloa_set',
        on_delete=CASCADE)

    epigrafe = models.CharField(
        max_length=100,
        verbose_name=_("Epígrafe"))

    arquivo = PortalFileField(
        blank=True,
        null=True,
        upload_to=ajuste_upload_path,
        verbose_name=_('Ofício'),
        storage=OverwriteStorage(),
        max_length=512)

    metadata = JSONField(
        verbose_name=_('Metadados'),
        blank=True, null=True, default=None, encoder=DjangoJSONEncoder)

    parlamentares = models.ManyToManyField(
        Parlamentar,
        related_name='oficioajusteloa_set',
        verbose_name=_('Parlamentares'),)

    class Meta:
        verbose_name = _('Ofício de Ajuste Técnico')
        verbose_name_plural = _(
            'Ofícios de Ajuste Técnico')
        ordering = ['id']

    def __str__(self):
        ps = map(lambda x: x.nome_parlamentar, self.parlamentares.all())
        parlamentares = ' / '.join(ps)
        return f'{self.epigrafe} - {parlamentares}'

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):

        if not self.pk and self.arquivo:
            arquivo = self.arquivo
            self.arquivo = None
            models.Model.save(self, force_insert=force_insert,
                              force_update=force_update,
                              using=using,
                              update_fields=update_fields)
            self.arquivo = arquivo
            update_fields = ('arquivo', )

        return models.Model.save(self, force_insert=force_insert,
                                 force_update=force_update,
                                 using=using,
                                 update_fields=update_fields)


class RegistroAjusteLoa(models.Model):

    SAUDE = 10
    DIVERSOS = 99
    TIPOEMENDALOA_CHOICE = (
        (SAUDE, _('Saúde')),
        (DIVERSOS, _('Áreas Diversas'))
    )

    tipo = models.PositiveSmallIntegerField(
        choices=TIPOEMENDALOA_CHOICE,
        default=99, verbose_name=_('Área de aplicação'))

    oficio_ajuste_loa = models.ForeignKey(
        OficioAjusteLoa,
        verbose_name=_('Ofício de Ajuste Técnico'),
        related_name='registroajusteloa_set',
        on_delete=CASCADE)

    emendaloa = models.ForeignKey(
        EmendaLoa,
        blank=True, null=True, default=None,
        verbose_name=_('Emenda Impositiva'),
        related_name='registroajusteloa_set',
        on_delete=CASCADE)

    descricao = models.TextField(
        verbose_name=_("Descrição"))

    class Meta:
        verbose_name = _('Registro do Ajuste Técnico')
        verbose_name_plural = _(
            'Registros do Ajuste Técnico')
        ordering = ['id']

    parlamentares_valor = models.ManyToManyField(
        Parlamentar,
        through='RegistroAjusteLoaParlamentar',
        related_name='registroajusteloa_set',

        verbose_name=_('Parlamentares'),
        through_fields=(
            'registro',
            'parlamentar'))

    @property
    def str_valor(self):
        soma = sum(
            list(
                filter(
                    lambda x: x, self.registroajusteloaparlamentar_set.values_list(
                        'valor', flat=True)
                )
            )
        )
        str_v = formats.number_format(soma, force_grouping=True)
        if '-' in str_v:
            str_v = f'({str_v[1:]})'
        return str_v

    def __str__(self):
        return f'R$ {self.str_valor} - {self.oficio_ajuste_loa}'


class RegistroAjusteLoaParlamentar(models.Model):

    registro = models.ForeignKey(
        RegistroAjusteLoa,
        verbose_name=_('Registro de Ajuste'),
        related_name='registroajusteloaparlamentar_set',
        on_delete=CASCADE)

    parlamentar = models.ForeignKey(
        Parlamentar,
        related_name='registroajusteloaparlamentar_set',
        verbose_name=_('Parlamentar'),
        on_delete=CASCADE)

    valor = models.DecimalField(
        max_digits=14, decimal_places=2, default=Decimal('0.00'),
        verbose_name=_('Valor por Parlamentar (R$)'),
    )

    def __str__(self):
        valor_str = formats.number_format(self.valor, force_grouping=True)
        return f'R$ {valor_str} - {self.parlamentar.nome_parlamentar}'

    class Meta:
        verbose_name = _(
            'Participação Parlamentar no Registro de Ajuste Técnico')
        verbose_name_plural = _(
            'Participações Parlamentares no Registro de Ajuste Técnico')
        ordering = ['id']


class ElementoBase(models.Model):

    loa = models.ForeignKey(
        Loa,
        verbose_name=_('Loa'),
        related_name='+',
        on_delete=CASCADE)

    codigo = models.TextField(verbose_name=_("Código"))

    especificacao = models.CharField(
        max_length=256,
        verbose_name=_("Especificação"), default='', blank=True)

    # metadata = JSONField(
    #    verbose_name=_('Metadados'),
    #    blank=True, null=True, default=None, encoder=DjangoJSONEncoder)

    class Meta:
        abstract = True

    def __str__(self):
        return f'{self.codigo} - {self.especificacao}'


class Orgao(ElementoBase):

    class Meta:
        verbose_name = _('Órgão')
        verbose_name_plural = _('Órgãos')
        ordering = ['codigo']


class UnidadeOrcamentaria(ElementoBase):

    orgao = models.ForeignKey(
        Orgao,
        verbose_name=_('Órgão'),
        related_name='unidadeorcamentaria_set',
        on_delete=CASCADE)

    class Meta:
        verbose_name = _('Unidade Orçamentária')
        verbose_name_plural = _('Unidades Orçamentárias')
        ordering = ['codigo']


class Funcao(ElementoBase):

    class Meta:
        verbose_name = _('Função')
        verbose_name_plural = _('Funções')
        ordering = ['codigo']


class SubFuncao(ElementoBase):

    funcao = models.ForeignKey(
        Funcao,
        verbose_name=_('Função'),
        related_name='funcao_set',
        on_delete=CASCADE)

    class Meta:
        verbose_name = _('SubFunção')
        verbose_name_plural = _('SubFunções')
        ordering = ['codigo']


class Programa(ElementoBase):

    class Meta:
        verbose_name = _('Programa')
        verbose_name_plural = _('Programas')
        ordering = ['codigo']


class Acao(ElementoBase):

    class Meta:
        verbose_name = _('Ação')
        verbose_name_plural = _('Ações')
        ordering = ['codigo']


class Fonte(ElementoBase):

    class Meta:
        verbose_name = _('Fonte')
        verbose_name_plural = _('Fontes')
        ordering = ['codigo']


class Natureza(ElementoBase):

    class Meta:
        verbose_name = _('Natureza')
        verbose_name_plural = _('Naturezas')
        ordering = ['codigo']


class Despesa(models.Model):

    loa = models.ForeignKey(
        Loa,
        verbose_name=_('Loa'),
        related_name='despesa_set',
        on_delete=CASCADE)

    orgao = models.ForeignKey(
        Orgao,
        verbose_name=_('Órgão'),
        related_name='despesa_set',
        on_delete=CASCADE)

    unidade = models.ForeignKey(
        UnidadeOrcamentaria,
        verbose_name=_('Unidade Orçamentária'),
        related_name='despesa_set',
        on_delete=CASCADE)

    funcao = models.ForeignKey(
        Funcao,
        verbose_name=_('Função'),
        related_name='despesa_set',
        on_delete=CASCADE)

    subfuncao = models.ForeignKey(
        SubFuncao,
        verbose_name=_('SubFunção'),
        related_name='despesa_set',
        on_delete=CASCADE)

    programa = models.ForeignKey(
        Programa,
        verbose_name=_('Programa'),
        related_name='despesa_set',
        on_delete=CASCADE)

    acao = models.ForeignKey(
        Acao,
        verbose_name=_('Ação'),
        related_name='despesa_set',
        on_delete=CASCADE)

    fonte = models.ForeignKey(
        Fonte,
        blank=True, null=True, default=None,
        verbose_name=_('Fonte'),
        related_name='despesa_set',
        on_delete=CASCADE)

    natureza = models.ForeignKey(
        Natureza,
        verbose_name=_('Natureza'),
        related_name='despesa_set',
        on_delete=CASCADE)

    valor_materia = models.DecimalField(
        max_digits=14, decimal_places=2, default=Decimal('0.00'),
        verbose_name=_('Valor Despesa Matéria (R$)'),
    )

    valor_norma = models.DecimalField(
        max_digits=14, decimal_places=2, default=Decimal('0.00'),
        verbose_name=_('Valor Despesa Norma (R$)'),
    )

    class Meta:
        verbose_name = _('Despesa')
        verbose_name_plural = _('Despesas')
        ordering = ['id']

        unique_together = (
            (
                'loa',
                'orgao',
                'unidade',
                'funcao',
                'subfuncao',
                'programa',
                'acao',
                'fonte',
                'natureza'
            ),
        )

    def __str__(self):
        dc = DespesaConsulta.objects.get(pk=self.id)
        return str(dc)

    @property
    def consulta(self):
        return DespesaConsulta.objects.get(pk=self.id)

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):

        self.clean()

        return models.Model.save(self, force_insert=force_insert, force_update=force_update, using=using, update_fields=update_fields)

    def clean(self):

        # Check for instances with null values in unique_together fields.

        from django.core.exceptions import ValidationError

        super().clean()

        for field_tuple in self._meta.unique_together[:]:
            unique_filter = {}
            unique_fields = []
            null_found = False
            for field_name in field_tuple:
                field_value = getattr(self, field_name)
                if getattr(self, field_name) is None:
                    unique_filter['%s__isnull' % field_name] = True
                    null_found = True
                else:
                    unique_filter['%s' % field_name] = field_value
                    unique_fields.append(field_name)
            if null_found:
                unique_queryset = self.__class__.objects.filter(
                    **unique_filter)
                if self.pk:
                    unique_queryset = unique_queryset.exclude(pk=self.pk)
                if unique_queryset.exists():
                    msg = self.unique_error_message(
                        self.__class__, tuple(unique_fields))
                    raise ValidationError(msg)


class DespesaConsulta(models.Model):

    loa = models.ForeignKey(
        Loa,
        verbose_name=_('Loa'),
        related_name='+',
        on_delete=CASCADE)

    valor_materia = models.DecimalField(
        max_digits=14, decimal_places=2, default=Decimal('0.00'),
        verbose_name=_('Valor Despesa Matéria (R$)'),
    )

    valor_norma = models.DecimalField(
        max_digits=14, decimal_places=2, default=Decimal('0.00'),
        verbose_name=_('Valor Despesa Norma (R$)'),
    )

    codigo = models.TextField(verbose_name=_("Código"))
    especificacao = models.TextField(verbose_name=_("Especificação"))

    cod_orgao = models.TextField(verbose_name=_("Código do Órgão"))
    esp_orgao = models.TextField(verbose_name=_("Órgão"))

    cod_unidade = models.TextField(verbose_name=_("Código da Unidade"))
    esp_unidade = models.TextField(verbose_name=_("Unidade Orçamentária"))

    cod_natureza = models.TextField(verbose_name=_("Código Natureza"))
    esp_natureza = models.TextField(verbose_name=_("Natureza da Despesa"))
    cod_fonte = models.TextField(verbose_name=_("Fonte"))

    class Meta:
        managed = False
        db_table = 'loa_despesa_consulta'
        ordering = ('cod_orgao', 'cod_unidade', 'codigo', 'cod_natureza')

    def __str__(self):
        return f'{self.codigo}:{self.cod_natureza} - {self.especificacao}'


class EmendaLoaRegistroContabilManager(manager.Manager):

    use_for_related_fields = True

    def all_deducoes(self):
        qs = self.get_queryset()
        qs = qs.filter(valor__lt=Decimal('0.00'))
        return qs

    def all_insercoes(self):
        qs = self.get_queryset()
        qs = qs.filter(valor__gt=Decimal('0.00'))
        return qs


class EmendaLoaRegistroContabil(models.Model):

    objects = EmendaLoaRegistroContabilManager()

    emendaloa = models.ForeignKey(
        EmendaLoa,
        verbose_name=_('Emenda Impositiva'),
        related_name='registrocontabil_set',
        on_delete=CASCADE)

    despesa = models.ForeignKey(
        Despesa,
        blank=True, null=True, default=None,
        related_name='registrocontabil_set',
        verbose_name=_('Despesa'),
        on_delete=CASCADE)

    valor = models.DecimalField(
        max_digits=14, decimal_places=2, default=Decimal('0.00'),
        verbose_name=_('Valor (R$)'),
    )

    """orgao = models.ForeignKey(
        Orgao,
        blank=True, null=True, default=None,
        verbose_name=_('Órgão'),
        related_name='registrocontabil_set',
        on_delete=CASCADE)

    unidade = models.ForeignKey(
        UnidadeOrcamentaria,
        blank=True, null=True, default=None,
        verbose_name=_('Unidade Orçamentária'),
        related_name='registrocontabil_set',
        on_delete=CASCADE)

    natureza = models.ForeignKey(
        Natureza,
        blank=True, null=True, default=None,
        verbose_name=_('Natureza'),
        related_name='registrocontabil_set',
        on_delete=CASCADE)"""

    def __str__(self):
        valor_str = formats.number_format(self.valor, force_grouping=True)
        return f'R$ {valor_str} - {self.despesa}'

    @property
    def str_valor(self):
        return formats.number_format(self.valor, force_grouping=True)

    class Meta:
        verbose_name = _('Registro Contábil de Dedução e Inserção em Emendas')
        verbose_name_plural = _(
            'Registros Contábeis de Dedução e Inserção em Emendas')
        ordering = ['id']

        unique_together = (
            (
                'emendaloa',
                'despesa',
            ),

        )


class DespesaPaga(models.Model):

    mapeamento = {
        'Código:': 'codigo',
        'Código': 'codigo',
        'Data:': 'data',
        'Data': 'data',
        'Banco:': 'banco',
        'Banco': 'banco',
        'Agência:': 'agencia',
        'Agência': 'agencia',
        'Conta Bancária:': 'conta',
        'Conta': 'conta',
        'Tipo do Documento:': 'tipo',
        'Tipo do Documento': 'tipo',
        'Nº do Documento:': 'numero_documento',
        'Número do Documento': 'numero_documento',
        'Número da Licitação:': 'numero_licitacao',
        'Código Empenho:': 'empenho',
        'Elemento:': 'elemento',
        'Sub Elemento:': 'subelemento',
        'Unidade Financeira:': 'unidade',
        'Unidade Financeira': 'unidade',
        'Fonte de Recursos:': 'fonte',
        'Fonte de Recursos': 'fonte',
        'Historico:': 'historico',
        'Número': 'numero_emissao',
        'Série': 'serie',
        'Data de Emissão': 'data_emissao',
        'Tipo': 'tipo_emissao',
        'Valor': 'valor'
    }

    codigo = models.TextField(verbose_name=_("Código"))
    data = models.DateField(verbose_name=_('Data'))

    orgao = models.ForeignKey(
        Orgao,
        related_name='despesapaga_set',
        verbose_name=_('Órgão'),
        on_delete=CASCADE)

    unidade = models.ForeignKey(
        UnidadeOrcamentaria,
        related_name='despesapaga_set',
        verbose_name=_('Unidade Financeira'),
        on_delete=CASCADE)

    valor = models.DecimalField(
        max_digits=14, decimal_places=2, default=Decimal('0.00'),
        verbose_name=_('Valor (R$)'),
    )

    class Meta:
        verbose_name = _('Despesa Paga')
        verbose_name_plural = _('Despesas Pagas')
        ordering = ['id']


class ScrapRecord(models.Model):

    metadata = JSONField(
        verbose_name=_('Metadados'),
        blank=True, null=True, default=None, encoder=DjangoJSONEncoder)

    mes = models.PositiveSmallIntegerField(verbose_name=_('Mes'))
    ano = models.PositiveSmallIntegerField(verbose_name=_('Ano'))
    orgao = models.TextField(verbose_name=_("Órgão"))

    codigo = models.TextField(verbose_name=_("Código"), default='')

    url = models.TextField(verbose_name=_("Órgão"), unique=True)

    content = models.BinaryField(editable=True, default=b'')

    modified = models.DateTimeField(
        verbose_name=_('modified'), editable=False, auto_now=True)

    parent = models.ForeignKey(
        'self',
        blank=True, null=True, default=None,
        related_name='scrap_set',
        on_delete=CASCADE)

    class Meta:
        verbose_name = 'ScrapRecord'
        verbose_name_plural = 'ScrapRecord'
        ordering = ['id']

    def get_despesa_paga(self):

        def clean_text(text):
            while '  ' in text:
                text = text.replace('  ', ' ')
            while ' \n' in text:
                text = text.replace(' \n', '\n')
            while '\n ' in text:
                text = text.replace('\n ', '\n')
            while '\r\n' in text:
                text = text.replace('\r\n', '\n')
            while '\n\n' in text:
                text = text.replace('\n\n', '\n')
            while '<td> ' in text:
                text = text.replace('<td> ', '<td>')
            while ' :</td>' in text:
                text = text.replace(' :</td>', ':</td>')
            while '\n</td>' in text:
                text = text.replace('\n</td>', '</td>')
            while ' </td>' in text:
                text = text.replace(' </td>', '</td>')
            while '<td>R$ ' in text:
                text = text.replace('<td>R$ ', '<td>')
            return text

        # if self.scrap_set.exists():
        # return [scrap.get_despesa_paga() for scrap in self.scrap_set.all()]

        if not self.codigo or self.codigo == 'TOTAL:':
            return None

        if not self.metadata['url_dict']['format'] == 'html':
            return None

        if 'despesa' not in self.metadata['url_dict']['name']:
            return None

        content = self.content
        if not isinstance(content, bytes):
            content = content.tobytes()
        content = content.decode('utf-8-sig')
        content = clean_text(clean_text(clean_text(content)))
        tables = bs(content).findAll('table')
        if not tables:
            return None
        try:
            values = {}
            for row in tables[0].findAll('tr'):
                cols = row.findAll('td')
                values[cols[0].text] = cols[1].text

            item_list = self.metadata['item_list']

            orgao = Orgao.objects.get(codigo=self.orgao, loa__ano=self.ano)
            unidade = UnidadeOrcamentaria.objects.get(
                orgao=orgao,
                loa__ano=self.ano,
                codigo=values['Unidade Financeira:'][:2]
            )
            dt = datetime.strptime(values['Data:'], "%d/%m/%Y").date()

            dp = DespesaPaga.objects.get_or_create(
                codigo=self.codigo,
                orgao=orgao,
                unidade=unidade,
            )
            dp.valor = Decimal(
                item_list[-1].replace('.', '').replace(',', '.'))
            dp.data = dt
            dp.save()
            return dp
        except Exception as e:
            return None
