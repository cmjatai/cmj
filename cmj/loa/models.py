from _decimal import ROUND_HALF_DOWN, ROUND_DOWN
from datetime import datetime
from decimal import Decimal
from enum import unique
from io import StringIO
import csv
from math import e
from pyexpat import model
import re
from django.core.validators import RegexValidator

from bs4 import BeautifulSoup as bs
from django.conf.locale import ro
from django.core.serializers.json import DjangoJSONEncoder
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models, transaction
from django.db.models import manager
from django.db.models.aggregates import Sum
from django.db.models.deletion import PROTECT, CASCADE, SET_NULL
from django.db.models.fields.json import JSONField
from django.utils import formats
from django.utils.translation import gettext_lazy as _

from cmj.utils import UF, run_sql, texto_upload_path, get_settings_auth_user_model
from sapl.materia.models import EM_TRAMITACAO, MateriaLegislativa
from sapl.parlamentares.models import Legislatura, Parlamentar
from sapl.utils import PortalFileField, OverwriteStorage


PERCENTAGE_VALIDATOR = [MinValueValidator(0), MaxValueValidator(100)]


def quantize(value, decimal_places='0.01', rounding=ROUND_HALF_DOWN) -> Decimal:
    return value.quantize(
        Decimal(decimal_places),
        rounding=rounding
    )


class Loa(models.Model):

    ano = models.PositiveSmallIntegerField(verbose_name=_('Ano'))

    materia = models.OneToOneField(
        MateriaLegislativa,
        blank=True, null=True, default=None,
        verbose_name=_('Matéria Legislativa'),
        related_name='loa',
        on_delete=PROTECT)

    rcl_previa = models.DecimalField(
        max_digits=14, decimal_places=2, default=Decimal('0.00'),
        verbose_name=_('Receita Corrente Líquida - Prévia (R$)'),
    )

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

    despesa_default_deducao_saude = models.ForeignKey(
        'Despesa',
        blank=True, null=True, default=None,
        verbose_name=_('Despesa Default Dedução Saúde'),
        related_name='loa_despesa_default_deducao_saude',
        on_delete=PROTECT)

    despesa_default_deducao_diversos = models.ForeignKey(
        'Despesa',
        blank=True, null=True, default=None,
        verbose_name=_('Despesa Default Dedução Diversos'),
        related_name='loa_despesa_default_deducao_diversos',
        on_delete=PROTECT)

    despesa_default_deducao_educacao = models.ForeignKey(
        'Despesa',
        blank=True, null=True, default=None,
        verbose_name=_('Despesa Default Dedução Educação'),
        related_name='loa_despesa_default_deducao_educacao',
        on_delete=PROTECT)


    class Meta:
        verbose_name = _('LOA')
        verbose_name_plural = _('LOAs')
        ordering = ['-id']
        permissions = (
            ('view_despesasexecutadas', _('View Despesas Executadas')),
        )

    def __str__(self):
        nj = self.materia.normajuridica() if self.materia else ''
        descr = nj or (self.materia or '')
        return f'LOA {self.ano} - {descr}'

    def update_disponibilidades(self):

        def set_values_for_lp(lp, disp_total, disp_saude, disp_diversos, count_lps):
            idsp = quantize(disp_saude / Decimal(count_lps), rounding=ROUND_DOWN)
            iddp = quantize(disp_diversos / Decimal(count_lps), rounding=ROUND_DOWN)
            # if iddp + idsp != idtp:
            #    iddp = idtp - idsp
            lp.disp_total = idsp + iddp
            lp.disp_saude = idsp
            lp.disp_diversos = iddp

        legislatura_atual = Legislatura.cache_legislatura_atual()

        materia_in_legislatura_atual = True
        loa_in_legislatura_atual = True

        if self.materia:
            materia_in_legislatura_atual = legislatura_atual['data_inicio'] <= self.materia.data_apresentacao <= legislatura_atual['data_fim']
            loa_in_legislatura_atual = legislatura_atual['data_inicio'].year <= self.ano <= legislatura_atual['data_fim'].year

        lps = self.loaparlamentar_set.all()
        count_lps = lps.count()

        if (loa_in_legislatura_atual and  materia_in_legislatura_atual) or (
            not loa_in_legislatura_atual and not materia_in_legislatura_atual
        ):
            count_lps = lps.count()
            if count_lps:
                for lp in lps:
                    set_values_for_lp(lp, self.disp_total, self.disp_saude, self.disp_diversos, count_lps)
                    lp.save()
            return self


        parlamentares_ativos_sem_emendas = Parlamentar.objects.filter(
            ativo=True, emendaloaparlamentar_set__isnull=True)

        parlamentares_ativos_com_emendas = Parlamentar.objects.filter(
            ativo=True).exclude(emendaloaparlamentar_set__isnull=True).distinct()

        parlamentares_inativos_com_emendas = Parlamentar.objects.filter(
            ativo=False).exclude(emendaloaparlamentar_set__isnull=True).distinct()

        count_parlamentares_ativos = Decimal(parlamentares_ativos_com_emendas.count() + parlamentares_ativos_sem_emendas.count())

        disp_previa_total = quantize(self.rcl_previa * self.perc_disp_total / Decimal(100), rounding=ROUND_DOWN)
        disp_previa_saude = quantize(self.rcl_previa * self.perc_disp_saude / Decimal(100), rounding=ROUND_DOWN)
        disp_previa_diversos = quantize(self.rcl_previa * self.perc_disp_diversos / Decimal(100), rounding=ROUND_DOWN)

        disp_previa_total = quantize(disp_previa_total / count_parlamentares_ativos, rounding=ROUND_DOWN) * count_parlamentares_ativos
        disp_previa_saude = quantize(disp_previa_saude / count_parlamentares_ativos, rounding=ROUND_DOWN) * count_parlamentares_ativos
        disp_previa_diversos = quantize(disp_previa_diversos / count_parlamentares_ativos, rounding=ROUND_DOWN) * count_parlamentares_ativos

        imp_inativos_saude = Decimal('0.00')
        imp_inativos_diversos = Decimal('0.00')
        for lp in lps:
            if lp.parlamentar in parlamentares_inativos_com_emendas:
                soma_imp_saude = lp.parlamentar.emendaloaparlamentar_set.filter(
                    emendaloa__loa = self,
                    emendaloa__fase = EmendaLoa.IMPEDIMENTO_TECNICO,
                    emendaloa__tipo = EmendaLoa.SAUDE
                ).aggregate(Sum('valor'))
                soma_imp_diversos = lp.parlamentar.emendaloaparlamentar_set.filter(
                    emendaloa__loa = self,
                    emendaloa__fase = EmendaLoa.IMPEDIMENTO_TECNICO,
                    emendaloa__tipo = EmendaLoa.DIVERSOS
                ).aggregate(Sum('valor'))

                soma_imp_saude = soma_imp_saude['valor__sum'] or Decimal('0.00')
                soma_imp_diversos = soma_imp_diversos['valor__sum'] or Decimal('0.00')
                dps = disp_previa_saude
                dpd = disp_previa_diversos
                set_values_for_lp(
                    lp, dps + dpd, dps, dpd, parlamentares_ativos_com_emendas.count() + parlamentares_inativos_com_emendas.count()
                )
                lp.disp_total -= soma_imp_saude + soma_imp_diversos
                lp.disp_saude -= soma_imp_saude
                lp.disp_diversos -= soma_imp_diversos
                lp.save()
                imp_inativos_saude += soma_imp_saude
                imp_inativos_diversos += soma_imp_diversos



        for lp in lps:
            if lp.parlamentar in parlamentares_ativos_com_emendas:
                set_values_for_lp(
                    lp, self.disp_total + imp_inativos_saude + imp_inativos_diversos,
                    self.disp_saude + imp_inativos_saude,
                    self.disp_diversos + imp_inativos_diversos,
                    count_parlamentares_ativos
                    )
            elif lp.parlamentar in parlamentares_ativos_sem_emendas:
                set_values_for_lp(
                    lp,
                    self.disp_total - disp_previa_total + imp_inativos_saude + imp_inativos_diversos,
                    self.disp_saude - disp_previa_saude + imp_inativos_saude,
                    self.disp_diversos - disp_previa_diversos + imp_inativos_diversos,
                    count_parlamentares_ativos
                    )
            lp.save()


