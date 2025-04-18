from functools import cached_property
from django.contrib.contenttypes.fields import GenericRelation
from django.db.models.fields.json import JSONField
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from django.template import defaultfilters
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from model_utils import Choices

from cmj.core.models import CertidaoPublicacao
from cmj.diarios.models import VinculoDocDiarioOficial, DiarioOficial
from cmj.mixins import CommonMixin
from cmj.utils import restringe_tipos_de_arquivo_midias
from sapl.base.models import Autor
from sapl.compilacao.models import TextoArticulado
from sapl.materia.models import MateriaLegislativa
from sapl.utils import (RANGE_ANOS, YES_NO_CHOICES,
                        restringe_tipos_de_arquivo_txt,
                        texto_upload_path,
                        get_settings_auth_user_model,
                        OverwriteStorage,
                        PortalFileField)


class AssuntoNorma(models.Model):
    assunto = models.CharField(max_length=50, verbose_name=_('Assunto'))
    descricao = models.CharField(
        max_length=250, blank=True, verbose_name=_('Descrição'))

    class Meta:
        verbose_name = _('Assunto de Norma Jurídica')
        verbose_name_plural = _('Assuntos de Normas Jurídicas')
        ordering = ['assunto']

    def __str__(self):
        return self.assunto


class TipoNormaJuridica(models.Model):
    # TODO transform into Domain Model and use an FK for the field
    EQUIVALENTE_LEXML_CHOICES = ((name, name) for name in
                                 ('constituicao',
                                  'ementa.constitucional',
                                  'lei.complementar',
                                  'lei.delegada',
                                  'lei',
                                  'decreto.lei',
                                  'medida.provisoria',
                                  'decreto',
                                  'lei.organica',
                                  'emenda.lei.organica',
                                  'decreto.legislativo',
                                  'resolucao',
                                  'regimento.interno',
                                  ))
    equivalente_lexml = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_('Equivalente LexML'),
        choices=EQUIVALENTE_LEXML_CHOICES)
    sigla = models.CharField(max_length=3, verbose_name=_('Sigla'))
    descricao = models.CharField(max_length=50, verbose_name=_('Descrição'))

    relevancia = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Relevância'),)

    origem_processo_legislativo = models.BooleanField(null=True,
        blank=True, default=True, verbose_name=_('Possui Origem no Processo Legislativo?'),
        choices=YES_NO_CHOICES)

    class Meta:
        verbose_name = _('Tipo de Norma Jurídica')
        verbose_name_plural = _('Tipos de Norma Jurídica')
        ordering = ['descricao']

    def __str__(self):
        return self.descricao


def norma_upload_path(instance, filename):
    return texto_upload_path(instance, filename, subpath=instance.ano)