class LoaParlamentar(models.Model):

    loa = models.ForeignKey(
        Loa,
        verbose_name=_('LOA'),
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
        (SAUDE, _('Em.Imp. Saúde')),
        (DIVERSOS, _('Em.Imp. Áreas Diversas')),
        (0, _('Emenda Modificativa')),
    )

    PROPOSTA = 10
    PROPOSTA_LIBERADA = 12
    EDICAO_CONTABIL = 15
    LIBERACAO_CONTABIL = 17
    EM_TRAMITACAO = 20
    APROVACAO_LEGISLATIVA = 25
    APROVACAO_LEGAL = 30
    IMPEDIMENTO_TECNICO = 40
    IMPEDIMENTO_SANADO = 50
    FASE_CHOICE = (
        (PROPOSTA, _('Proposta Legislativa')),
        (PROPOSTA_LIBERADA, _('Proposta Liberada para Edição Contábil')),
        (EDICAO_CONTABIL, _('Em edição pela Contabilidade')),
        (LIBERACAO_CONTABIL, _('Liberado pela Contabilidade')),
        (EM_TRAMITACAO, _('Matéria protocolada, em tramitação')),
        (APROVACAO_LEGISLATIVA, _('Aprovada no Processo Legislativo')),
        (APROVACAO_LEGAL, _('Aprovada')),
        (IMPEDIMENTO_TECNICO, _('Impedimento Técnico')),
        (IMPEDIMENTO_SANADO, _('Impedimento Técnico Sanado'))
    )

    metadata = JSONField(
        verbose_name=_('Metadados'),
        blank=True, null=True, default=dict, encoder=DjangoJSONEncoder)

    tipo = models.PositiveSmallIntegerField(
        choices=TIPOEMENDALOA_CHOICE, default=99, verbose_name=_('Área de aplicação'))

    fase = models.PositiveSmallIntegerField(
        choices=FASE_CHOICE,
        default=10, verbose_name=_('Fase'))

    indicacao = models.TextField(
        verbose_name=_('Indicação'),
        blank=True, null=True, default=None)

    entidade = models.ForeignKey(
        'Entidade',
        verbose_name=_('Entidade'),
        related_name='emendaloa_set',
        blank=True, null=True, default=None,
        on_delete=PROTECT)

    unidade = models.ForeignKey(
        'UnidadeOrcamentaria',
        verbose_name=_('Unidade Orçamentária'),
        related_name='emendaloa_set',
        blank=True, null=True, default=None,
        on_delete=PROTECT)

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
        verbose_name=_('LOA'),
        related_name='emendaloa_set',
        on_delete=CASCADE)

    materia = models.OneToOneField(
        MateriaLegislativa,
        blank=True, null=True, default=None,
        verbose_name=_('Matéria Legislativa'),
        related_name='emendaloa',
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

    owner = models.ForeignKey(
        get_settings_auth_user_model(),
        blank=True, null=True, default=None,
        verbose_name=_('Cadastrado Por'),
        related_name='+',
        on_delete=PROTECT)

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
        return f'R$ {valor_str} - {self.finalidade_format}'

    @property
    def finalidade_format(self):
        finalidade = self.finalidade
        chaves = re.findall(r'\{(.*?)\}', finalidade)

        for chave in chaves:
            chave_strip = chave.strip()
            if '__' in chave_strip:
                partes = chave_strip.split('__')
                obj = self
                for parte in partes:
                    if hasattr(obj, parte):
                        obj = getattr(obj, parte)
                    else:
                        obj = None
                        break
                valor = str(obj) if obj else ''
            elif hasattr(self, chave_strip):
                valor = getattr(self, chave_strip) or ''
                if isinstance(valor, models.Model):
                    valor = str(valor)
            valor = valor.upper() if valor and isinstance(valor, str) else valor
            finalidade = finalidade.replace(f'{{{chave}}}', str(valor))

        return finalidade

    @property
    def str_valor(self):
        return formats.number_format(self.valor, force_grouping=True)

    class Meta:
        verbose_name = _('Emenda Impositiva/Modificativa')
        verbose_name_plural = _('Emendas Impositivas/Modificativas')
        ordering = ['id']

        permissions = (
            (
                'emendaloa_full_editor',
                _('Edição completa de Emendas Impositivas.')
            ),
        )

    _syncing = False

    def errors(self):
        erros = []
        if self.tipo in (self.SAUDE, self.DIVERSOS) and not self.unidade:
            erros.append('Emendas Impositivas devem ter Unidade Orçamentária.')

        if self.tipo in (self.SAUDE, self.DIVERSOS) and not self.entidade:
            erros.append('Emendas Impositivas devem ter Entidade.')

        if self.tipo == self.SAUDE and self.unidade and self.unidade.area != UnidadeOrcamentaria.SAUDE_CHOICE:
            erros.append('Emendas Impositivas da Saúde devem ter Unidade Orçamentária classificadas como sendo da Área da Saúde.')
            # existe registro com fonte diferente de 102?

        if self.tipo == self.SAUDE and self.unidade and self.unidade.area == UnidadeOrcamentaria.SAUDE_CHOICE:

            if self.entidade and self.entidade.tipo_entidade and self.entidade.tipo_entidade.tipo_geral != TipoEntidade.SAUDE_CHOICE:
                erros.append('Emendas Impositivas da Saúde devem ter Entidade do Tipo Saúde.')

            registros = self.registrocontabil_set.all()
            fontes_invalidas = registros.exclude(despesa__fonte__codigo='102')
            if fontes_invalidas.exists():
                erros.append('Emendas Impositivas da Saúde não podem ter registros com fonte diferente de 102.')

        #if self.tipo == self.DIVERSOS and self.unidade and self.unidade.area == UnidadeOrcamentaria.SAUDE_CHOICE:
        #    erros.append('Emendas Impositivas de Áreas Diversas não podem ter Unidade Orçamentária classificadas como sendo da Área da Saúde.')

        if self.tipo == self.DIVERSOS and self.unidade and self.unidade.area == UnidadeOrcamentaria.EDUCACAO_CHOICE:
            # existe registro com fonte diferente de 101?
            registros = self.registrocontabil_set.all()
            fontes_invalidas = registros.exclude(despesa__fonte__codigo='101')
            if fontes_invalidas.exists():
                erros.append('Emendas Impositivas da Educação não podem ter registros com fonte diferente de 101.')

        return erros

    def sync(self):
        registros = self.registrocontabil_set.all().order_by('valor')
        old_self = EmendaLoa.objects.filter(pk=self.pk).first()
        if self.tipo:
            soma_dict = self.emendaloaparlamentar_set.aggregate(Sum('valor'))
            self.valor = soma_dict['valor__sum'] or Decimal('0.00')
            self.save()

            if hasattr(self, 'agrupamentoemendaloa'):
                registros.delete()
                self.agrupamentoemendaloa.save()
            else:
                if old_self:
                    valor_old = old_self.valor
                    tipo_old = old_self.tipo
                    unidade_old = old_self.unidade
                else:
                    valor_old = self.valor
                    tipo_old = self.tipo
                    unidade_old = self.unidade

                if tipo_old != self.tipo or unidade_old != self.unidade:
                    registros.delete()

                if registros.exists():
                    soma_registros_old = registros.aggregate(Sum('valor')).get('valor__sum', Decimal('0.00'))
                    soma_registros = Decimal('0.00')
                    for r in registros:
                        r.valor = quantize(r.valor * self.valor / valor_old, rounding=ROUND_HALF_DOWN) if valor_old else Decimal('0.00')
                        soma_registros = soma_registros + r.valor
                        r.save()
                    divergencia = soma_registros_old - soma_registros
                    if not soma_registros_old and divergencia:
                        r = registros.last()
                        r.valor = r.valor + divergencia
                        r.save()
                else:
                    # criar um registro contabil com o valor da emenda com base no tipo da unidade orcamentaria
                    if self.loa.despesa_default_deducao_diversos or self.loa.despesa_default_deducao_educacao or self.loa.despesa_default_deducao_saude:
                        if self.unidade and self.unidade.area == UnidadeOrcamentaria.SAUDE_CHOICE:
                            despesa = self.loa.despesa_default_deducao_saude
                        elif self.unidade and self.unidade.area == UnidadeOrcamentaria.EDUCACAO_CHOICE:
                            despesa = self.loa.despesa_default_deducao_educacao
                        else:
                            despesa = self.loa.despesa_default_deducao_diversos

                        if despesa:
                            rc = EmendaLoaRegistroContabil()
                            rc.emendaloa = self
                            rc.despesa = despesa
                            rc.valor = self.valor * (-1)
                            rc.save()
        else:
            registros.delete()
            self.save()
            qspa = self.emendaloaparlamentar_set.all()
            valores = [quantize(self.valor / qspa.count())] * qspa.count()
            sum_valores = sum(valores)
            resto = self.valor - sum_valores
            if resto:
                valores[-1] = valores[-1] + resto

            elpv = zip(qspa, valores)

            for elp, v in elpv:
                elp.valor = v
                elp.save()
        return self

    def save(
            self, force_insert=False, force_update=False, using=None, update_fields=None):
        if self.unidade:
            self.indicacao = self.unidade.especificacao

        creating = not self.pk

        if not self._syncing and not creating:
            self._syncing = True
            r = self.sync()
            self._syncing = False
            return r

        r = models.Model.save(self, force_insert=force_insert, force_update=force_update, using=using, update_fields=update_fields)

        self.loa.update_disponibilidades()
        return r


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
        verbose_name=_('LOA'),
        related_name='ajusteloa_set',
        on_delete=PROTECT)

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
        on_delete=PROTECT)

    emendaloa = models.ForeignKey(
        EmendaLoa,
        blank=True, null=True, default=None,
        verbose_name=_('Emenda Impositiva'),
        related_name='registroajusteloa_set',
        on_delete=PROTECT)

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
        soma = self.soma_valor
        str_v = formats.number_format(soma, force_grouping=True)
        if '-' in str_v:
            str_v = f'({str_v[1:]})'
        return str_v

    @property
    def soma_valor(self):
        soma = sum(
            list(
                filter(
                    lambda x: x, self.registroajusteloaparlamentar_set.values_list(
                        'valor', flat=True)
                )
            )
        )
        return soma

    def __str__(self):
        return f'R$ {self.str_valor} - {self.oficio_ajuste_loa}'