class NormaJuridica(CommonMixin):
    FIELDFILE_NAME = ('texto_integral', )

    ESFERA_FEDERACAO_CHOICES = Choices(
        ('M', 'municipal', _('Municipal')),
        ('E', 'estadual', _('Estadual')),
        ('F', 'federal', _('Federal')),
    )

    metadata = JSONField(
        verbose_name=_('Metadados'),
        blank=True, null=True, default=None, encoder=DjangoJSONEncoder)

    texto_integral = PortalFileField(
        blank=True,
        null=True,
        upload_to=norma_upload_path,
        verbose_name=_('Texto Integral'),
        storage=OverwriteStorage(),
        validators=[restringe_tipos_de_arquivo_txt],
        max_length=512)

    tipo = models.ForeignKey(
        TipoNormaJuridica,
        on_delete=models.PROTECT,
        related_name='normajuridica_set',
        verbose_name=_('Tipo da Norma Jurídica'))
    materia = models.ForeignKey(
        MateriaLegislativa, blank=True, null=True,
        on_delete=models.PROTECT, verbose_name=_('Matéria'))
    numero = models.CharField(
        max_length=8,
        verbose_name=_('Número'))
    ano = models.PositiveSmallIntegerField(verbose_name=_('Ano'),
                                           choices=RANGE_ANOS)

    mostrar_deliberacao = models.BooleanField(
        verbose_name=_('Mostrar Deliberação?'),
        choices=YES_NO_CHOICES, default=False)

    esfera_federacao = models.CharField(
        max_length=1,
        verbose_name=_('Esfera Federação'),
        choices=ESFERA_FEDERACAO_CHOICES)
    data = models.DateField(blank=False, null=True, verbose_name=_('Data'))
    data_publicacao = models.DateField(
        blank=True, null=True, verbose_name=_('Data de Publicação'))

    ementa = models.TextField(verbose_name=_('Ementa'))
    indexacao = models.TextField(
        blank=True, verbose_name=_('Indexação'))
    observacao = models.TextField(
        blank=True, verbose_name=_('Observação'))
    complemento = models.BooleanField(null=True,
        blank=True, verbose_name=_('Complementar ?'),
        choices=YES_NO_CHOICES)

    # XXX was a CharField (attention on migrate)
    assuntos = models.ManyToManyField(
        AssuntoNorma, blank=True,
        verbose_name=_('Assuntos'))
    data_vigencia = models.DateField(
        blank=True, null=True, verbose_name=_('Data Fim Vigência'))
    timestamp = models.DateTimeField(null=True)

    texto_articulado = GenericRelation(
        TextoArticulado, related_query_name='texto_articulado')

    diariosoficiais = GenericRelation(
        VinculoDocDiarioOficial,
        related_query_name='diariosoficiais')

    data_ultima_atualizacao = models.DateTimeField(
        blank=True, null=True,
        auto_now=True,
        verbose_name=_('Data'))

    autores = models.ManyToManyField(
        Autor,
        through='AutoriaNorma',
        through_fields=('norma', 'autor'),
        symmetrical=False)

    norma_de_destaque = models.BooleanField(verbose_name=_('Norma de Destaque ?'),
                                            choices=YES_NO_CHOICES,
                                            default=False)

    apelido = models.TextField(
        blank=True, verbose_name=_('Apelido'))

    user = models.ForeignKey(
        get_settings_auth_user_model(),
        verbose_name=_('Usuário'),
        on_delete=models.PROTECT,
        null=True,
        blank=True
    )
    ip = models.CharField(
        verbose_name=_('IP'),
        max_length=30,
        blank=True,
        default=''
    )

    checkcheck = models.BooleanField(
        verbose_name=_('Registro de Norma Jurídica Auditado?'),
        default=False,
        choices=YES_NO_CHOICES)

    _certidao = GenericRelation(
        CertidaoPublicacao, related_query_name='normajuridica_cert')

    _diario = GenericRelation(
        VinculoDocDiarioOficial, related_query_name='normajuridica_diario')

    class Meta:
        verbose_name = _('Norma Jurídica')
        verbose_name_plural = _('Normas Jurídicas')
        ordering = ['-data', '-id']

    def get_normas_relacionadas(self):
        principais = NormaRelacionada.objects.filter(
            norma_principal=self.id).order_by('norma_principal__data',
                                              'norma_relacionada__data')
        relacionadas = NormaRelacionada.objects.filter(
            norma_relacionada=self.id).order_by('norma_principal__data',
                                                'norma_relacionada__data')
        return (principais, relacionadas)

    def get_anexos_norma_juridica(self):
        anexos = AnexoNormaJuridica.objects.filter(
            norma=self.id)
        return anexos

    @property
    def sigla_norma_conversao(self):
        return {
            'LOM': ('LOM', ()),
            'RI': ('RI', ()),
            'LEI': ('L', ('numero',)),
            'LC': ('LC', ('numero','ano')),
            'LE': ('LE', ('numero','ano')),
            'DL': ('DL', ('numero','ano')),
            'PLE': ('PLE', ('numero','ano')),
            'PR': ('PR', ('numero','ano')),
            'RES': ('RES', ('numero','ano')),
            'ATG': ('ATG', ('numero','ano')),
            'ELO': ('ELO', ('numero','ano')),
        }

    def urlize(self):
        sigla = self.tipo.sigla
        url = f'/{sigla}'
        if sigla in self.sigla_norma_conversao:
            url = f'/{self.sigla_norma_conversao[sigla][0]}'
            sufix = []
            for field in self.sigla_norma_conversao[sigla][1]:
                sufix.append(f'{getattr(self, field)}')
            url += '-'.join(sufix)
        return url

    @property
    def is_signed(self):
        try:
            return self.metadata and self.metadata['signs'] and \
                self.metadata['signs']['texto_integral'] and \
                self.metadata['signs']['texto_integral']['signs']
        except:
            return False

    @property
    def certidao(self):
        return self._certidao.order_by('-id').first()

    @property
    def render_description(self):
        return str(self.ementa)

    @property
    def diariooficial(self):
        try:
            return self._diario.all().first().diario
        except:
            return None

    @property
    def __descr__(self):
        return self.ementa

    @property
    def epigrafe(self):
        return _('%(tipo)s nº %(numero)s de %(data)s') % {
            'tipo': self.tipo,
            'numero': self.numero,
            'data': defaultfilters.date(self.data, r"d \d\e F \d\e Y")}

    def __str__(self):
        return _('%(tipo)s nº %(numero)s de %(data)s') % {
            'tipo': self.tipo,
            'numero': self.numero,
            'data': defaultfilters.date(self.data, r"d \d\e F \d\e Y")}

    def delete(self, using=None, keep_parents=False):
        if self.texto_integral:
            self.texto_integral.delete()

        return models.Model.delete(
            self, using=using, keep_parents=keep_parents)

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):

        if not self.pk and self.texto_integral:
            texto_integral = self.texto_integral
            self.texto_integral = None
            models.Model.save(self, force_insert=force_insert,
                              force_update=force_update,
                              using=using,
                              update_fields=update_fields)
            self.texto_integral = texto_integral

        return models.Model.save(self, force_insert=force_insert,
                                 force_update=force_update,
                                 using=using,
                                 update_fields=update_fields)