class RegistroAjusteLoaParlamentar(models.Model):

    registro = models.ForeignKey(
        RegistroAjusteLoa,
        verbose_name=_('Registro de Ajuste'),
        related_name='registroajusteloaparlamentar_set',
        on_delete=PROTECT)

    parlamentar = models.ForeignKey(
        Parlamentar,
        related_name='registroajusteloaparlamentar_set',
        verbose_name=_('Parlamentar'),
        on_delete=PROTECT)

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


def prestacaoconta_upload_path(instance, filename):
    return texto_upload_path(
        instance,
        filename,
        subpath=instance.prestacao_conta.loa.ano
        )


class PrestacaoContaLoa(models.Model):

    loa = models.ForeignKey(
        Loa,
        verbose_name=_('LOA'),
        related_name='prestacaoconta_set',
        on_delete=PROTECT)

    data_envio = models.DateField(
        verbose_name=_('Data de Envio'),
        blank=True, null=True, default=None)

    epigrafe = models.CharField(
        max_length=100,
        verbose_name=_("Epígrafe"))

    metadata = JSONField(
        verbose_name=_('Metadados'),
        blank=True, null=True, default=None, encoder=DjangoJSONEncoder)

    class Meta:
        verbose_name = _('Prestação de Conta')
        verbose_name_plural = _(
            'Prestações de Conta')
        ordering = ['id']

    def __str__(self):
        return f'{self.epigrafe} - {self.loa.ano}'


class ArquivoPrestacaoContaLoa(models.Model):

    FIELDFILE_NAME = ('arquivo',)

    prestacao_conta = models.ForeignKey(
        PrestacaoContaLoa,
        verbose_name=_('Prestação de Conta LOA'),
        related_name='arquivoprestacaocontaloa_set',
        on_delete=PROTECT)

    arquivo = PortalFileField(
        blank=True,
        null=True,
        upload_to=prestacaoconta_upload_path,
        verbose_name=_('Arquivo Anexo'),
        max_length=512)

    descricao = models.CharField(
        max_length=256,
        verbose_name=_("Descrição"), default='', blank=True)

    class Meta:
        verbose_name = _('Arquivo da Prestação de Conta LOA')
        verbose_name_plural = _(
            'Arquivos da Prestação de Conta LOA')
        ordering = ['id']

    def __str__(self):
        return f'{self.descricao} - {self.prestacao_conta.loa.ano}'

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

        return models.Model.save(self, force_insert=False,
                                 force_update=force_update,
                                 using=using,
                                 update_fields=update_fields)


class PrestacaoContaRegistro(models.Model):

    class SituacaoChoices(models.TextChoices):
        EM_TRAMITACAO = 'EM_TRAMITACAO', _('Em Tramitação')
        FINALIZADO = 'FINALIZADO', _('Finalizado')
        OUTRO = 'OUTRO', _('Outros (Detalhar)')

    prestacao_conta = models.ForeignKey(
        PrestacaoContaLoa,
        verbose_name=_('Prestação de Conta LOA'),
        related_name='prestacaocontaregistro_set',
        on_delete=PROTECT)

    registro_ajuste = models.ForeignKey(
        RegistroAjusteLoa,
        verbose_name=_('Registro de Ajuste Técnico'),
        related_name='prestacaocontaregistro_set',
        on_delete=PROTECT,
        blank=True, null=True, default=None
        )

    emendaloa = models.ForeignKey(
        EmendaLoa,
        blank=True, null=True, default=None,
        verbose_name=_('Emenda Impositiva'),
        related_name='prestacaocontaregistro_set',
        on_delete=PROTECT
        )

    detalhamento = models.TextField(
        verbose_name=_("Detalhamento"),
        blank=True, null=True, default=''
        )

    situacao = models.CharField(
        choices=SituacaoChoices.choices,
        max_length=20,
        default=SituacaoChoices.EM_TRAMITACAO,
        verbose_name=_("Situação"))

    class Meta:
        verbose_name = _('Registro de Prestação de Conta')
        verbose_name_plural = _('Registros de Prestação de Conta')
        ordering = ['id']

    def __str__(self):
        return f'{self.prestacao_conta.loa.ano} - {self.registro_ajuste or self.emendaloa}'