def get_ano_atual():
    return timezone.now().year


class NormaEstatisticas(models.Model):
    usuario = models.CharField(max_length=50)
    horario_acesso = models.DateTimeField(
        blank=True, null=True)
    ano = models.PositiveSmallIntegerField(verbose_name=_('Ano'),
                                           choices=RANGE_ANOS, default=get_ano_atual)
    norma = models.ForeignKey(NormaJuridica,
                              on_delete=models.CASCADE)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return _('Usuário: %(usuario)s, Norma: %(norma)s') % {
            'usuario': self.usuario, 'norma': self.norma}


class AutoriaNorma(models.Model):
    autor = models.ForeignKey(Autor,
                              verbose_name=_('Autor'),
                              on_delete=models.CASCADE)
    norma = models.ForeignKey(
        NormaJuridica, on_delete=models.CASCADE,
        verbose_name=_('Norma Jurídica'))
    primeiro_autor = models.BooleanField(verbose_name=_('Primeiro Autor'),
                                         choices=YES_NO_CHOICES,
                                         default=False)

    class Meta:
        verbose_name = _('Autoria')
        verbose_name_plural = _('Autorias')
        unique_together = (('autor', 'norma'), )
        ordering = ('-primeiro_autor', 'autor__nome')

    def __str__(self):
        return _('Autoria: %(autor)s - %(norma)s') % {
            'autor': self.autor, 'norma': self.norma}


class LegislacaoCitada(models.Model):
    materia = models.ForeignKey(MateriaLegislativa, on_delete=models.CASCADE)
    norma = models.ForeignKey(NormaJuridica, on_delete=models.CASCADE)
    disposicoes = models.CharField(
        max_length=15, blank=True, verbose_name=_('Disposição'))
    parte = models.CharField(
        max_length=8, blank=True, verbose_name=_('Parte'))
    livro = models.CharField(
        max_length=7, blank=True, verbose_name=_('Livro'))
    titulo = models.CharField(
        max_length=7, blank=True, verbose_name=_('Título'))
    capitulo = models.CharField(
        max_length=7, blank=True, verbose_name=_('Capítulo'))
    secao = models.CharField(
        max_length=7, blank=True, verbose_name=_('Seção'))
    subsecao = models.CharField(
        max_length=7, blank=True, verbose_name=_('Subseção'))
    artigo = models.CharField(
        max_length=4, blank=True, verbose_name=_('Artigo'))
    paragrafo = models.CharField(
        max_length=3, blank=True, verbose_name=_('Parágrafo'))
    inciso = models.CharField(
        max_length=10, blank=True, verbose_name=_('Inciso'))
    alinea = models.CharField(
        max_length=3, blank=True, verbose_name=_('Alínea'))
    item = models.CharField(
        max_length=3, blank=True, verbose_name=_('Item'))

    class Meta:
        verbose_name = _('Legislação')
        verbose_name_plural = _('Legislações')
        ordering = ['id']

    def __str__(self):
        return str(self.norma)