class ElementoBase(models.Model):

    loa = models.ForeignKey(
        Loa,
        verbose_name=_('Loa'),
        related_name='+',
        on_delete=PROTECT)

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

    recebe_emenda_impositiva = models.BooleanField(
        default=False,
        verbose_name=_('Recebe Verbas Emenda Impositiva'),
    )

    SAUDE_CHOICE = 10
    EDUCACAO_CHOICE = 20
    ASSISTENCIA_SOCIAL_CHOICE = 30
    SEGURANCA_PUBLICA_CHOICE = 40
    CULTURA_CHOICE = 50
    ESPORTE_CHOICE = 60
    OUTROS_CHOICE = 70

    area = models.PositiveSmallIntegerField(
        choices=(
            (SAUDE_CHOICE, _('Saúde')),
            (EDUCACAO_CHOICE, _('Educação')),
            (ASSISTENCIA_SOCIAL_CHOICE, _('Assistência Social')),
            (SEGURANCA_PUBLICA_CHOICE, _('Segurança Pública')),
            (CULTURA_CHOICE, _('Cultura')),
            (ESPORTE_CHOICE, _('Esporte')),
            (OUTROS_CHOICE, _('Outros')),
        ),
        default=OUTROS_CHOICE,
        verbose_name=_('Tipo Geral'),
    )



    class Meta:
        verbose_name = _('Unidade Orçamentária')
        verbose_name_plural = _('Unidades Orçamentárias')
        ordering = ['codigo']


class Funcao(ElementoBase):

    class Meta:
        verbose_name = _('Função')
        verbose_name_plural = _('Funções')
        ordering = ['codigo']

    def __str__(self):
        return f'{self.codigo} - {self.especificacao} ({self.loa.ano})'


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
        return f'{self.codigo}:{self.cod_natureza}/{self.cod_fonte} - {self.especificacao}'


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
        on_delete=PROTECT)

    valor = models.DecimalField(
        max_digits=14, decimal_places=2, default=Decimal('0.00'),
        verbose_name=_('Valor (R$)'),
    )

    def __str__(self):
        return f'R$ {self.str_valor} - {self.despesa}'

    @property
    def str_valor(self):
        str_valor = formats.number_format(self.valor, force_grouping=True)
        str_valor = ' ' * (self._meta.get_field('valor').max_digits - len(str_valor)) + str_valor
        return str_valor

    def delete(self, *args, **kwargs):
        # remove emenda de agrupamento que possa pertercer sem causar recursividade do agrupamentoemendaloa_pre_delete
        run_sql(f'DELETE FROM loa_agrupamentoemendaloa WHERE emendaloa_id = {self.emendaloa.id}')
        # run_sql acima substitui: AgrupamentoEmendaLoa.objects.filter(emendaloa=self.emendaloa).delete()

        return super().delete(*args, **kwargs)


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


class Agrupamento(models.Model):

    loa = models.ForeignKey(
        Loa,
        verbose_name=_('LOA'),
        related_name='agrupamento_set',
        on_delete=PROTECT)

    nome = models.CharField(
        verbose_name=_('Nome do Agrupamento'), max_length=256)

    emendas = models.ManyToManyField(
        EmendaLoa,
        through='AgrupamentoEmendaLoa',
        related_name='agrupamento_set',
        verbose_name=_('Emendas Impositivas/Modificativas'),
        through_fields=(
            'agrupamento',
            'emendaloa'))

    despesas = models.ManyToManyField(
        Despesa,
        through='AgrupamentoRegistroContabil',
        related_name='agrupamento_set',
        verbose_name=_('Registro Contabeis Agrupamento'),
        through_fields=(
            'agrupamento',
            'despesa'))

    class Meta:
        verbose_name = _('Agrupamento de Emenda Impositiva/Modificativas')
        verbose_name_plural = _(
            'Agrupamentos de Emendas Impositivas/Modificativas')
        ordering = ['id']

    def __str__(self):
        return self.nome

    def sync(self):
        registros = self.agrupamentoregistrocontabil_set.all()

        for emenda in self.emendas.all():
            emenda.registrocontabil_set.all().delete()

            deducoes = []
            insercoes = []
            soma_zero = Decimal('0.00')
            for r in registros:
                elrc = EmendaLoaRegistroContabil()
                elrc.emendaloa = emenda
                elrc.despesa = r.despesa
                elrc.valor = quantize(
                    emenda.valor * r.percentual / Decimal(100))
                elrc.save()

                soma_zero += r.percentual

                if r.percentual < Decimal('0.00'):
                    deducoes.append(elrc)
                else:
                    insercoes.append(elrc)

            if soma_zero == Decimal('0.00'):
                sum_deducoes = sum(map(lambda x: x.valor, deducoes))
                sum_insercoes = sum(map(lambda x: x.valor, insercoes))

                if abs(sum_deducoes) != emenda.valor and deducoes:
                    resto = emenda.valor + sum_deducoes
                    deducoes[-1].valor = deducoes[-1].valor - resto
                    deducoes[-1].save()

                if abs(sum_insercoes) != emenda.valor and insercoes:
                    resto = emenda.valor - sum_insercoes
                    insercoes[-1].valor = insercoes[-1].valor + resto
                    insercoes[-1].save()

            print()


class AgrupamentoEmendaLoa(models.Model):
    agrupamento = models.ForeignKey(
        Agrupamento,
        verbose_name=_('Agrupamento de Emenda Impositiva'),
        related_name='agrupamentoemendaloa_set',
        on_delete=CASCADE)

    emendaloa = models.OneToOneField(
        EmendaLoa,
        verbose_name=_('Emenda Impositiva'),
        related_name='agrupamentoemendaloa',
        on_delete=CASCADE)

    class Meta:
        verbose_name = _('Agrupamento de Emenda Impositiva')
        verbose_name_plural = _('Agrupamentos de Emendas Impositivas')
        ordering = ['id']

        unique_together = (
            (
                'agrupamento',
                'emendaloa',
            ),
        )


class AgrupamentoRegistroContabilManager(manager.Manager):

    use_for_related_fields = True

    def all_deducoes(self):
        qs = self.get_queryset()
        qs = qs.filter(percentual__lt=Decimal('0.00'))
        return qs

    def all_insercoes(self):
        qs = self.get_queryset()
        qs = qs.filter(percentual__gt=Decimal('0.00'))
        return qs


class AgrupamentoRegistroContabil(models.Model):

    DEDUCAO = 10
    INSERCAO = 20

    OPERACAO_CHOICE = (
        (DEDUCAO, _('Dedução')),
        (INSERCAO, _('Inserção'))
    )

    objects = AgrupamentoRegistroContabilManager()

    agrupamento = models.ForeignKey(
        Agrupamento,
        verbose_name=_('Agrupamento de Emenda Impositiva'),
        related_name='agrupamentoregistrocontabil_set',
        on_delete=CASCADE)

    despesa = models.ForeignKey(
        Despesa,
        blank=True, null=True, default=None,
        related_name='agrupamentoregistrocontabil_set',
        verbose_name=_('Despesa'),
        on_delete=CASCADE)

    operacao = models.PositiveSmallIntegerField(
        choices=OPERACAO_CHOICE,
        default=10, verbose_name=_('Operação'))

    percentual = models.DecimalField(
        max_digits=6, decimal_places=2, default=Decimal('100.00'),
        validators=PERCENTAGE_VALIDATOR,
        verbose_name=_('Percentual do Valor da Emenda'),
    )

    class Meta:
        verbose_name = _('Registro Contábil de Dedução e Inserção em Emendas')
        verbose_name_plural = _(
            'Registros Contábeis de Dedução e Inserção em Emendas')
        ordering = ['id']

        unique_together = (
            (
                'agrupamento',
                'despesa',
            ),
        )

    def __str__(self):
        percentual_str = formats.number_format(
            self.percentual, force_grouping=True)
        return f'{percentual_str}% - {self.despesa}'

    @property
    def str_percentual(self):
        return formats.number_format(self.percentual, force_grouping=True)


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

    cpfcnpj = models.TextField(
        verbose_name=_("CpfCNPJ"),
        blank=True, null=True, default=None)
    nome = models.TextField(
        verbose_name=_("Nome"),
        blank=True, null=True, default=None)
    historico = models.TextField(
        verbose_name=_("Histórico"),
        blank=True, null=True, default=None)
    tipo = models.TextField(
        verbose_name=_("Tipo"),
        blank=True, null=True, default=None)

    data = models.DateField(blank=True, null=True, verbose_name=_('Data'))

    orgao = models.ForeignKey(
        Orgao,
        related_name='despesapaga_set',
        verbose_name=_('Órgão'),
        on_delete=CASCADE)

    unidade = models.ForeignKey(
        UnidadeOrcamentaria,
        blank=True, null=True, default=None,
        related_name='despesapaga_set',
        verbose_name=_('Unidade Financeira'),
        on_delete=CASCADE)

    natureza = models.ForeignKey(
        Natureza,
        blank=True, null=True, default=None,
        verbose_name=_('Natureza'),
        related_name='despesapaga_set',
        on_delete=CASCADE)

    fonte = models.ForeignKey(
        Fonte,
        blank=True, null=True, default=None,
        verbose_name=_('Fonte'),
        related_name='despesapaga_set',
        on_delete=CASCADE)

    valor = models.DecimalField(
        max_digits=14, decimal_places=2, default=Decimal('0.00'),
        verbose_name=_('Valor (R$)'),
    )

    class Meta:
        verbose_name = _('Despesa Paga')
        verbose_name_plural = _('Despesas Pagas')
        ordering = ['id']


class ReceitaOrcamentaria(models.Model):

    codigo = models.TextField(verbose_name=_("Código"))

    historico = models.TextField(
        verbose_name=_("Histórico"),
        blank=True, null=True, default=None)

    orgao = models.ForeignKey(
        Orgao,
        related_name='receitaorcamentaria_set',
        verbose_name=_('Órgão'),
        on_delete=CASCADE)

    valor = models.DecimalField(
        max_digits=14, decimal_places=2, default=Decimal('0.00'),
        verbose_name=_('Valor (R$)'),
    )

    class Meta:
        verbose_name = _('Receita Orçamentária')
        verbose_name_plural = _('Receitas Orçamentárias')
        ordering = ['id']