class TipoVinculoNormaJuridica(models.Model):
    sigla = models.CharField(
        max_length=1, blank=True, verbose_name=_('Sigla'))
    descricao_ativa = models.CharField(
        max_length=50, blank=True, verbose_name=_('Descrição Ativa'))
    descricao_passiva = models.CharField(
        max_length=50, blank=True, verbose_name=_('Descrição Passiva'))
    revoga_integralmente = models.BooleanField(verbose_name=_('Revoga Integralmente?'),
                                               choices=YES_NO_CHOICES,
                                               default=False)

    class Meta:
        verbose_name = _('Tipo de Vínculo entre Normas Jurídicas')
        verbose_name_plural = _('Tipos de Vínculos entre Normas Jurídicas')
        ordering = ['id']

    def __str__(self):
        return self.descricao_ativa


class NormaRelacionada(models.Model):
    norma_principal = models.ForeignKey(
        NormaJuridica,
        related_name='norma_principal',
        on_delete=models.PROTECT,
        verbose_name=_('Norma Principal'))
    norma_relacionada = models.ForeignKey(
        NormaJuridica,
        related_name='norma_relacionada',
        on_delete=models.PROTECT,
        verbose_name=_('Norma Relacionada'))
    tipo_vinculo = models.ForeignKey(
        TipoVinculoNormaJuridica,
        on_delete=models.PROTECT,
        verbose_name=_('Tipo de Vínculo'))

    class Meta:
        verbose_name = _('Norma Relacionada')
        verbose_name_plural = _('Normas Relacionadas')
        ordering = ('norma_principal__data', 'norma_relacionada__data')

    def __str__(self):
        return _('Principal: %(norma_principal)s'
                 ' - Relacionada: %(norma_relacionada)s') % {
            'norma_principal': self.norma_principal,
            'norma_relacionada': self.norma_relacionada}


class AnexoNormaJuridica(CommonMixin):
    FIELDFILE_NAME = ('anexo_arquivo', )

    metadata = JSONField(
        verbose_name=_('Metadados'),
        blank=True, null=True, default=None, encoder=DjangoJSONEncoder)

    norma = models.ForeignKey(
        NormaJuridica,
        related_name='anexos_set',
        on_delete=models.PROTECT,
        verbose_name=_('Norma Jurídica'))
    assunto_anexo = models.TextField(
        blank=True,
        default="",
        verbose_name=_('Assunto do Anexo'),
        max_length=250
    )
    anexo_arquivo = PortalFileField(
        blank=True,
        null=True,
        upload_to=norma_upload_path,
        verbose_name=_('Arquivo Anexo'),
        storage=OverwriteStorage(),
        validators=[restringe_tipos_de_arquivo_midias])

    ano = models.PositiveSmallIntegerField(verbose_name=_('Ano'),
                                           choices=RANGE_ANOS)

    class Meta:
        verbose_name = _('Anexo da Norma Jurídica')
        verbose_name_plural = _('Anexos da Norma Jurídica')
        ordering = ('assunto_anexo', )

    def __str__(self):
        return _('Anexo: %(anexo)s da norma %(norma)s') % {
            'anexo': self.anexo_arquivo, 'norma': self.norma}

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):

        if not self.pk and self.anexo_arquivo:
            anexo_arquivo = self.anexo_arquivo
            self.anexo_arquivo = None
            models.Model.save(self, force_insert=force_insert,
                              force_update=force_update,
                              using=using,
                              update_fields=update_fields)
            self.anexo_arquivo = anexo_arquivo

        return models.Model.save(self, force_insert=force_insert,
                                 force_update=force_update,
                                 using=using,
                                 update_fields=update_fields)