class ReceitaArrecadada(models.Model):

    data = models.DateField(blank=True, null=True, verbose_name=_('Data'))

    tipo = models.TextField(
        verbose_name=_("Tipo"),
        blank=True, null=True, default=None)

    historico = models.TextField(
        verbose_name=_("Histórico"),
        blank=True, null=True, default=None)

    receita = models.ForeignKey(
        ReceitaOrcamentaria,
        related_name='receitaarrecadada_set',
        verbose_name=_('Receita Orçamentária'),
        on_delete=CASCADE)

    valor = models.DecimalField(
        max_digits=14, decimal_places=2, default=Decimal('0.00'),
        verbose_name=_('Valor (R$)'),
    )

    class Meta:
        verbose_name = _('Receita Arrecadada')
        verbose_name_plural = _('Receitas Arrecadadas')
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

    erro = models.BooleanField(default=False)

    parent = models.ForeignKey(
        'self',
        blank=True, null=True, default=None,
        related_name='scrap_set',
        on_delete=CASCADE)

    class Meta:
        verbose_name = 'ScrapRecord'
        verbose_name_plural = 'ScrapRecord'
        ordering = ['id']

    def clean_text(self, text):
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

    def update_data_models(self):

        try:
            # with transaction.atomic():
            if 'despesa' in self.metadata['url_dict']['name']:
                if not self.codigo or self.codigo == 'TOTAL:':
                    return None
                self._update_despesa_paga()
            elif 'receita' in self.metadata['url_dict']['name']:
                if not self.codigo or self.codigo == 'TOTAL:':
                    return None
                self._update_receita_arrecadada()
            elif 'transferencia' in self.metadata['url_dict']['name']:
                self._update_transferencia_recursos()
            if self.erro:
                self.erro = False
                self.save(update_fields=('erro', ))
        except Exception as e:
            self.erro = True
            self.save(update_fields=('erro', ))

    def _update_transferencia_recursos(self):

        if self.metadata['url_dict']['format'] != 'csv':
            return None
        org = Orgao.objects.get(codigo=self.orgao, loa__ano=self.ano)

        content = self.content
        if isinstance(content, memoryview):
            content = content.tobytes()
        content = content.decode('utf-8-sig')
        file = StringIO(content)
        csv_data = csv.reader(file, delimiter=";")

        lista = list(csv_data)[1:]

        for row in lista:

            dt = datetime.strptime(row[0], "%d/%m/%Y").date()

            valor = Decimal(row[4].replace('.', '').replace(',', '.'))

            ro, created = ReceitaOrcamentaria.objects.get_or_create(
                codigo=row[1], orgao=org
            )

            if row[2] == 'Despesa':
                valor = quantize(valor * Decimal(-1))

            ra = ReceitaArrecadada.objects.get_or_create(
                receita=ro,
                data=dt,
                historico=row[1],
                tipo=row[2],
                valor=valor)

    def _update_receita_arrecadada(self):
        if self.metadata['url_dict']['format'] != 'csv':
            return None
        org = Orgao.objects.get(codigo=self.orgao, loa__ano=self.ano)

        ro, created = ReceitaOrcamentaria.objects.get_or_create(
            codigo=self.codigo, orgao=org
        )

        # if self.codigo != '11130311' or org.codigo != '03':
        #    return

        item_list = self.metadata['item_list']
        ro.historico = item_list[1]
        ro.valor = Decimal(item_list[2].replace('.', '').replace(',', '.'))
        ro.save()

        content = self.content
        if isinstance(content, memoryview):
            content = content.tobytes()
        content = content.decode('utf-8-sig')
        file = StringIO(content)
        csv_data = csv.reader(file, delimiter=";")

        lista = list(csv_data)
        idx_init = 0
        for idx_init, row in enumerate(lista):
            if not row[0]:
                break

        idx_init += 2
        rows = lista[idx_init:]

        rows = sorted(
            rows, key=lambda x:
            [
                tuple(map(int, x[0].split('/')[::-1])),
                x[1],
                x[3]
            ]
        )

        rows_filtered = []
        rows = list(enumerate(rows))
        for idx, row in rows:
            # rows_filtered.append(row)
            # continue

            if not idx or 'RETENÇÃO' not in row[2]:
                rows_filtered.append(row)
                continue

            if rows[idx][1] == rows[idx - 1][1]:
                continue

            rows_filtered.append(row)

        rows = rows_filtered

        if ro.receitaarrecadada_set.count() >= len(rows):
            return
        ro.receitaarrecadada_set.filter().delete()

        for row in rows:
            dt = datetime.strptime(row[0], "%d/%m/%Y").date()
            #print(self.codigo, row)

            valor = Decimal(row[3].replace('.', '').replace(',', '.'))

            # if row[2] == 'RETENÇÃO DE EMPENHO':
            #    ra = ReceitaArrecadada.objects.filter(
            #        receita=ro,
            #        historico=row[1],
            #        data=dt,
            #        valor=valor
            #    ).first()
            #    if ra:
            #        continue

            ra = ReceitaArrecadada()
            ra.receita = ro
            ra.data = dt
            ra.historico = row[1]
            ra.tipo = row[2]
            ra.valor = valor
            ra.save()

    def _update_despesa_paga(self):

        org = Orgao.objects.get(codigo=self.orgao, loa__ano=self.ano)
        dp = DespesaPaga.objects.filter(codigo=self.codigo, orgao=org).first()

        item_list = self.metadata['item_list']
        dt = datetime.strptime(item_list[1], "%d/%m/%Y").date()
        valor = Decimal(item_list[-1].replace('.', '').replace(',', '.'))

        if dp and dp.valor == valor and dp.data == dt and dp.natureza:
            return dp

        if dp and self.metadata['url_dict']['format'] == 'csv':
            return dp

        values = {}
        unidade = None
        natureza = None
        fonte = None

        if self.metadata['url_dict']['format'] == 'html':
            content = self.content
            if not isinstance(content, bytes):
                content = content.tobytes()
            content = content.decode('utf-8-sig')
            content = self.clean_text(
                self.clean_text(self.clean_text(content)))
            tables = bs(content, 'html.parser').findAll('table')
            if not tables:
                return None
            for row in tables[0].findAll('tr'):
                cols = row.findAll('td')
                values[cols[0].text] = cols[1].text
            unidade = UnidadeOrcamentaria.objects.filter(
                orgao=org,
                loa__ano=self.ano,
                codigo=values['Unidade Financeira:'][:2]
            ).first()

            try:
                nat = values['Elemento:']
                natureza = Natureza.objects.filter(
                    loa__ano=self.ano,
                    codigo=f'{nat[0]}.{nat[1]}.{nat[2:4]}.{nat[4:6]}.00'
                ).first()
            except:
                natureza = None

            try:
                fontestr = values['Fonte de Recursos:']
                fonte, created = Fonte.objects.get_or_create(
                    loa_id=self.ano,
                    codigo=fontestr[0:3]
                )
                if fonte.especificacao != fontestr[6:]:
                    fonte.especificacao = fontestr[6:]
                    fonte.save()
            except:
                fonte = None

        dp, created = DespesaPaga.objects.get_or_create(
            codigo=self.codigo,
            orgao=org,
        )
        dp.cpfcnpj = item_list[3]
        dp.nome = item_list[2]
        dp.tipo = item_list[4]
        dp.historico = values.get('Historico:', None)

        dp.unidade = unidade
        dp.natureza = natureza
        dp.fonte = fonte

        dp.valor = valor
        dp.data = dt
        dp.save()

        return dp


class NaturezaJuridica(models.Model):

    codigo = models.CharField(
        max_length=4,
        verbose_name=_("Código"),
        validators=[RegexValidator(r'^\d{4}$', _('Código inválido'))],
    )

    descricao = models.CharField(
        max_length=256,
        verbose_name=_("Descrição"),
    )

    class Meta:
        verbose_name = _('Natureza Jurídica')
        verbose_name_plural = _('Naturezas Jurídicas')
        ordering = ['codigo']

    def __str__(self):
        return f'{self.codigo} - {self.descricao}'

class TipoEntidade(models.Model):

    codigo = models.CharField(
        max_length=3,
        verbose_name=_("Código"),
        validators=[RegexValidator(r'^\d{3}$', _('Código inválido'))],
    )

    descricao = models.CharField(
        max_length=256,
        verbose_name=_("Descrição"),
    )

    SAUDE_CHOICE = 10
    EDUCACAO_CHOICE = 20
    ASSISTENCIA_SOCIAL_CHOICE = 30
    SEGURANCA_PUBLICA_CHOICE = 40
    CULTURA_CHOICE = 50
    ESPORTE_CHOICE = 60
    OUTROS_CHOICE = 70

    #tipo_geral é uma classificação mais ampla que agrupa vários tipos de entidade
    # será um choice com valores fixos definidos no código sendo: saúde, educação, assistência social, segurança pública, cultura, esporte, outros. criando através de números
    tipo_geral = models.PositiveSmallIntegerField(
        choices=(
            (SAUDE_CHOICE, _('Saúde')),
            (EDUCACAO_CHOICE, _('Educação')),
            (ASSISTENCIA_SOCIAL_CHOICE, _('Assistência Social')),
            (SEGURANCA_PUBLICA_CHOICE, _('Segurança Pública')),
            (CULTURA_CHOICE, _('Cultura')),
            (ESPORTE_CHOICE, _('Esporte')),
            (OUTROS_CHOICE, _('Outros')),
        ),
        default=OUTROS_CHOICE,
        verbose_name=_('Tipo Geral'),
    )

    class Meta:
        verbose_name = _('Tipo de Entidade')
        verbose_name_plural = _('Tipos de Entidades')
        ordering = ['codigo']

    def __str__(self):
        return f'{self.codigo} - {self.descricao}'

class Entidade(models.Model):
    """ Entidades públicas ou privadas que recebem recursos de emendas impositivas/modificativas.
    """

    nome_fantasia = models.CharField(
        max_length=256,
        verbose_name=_("Nome"),
    )

    razao_social = models.CharField(
        max_length=256,
        verbose_name=_("Nome Empresarial"),
    )

    cpfcnpj = models.CharField(
        max_length=18,
        blank=True, null=True, default=None,
        verbose_name=_("CNPJ"),
        #validators=[CNPJValidator()],
    )

    cnes = models.CharField(
        max_length=7,
        blank=True, null=True, default=None,
        verbose_name=_("CNES"),
        validators=[RegexValidator(r'^\d{7}$', _('CNES inválido'))],
    )

    natureza_juridica = models.ForeignKey(
        NaturezaJuridica,
        blank=True, null=True, default=None,
        verbose_name=_("Natureza Jurídica"),
        on_delete=SET_NULL,
    )

    tipo_entidade = models.ForeignKey(
        TipoEntidade,
        blank=True, null=True, default=None,
        verbose_name=_("Tipo de Entidade"),
        on_delete=SET_NULL,
    )

    metadata = JSONField(
        verbose_name=_('Metadados'),
        blank=True, null=True, default=dict, encoder=DjangoJSONEncoder)

    ativo = models.BooleanField(
        default=False,
        verbose_name=_('Ativo'),
    )


    class Meta:
        verbose_name = _('Entidade')
        verbose_name_plural = _('Entidades')
        ordering = ['nome_fantasia']
        unique_together = (
            ('cpfcnpj', 'cnes'),
        )

    def __str__(self):
        return f'{self.nome_fantasia} - {self.tipo_entidade.descricao if self.tipo_entidade else ""} - {"CNES:" if self.cnes else "CNPJ:"} {self.cnes or self.cpfcnpj or "Sem Identificação"}'