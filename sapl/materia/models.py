
import glob
import logging
import os
from time import sleep
from django.conf import settings
from django.contrib.auth.models import Group
from django.contrib.contenttypes.fields import GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from django.db.models import Q, F
from django.db.models.deletion import PROTECT
from django.db.models.fields.json import JSONField
from django.db.models.functions import Concat
from django.template import defaultfilters
from django.utils import formats, timezone
from django.utils.translation import gettext_lazy as _
from model_utils import Choices

from cmj.core.models import CertidaoPublicacao
from cmj.diarios.models import VinculoDocDiarioOficial, DiarioOficial
from cmj.mixins import CommonMixin, PluginSignMixin
from sapl.base.models import SEQUENCIA_NUMERACAO_PROTOCOLO, Autor, \
    TipoAutor, Metadata
from sapl.comissoes.models import Comissao, Reuniao
from sapl.compilacao.models import (PerfilEstruturalTextoArticulado,
                                    TextoArticulado)
from sapl.parlamentares.models import Parlamentar
from sapl.utils import (RANGE_ANOS, YES_NO_CHOICES, SaplGenericForeignKey,
                        SaplGenericRelation, restringe_tipos_de_arquivo_txt,
                        texto_upload_path, get_settings_auth_user_model,
                        OverwriteStorage, PortalFileField)

logger = logging.getLogger(__name__)

EM_TRAMITACAO = [(1, 'Sim'),
                 (0, 'Não')]


def grupo_autor():
    try:
        grupo = Group.objects.get(name='Autor')
    except Group.DoesNotExist:
        return None
    return grupo.id


class TipoProposicao(models.Model):
    descricao = models.CharField(
        max_length=50,
        verbose_name=_('Descrição'),
        unique=True,
        error_messages={
            'unique': _('Já existe um Tipo de Proposição com esta descrição.')
        })

    exige_assinatura_digital = models.BooleanField(
        default=True,
        verbose_name=_('Exigir Assinatura Digital'),
    )

    content_type = models.ForeignKey(
        ContentType, default=None,
        on_delete=models.PROTECT,
        verbose_name=_('Conversão de Meta-Tipos'),
        help_text=_("""
        Quando uma proposição é incorporada, ela é convertida de proposição
        para outro elemento dentro do Sapl. Existem alguns elementos que
        uma proposição pode se tornar. Defina este meta-tipo e em seguida
        escolha um Tipo Correspondente!
        """)
    )
    object_id = models.PositiveIntegerField(
        blank=True, null=True, default=None)
    tipo_conteudo_related = SaplGenericForeignKey(
        'content_type', 'object_id', verbose_name=_('Tipo Correspondente'))

    tipo_autores = models.ManyToManyField(
        TipoAutor,
        blank=True, verbose_name=_('Tipos de Autores'),
        help_text=_("""
                    Tipo de Autores que pode enviar este tipo de Proposição.
                    """))
    perfis = models.ManyToManyField(
        PerfilEstruturalTextoArticulado,
        blank=True, verbose_name=_('Perfis Estruturais de Textos Articulados'),
        help_text=_("""
                    Mesmo que em Configurações da Aplicação nas
                    Tabelas Auxiliares esteja definido que Proposições possam
                    utilizar Textos Articulados, ao gerar uma proposição,
                    a solução de Textos Articulados será disponibilizada se
                    o Tipo escolhido para a Proposição estiver associado a ao
                    menos um Perfil Estrutural de Texto Articulado.
                    """))

    class Meta:
        verbose_name = _('Tipo de Proposição')
        verbose_name_plural = _('Tipos de Proposições')
        ordering = ['id']

    def __str__(self):
        return self.descricao


class TipoMateriaManager(models.Manager):

    def reordene(self, exclude_pk=None):
        tipos = self.get_queryset()
        if exclude_pk:
            tipos = tipos.exclude(pk=exclude_pk)
        for sr, t in enumerate(tipos, 1):
            t.sequencia_regimental = sr
            t.save()

    def reposicione(self, pk, idx):
        tipos = self.reordene(exclude_pk=pk)

        self.get_queryset(
        ).filter(
            sequencia_regimental__gte=idx
        ).update(
            sequencia_regimental=models.F('sequencia_regimental') + 1
        )

        self.get_queryset(
        ).filter(
            pk=pk
        ).update(
            sequencia_regimental=idx
        )


AGRUPAMENTO_TIPOS_MATERIAS = (('1', _('Nível 1')),
                              ('2', _('Nível 2')),
                              ('3', _('Nível 3')),
                              ('4', _('Nível 4')),
                              ('5', _('Nível 5')),
                              ('6', _('Nível 6')),
                              ('7', _('Nível 7')),
                              ('8', _('Nível 8')),
                              ('9', _('Nível 9')))


class TipoMateriaLegislativa(models.Model):
    objects = TipoMateriaManager()
    sigla = models.CharField(max_length=5, verbose_name=_('Sigla'))
    descricao = models.CharField(max_length=50, verbose_name=_('Descrição '))
    # XXX o que é isso ?
    num_automatica = models.BooleanField(default=False)
    # XXX o que é isso ?
    quorum_minimo_votacao = models.PositiveIntegerField(blank=True, null=True)

    limite_por_autor_tramitando = models.PositiveIntegerField(
        blank=True, null=True,
        default=0,
        verbose_name=_('Limitar Protocolo por Autor'),
        )

    limite_minimo_coletivo = models.PositiveIntegerField(
        blank=True, null=True,
        default=0,
        verbose_name=_('Não Impõe Limites de Protocolo acima deste valor'),
        )

    tipo_proposicao = SaplGenericRelation(
        TipoProposicao,
        related_query_name='tipomaterialegislativa_set',
        fields_search=(
            ('descricao', '__icontains'),
            ('sigla', '__icontains')
        ))

    nivel_agrupamento = models.CharField(
        max_length=1,
        blank=True,
        verbose_name=_('Nível de Agrupamento'),
        choices=AGRUPAMENTO_TIPOS_MATERIAS)

    sequencia_numeracao = models.CharField(
        max_length=1,
        blank=True,
        verbose_name=_('Sequência de numeração'),
        choices=SEQUENCIA_NUMERACAO_PROTOCOLO)

    sequencia_regimental = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Sequência Regimental'),
        help_text=_('A sequência regimental diz respeito ao que define '
                    'o regimento da Casa Legislativa sobre qual a ordem '
                    'de entrada das proposições nas Sessões Plenárias.'))

    turnos_aprovacao = models.PositiveIntegerField(
        default=1,
        verbose_name=_('Turnos para aprovação.'),)

    prompt = models.TextField(
        blank=True,
        verbose_name=_('Prompt para Análise de IA.')
        )

    class Meta:
        verbose_name = _('Tipo de Matéria Legislativa')
        verbose_name_plural = _('Tipos de Matérias Legislativas')
        ordering = ['sequencia_regimental', 'descricao']

    def __str__(self):
        return self.descricao


class RegimeTramitacao(models.Model):
    descricao = models.CharField(max_length=50, verbose_name=_('Descrição'))

    sequencia_regimental = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Sequência Regimental'),
        help_text=_('A sequência regimental diz respeito ao que define '
                    'o regimento da Casa Legislativa sobre qual a ordem '
                    'de entrada das proposições nas Sessões Plenárias.'))

    class Meta:
        verbose_name = _('Regime de Tramitação')
        verbose_name_plural = _('Regimes de Tramitação')
        ordering = ['id']

    def __str__(self):
        return self.descricao


class Origem(models.Model):
    sigla = models.CharField(max_length=10, verbose_name=_('Sigla'))
    nome = models.CharField(max_length=50, verbose_name=_('Nome'))

    class Meta:
        verbose_name = _('Origem')
        verbose_name_plural = _('Origens')
        ordering = ['id']

    def __str__(self):
        return self.nome


TIPO_APRESENTACAO_CHOICES = Choices(('O', 'oral', _('Oral')),
                                    ('E', 'escrita', _('Escrita')))


def materia_upload_path(instance, filename):
    return texto_upload_path(instance, filename, subpath=instance.ano)


def anexo_upload_path(instance, filename):
    return texto_upload_path(instance, filename, subpath=instance.materia.ano)


class MateriaLegislativaManager(models.Manager):

    use_for_related_fields = True

    def materias_anexadas(self):
        return self.get_anexacao('filter').annotate(data_anexacao=F('materia_anexada_set__data_anexacao'))

    def materias_desanexadas(self):
        return self.get_anexacao('exclude').annotate(data_desanexacao=F('materia_anexada_set__data_desanexacao'))

    def get_anexacao(self, type_select):
        return getattr(
            self.get_queryset(), type_select
        )(
            Q(
                materia_anexada_set__data_desanexacao__isnull=True
            ) | Q(
                materia_anexada_set__data_desanexacao__gt=timezone.now()
            )
        )

    def materias_anexadas_ordem_crescente(self):
        return self.materias_anexadas().order_by('tipo__sequencia_regimental', 'ano', 'numero')


class MateriaLegislativa(CommonMixin):

    objects = MateriaLegislativaManager()

    FIELDFILE_NAME = ('texto_original',)

    metadata = JSONField(
        verbose_name=_('Metadados'),
        blank=True, null=True, default=None, encoder=DjangoJSONEncoder)

    tipo = models.ForeignKey(
        TipoMateriaLegislativa,
        on_delete=models.PROTECT,
        verbose_name=TipoMateriaLegislativa._meta.verbose_name)
    numero = models.PositiveIntegerField(verbose_name=_('Número'))
    ano = models.PositiveSmallIntegerField(verbose_name=_('Ano'),
                                           choices=RANGE_ANOS)
    numero_protocolo = models.PositiveIntegerField(
        blank=True, null=True, verbose_name=_('Número do Protocolo'))
    data_apresentacao = models.DateField(
        verbose_name=_('Data de Apresentação'))
    tipo_apresentacao = models.CharField(
        max_length=1, blank=True,
        verbose_name=_('Tipo de Apresentação'),
        choices=TIPO_APRESENTACAO_CHOICES)
    regime_tramitacao = models.ForeignKey(
        RegimeTramitacao,
        on_delete=models.PROTECT,
        verbose_name=_('Regime Tramitação'))
    data_publicacao = models.DateField(
        blank=True, null=True, verbose_name=_('Data de Publicação'))
    tipo_origem_externa = models.ForeignKey(
        TipoMateriaLegislativa,
        blank=True,
        null=True,
        related_name='tipo_origem_externa_set',
        on_delete=models.PROTECT,
        verbose_name=_('Tipo'))
    numero_origem_externa = models.CharField(
        max_length=10, blank=True, verbose_name=_('Número'))
    ano_origem_externa = models.PositiveSmallIntegerField(
        blank=True, null=True, verbose_name=_('Ano'), choices=RANGE_ANOS)
    data_origem_externa = models.DateField(
        blank=True, null=True, verbose_name=_('Data'))
    local_origem_externa = models.ForeignKey(
        Origem, blank=True, null=True,
        on_delete=models.PROTECT, verbose_name=_('Local de Origem'))
    apelido = models.CharField(
        max_length=50, blank=True, verbose_name=_('Apelido'))
    dias_prazo = models.PositiveIntegerField(
        blank=True, null=True, verbose_name=_('Dias Prazo'))
    data_fim_prazo = models.DateField(
        blank=True, null=True, verbose_name=_('Data Fim Prazo'))
    em_tramitacao = models.BooleanField(
        verbose_name=_('Em Tramitação?'),
        default=False,
        choices=YES_NO_CHOICES)
    polemica = models.BooleanField(null=True,
                                   blank=True, verbose_name=_('Matéria Polêmica?'))
    objeto = models.CharField(
        max_length=150, blank=True, verbose_name=_('Objeto'))
    complementar = models.BooleanField(null=True,
                                       blank=True, verbose_name=_('É Complementar?'))
    ementa = models.TextField(verbose_name=_('Ementa'))
    indexacao = models.TextField(
        blank=True, verbose_name=_('Indexação'))
    observacao = models.TextField(
        blank=True, verbose_name=_('Observação'))
    resultado = models.TextField(blank=True)
    # XXX novo

    anexadas = models.ManyToManyField(
        'self',
        blank=True,
        through='Anexada',
        symmetrical=False,
        related_name='anexo_de',
        through_fields=(
            'materia_principal',
            'materia_anexada'))

    similaridades = models.ManyToManyField(
        'self',
        blank=True,
        through='AnaliseSimilaridade',
        symmetrical=False,
        related_name='similaridade_set',
        through_fields=(
            'materia_1',
            'materia_2'))

    assuntos = models.ManyToManyField(
        'AssuntoMateria',
        blank=True,
        through='MateriaAssunto',
        symmetrical=False,
        through_fields=(
            'materia',
            'assunto'))
    texto_original = PortalFileField(
        blank=True,
        null=True,
        upload_to=materia_upload_path,
        verbose_name=_('Texto Original'),
        storage=OverwriteStorage(),
        validators=[restringe_tipos_de_arquivo_txt],
        max_length=512)

    texto_articulado = GenericRelation(
        TextoArticulado, related_query_name='texto_articulado')

    proposicao = GenericRelation(
        'Proposicao', related_query_name='proposicao')

    protocolo_gr = GenericRelation(
        'protocoloadm.Protocolo',
        object_id_field='conteudo_object_id',
        content_type_field='conteudo_content_type',
        related_query_name='protocolo_gr')

    diariosoficiais = GenericRelation(
        VinculoDocDiarioOficial,
        related_query_name='diariosoficiais')

    autores = models.ManyToManyField(
        Autor,
        through='Autoria',
        through_fields=('materia', 'autor'),
        symmetrical=False,)

    data_ultima_atualizacao = models.DateTimeField(
        blank=True, null=True,
        auto_now=True,
        verbose_name=_('Data'))

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

    arquivado = models.BooleanField(
        verbose_name=_('Arquivamento completo?'),
        default=False,
        choices=YES_NO_CHOICES)

    checkcheck = models.BooleanField(
        verbose_name=_('Processo Legislativo Auditado?'),
        default=False,
        choices=YES_NO_CHOICES)

    url_video = models.URLField(
        max_length=150, blank=True,
        verbose_name=_('URL Arquivo Vídeo (Formatos MP4 / FLV / WebM)'))

    _certidao = GenericRelation(
        CertidaoPublicacao, related_query_name='materialegislativa_cert')

    _metadata_model = GenericRelation(
        Metadata, related_query_name='materialegislativa_metadata')

    _diario = GenericRelation(
        VinculoDocDiarioOficial, related_query_name='materialegislativa_diario')

    class Meta:
        verbose_name = _('Matéria Legislativa')
        verbose_name_plural = _('Matérias Legislativas')
        # unique_together = (("tipo", "numero", "ano"),)
        ordering = ['-id']
        permissions = (
            ("can_access_impressos", "Can access impressos"),

            ("can_check_complete", "Pode checar conclusão de processo"),
        )
        indexes = [
            models.Index(fields=['-em_tramitacao']),
            models.Index(fields=['-data_apresentacao']),
            models.Index(fields=['-data_apresentacao', '-id'])
        ]

    @property
    def __descr__(self):
        return str(self.ementa)

    @property
    def render_description(self):
        return str(self.ementa)

    @property
    def certidao(self):
        return self._certidao.order_by('-id').first()

    @property
    def metadata_model(self):
        return self._metadata_model.order_by('-id').first()

    @property
    def diariooficial(self):
        try:
            return self._diario.all().first().diario
        except:
            return None

    def __str__(self):
        return _('%(tipo)s nº %(numero)s de %(ano)s') % {
            'tipo': self.tipo, 'numero': self.numero, 'ano': self.ano}

    @property
    def is_signed(self):
        try:
            return self.metadata and self.metadata['signs'] and \
                self.metadata['signs']['texto_original'] and \
                self.metadata['signs']['texto_original']['signs']
        except:
            return False

    @property
    def epigrafe(self):
        return _('%(tipo)s nº %(numero)s de %(data)s') % {
            'tipo': self.tipo,
            'numero': self.numero,
            'data': defaultfilters.date(
                self.data_apresentacao,
                r"d \d\e F \d\e Y"
            )}

    @property
    def epigrafe_short(self):
        return '{} {:03d}/{}'.format(self.tipo.sigla, self.numero, self.ano)

    def data_entrada_protocolo(self):
        '''
           hack: recuperar a data de entrada do protocolo sem gerar
           dependência circular
        '''
        from sapl.protocoloadm.models import Protocolo
        if self.ano and self.numero_protocolo:
            protocolo = Protocolo.objects.filter(
                ano=self.ano,
                numero=self.numero_protocolo).first()
            if protocolo:
                if protocolo.timestamp:
                    return protocolo.timestamp.date()
                elif protocolo.timestamp_data_hora_manual:
                    return protocolo.timestamp_data_hora_manual.date()
                elif protocolo.data:
                    return protocolo.data

            return ''

    def delete(self, using=None, keep_parents=False):
        if self.texto_original:
            self.texto_original.delete()

        for p in self.proposicao.all():
            p.conteudo_gerado_related = None
            p.cancelado = True
            p.save()

        for p in self.protocolo_gr.all():
            p.conteudo_protocolado = None
            p.save()

        return models.Model.delete(
            self, using=using, keep_parents=keep_parents)

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):

        if not self.pk and self.texto_original:
            texto_original = self.texto_original
            self.texto_original = None
            models.Model.save(self, force_insert=force_insert,
                              force_update=force_update,
                              using=using,
                              update_fields=update_fields)
            self.texto_original = texto_original

        if self.texto_original:
            self.clear_cache()

        return models.Model.save(self, force_insert=force_insert,
                                 force_update=force_update,
                                 using=using,
                                 update_fields=update_fields)

    def clear_cache(self, page=None, error=0):
        try:
            fcache = glob.glob(
                f'{self.texto_original.path}-p{page:0>3}*'
                if page else f'{self.texto_original.path}*.png'
            )

            for f in fcache:
                os.remove(f)

        except Exception as e:
            if not error:
                error = 1
            logger.error(f'Erro ao limpar cache de: {self.texto_original.path}. {e}')

        if error == 1:
            sleep(3)
            self.clear_cache(page=page, error=2)

    def autografos(self):
        return self.normajuridica_set.filter(tipo_id=27)

    def normajuridica(self):
        return self.normajuridica_set.exclude(tipo_id=27).first()

    def autografosvinculado_a_normajuridica(self):
        nr = self.normajuridica_set.exclude(
            tipo_id=27).first().norma_principal.filter(
                norma_relacionada__tipo_id=27)
        return nr

    @property
    def ultima_tramitacao(self):
        return self.tramitacao_set.first()

    def ultima_tramitacao_id(self):
        ultima = self.ultima_tramitacao
        if ultima:
            return ultima.id
        else:
            return None

    def autores_coautores(self):
        autorias = [
            autoria.autor for autoria in Autoria.objects.autores_coautores().filter(materia=self)]
        return autorias

    def homologar(self, compression=None, original2copia=True, x=193, y=50):
        from sapl.sessao.tasks import task_add_selo_votacao_function

        self.registrovotacao_set.all().update(selo_votacao=False)

        protocolo = self.protocolo_gr.first()

        if compression is None:
            autores = self.autores.values_list('sign_compression', flat=True)
            compression = all(autores)

        for field_file in self.FIELDFILE_NAME:
            if original2copia:
                paths = '{},{}'.format(
                    getattr(self, field_file).original_path,
                    getattr(self, field_file).path,
                )

            else:
                paths = getattr(self, field_file).path

            psm = PluginSignMixin()
            cmd = psm.cmd_mask

            params = {
                'plugin': psm.plugin_path,
                'comando': 'cert_protocolo',
                'in_file': paths,
                'certificado': settings.CERT_PRIVATE_KEY_ID,
                'password': settings.CERT_PRIVATE_KEY_ACCESS,
                'data_ocorrencia': formats.date_format(
                    timezone.localtime(
                        protocolo.timestamp) if protocolo.timestamp else p.data,
                    'd/m/Y'
                ),
                'hora_ocorrencia': formats.date_format(
                    timezone.localtime(
                        protocolo.timestamp) if protocolo.timestamp else protocolo.hora,
                    'H:i'
                ),
                'data_comando': formats.date_format(timezone.localtime(), 'd/m/Y'),
                'hora_comando': formats.date_format(timezone.localtime(), 'H:i'),
                'titulopre': 'Protocolo: {}/{}'.format(protocolo.numero, protocolo.ano),
                'titulo': self.epigrafe_short,
                'titulopos': '',
                'x': x,
                'y': y,
                'w': 12,
                'h': 60,
                'cor': "0, 76, 64, 255",
                'compression': compression,
                'debug': False # settings.DEBUG
            }
            cmd = cmd.format(
                **params
            )

            psm.run(cmd)

            del params['plugin']
            del params['in_file']
            del params['certificado']
            del params['password']
            del params['debug']
            del params['comando']
            self.metadata['selos'] = {'cert_protocolo': params}

            # print(cmd)
            # return

        self.save()

        task_add_selo_votacao_function(list(self.registrovotacao_set.values_list('id', flat=True)))


class AutoriaManager(models.Manager):

    use_for_related_fields = True

    def autores_coautores(self):
        return self.get_queryset().order_by('-primeiro_autor', 'autor__nome')


class Autoria(models.Model):

    objects = AutoriaManager()

    autor = models.ForeignKey(Autor,
                              verbose_name=_('Autor'),
                              on_delete=models.PROTECT)
    materia = models.ForeignKey(
        MateriaLegislativa, on_delete=models.CASCADE,
        verbose_name=_('Matéria Legislativa'))
    primeiro_autor = models.BooleanField(verbose_name=_('Primeiro Autor'),
                                         choices=YES_NO_CHOICES,
                                         default=False)

    class Meta:
        verbose_name = _('Autoria')
        verbose_name_plural = _('Autorias')
        unique_together = (('autor', 'materia'),)
        ordering = ('-primeiro_autor', 'autor__nome')

    def __str__(self):
        return _('Autoria: %(autor)s - %(materia)s') % {
            'autor': self.autor, 'materia': self.materia}


class AcompanhamentoMateria(models.Model):
    usuario = models.CharField(max_length=50)
    materia = models.ForeignKey(MateriaLegislativa, on_delete=models.CASCADE)
    email = models.EmailField(
        max_length=100, verbose_name=_('E-mail'))
    data_cadastro = models.DateField(auto_now_add=True)
    hash = models.CharField(max_length=8)
    confirmado = models.BooleanField(default=False)

    class Meta:
        verbose_name = _('Acompanhamento de Matéria')
        verbose_name_plural = _('Acompanhamentos de Matéria')
        ordering = ['id']

    def __str__(self):
        if self.data_cadastro is None:
            return _('%(materia)s - %(email)s') % {
                'materia': self.materia,
                'email': self.email
            }
        else:
            return _('%(materia)s - %(email)s - Registrado em: %(data)s') % {
                'materia': self.materia,
                'email': self.email,
                'data': str(self.data_cadastro.strftime('%d/%m/%Y'))
            }


class PautaReuniao(models.Model):
    reuniao = models.ForeignKey(
        Reuniao, related_name='reuniao_set',
        on_delete=models.CASCADE,
        verbose_name=_('Reunião')
    )
    materia = models.ForeignKey(
        MateriaLegislativa, related_name='materia_set',
        verbose_name=_('Matéria'),
        on_delete=PROTECT)

    class Meta:
        verbose_name = _('Matéria da Pauta')
        verbose_name_plural = ('Matérias da Pauta')
        ordering = ['id']

    def __str__(self):
        return _('Reunião: %(reuniao)s'
                 ' - Matéria: %(materia)s') % {
                     'reuniao': self.reuniao,
                     'materia': self.materia
        }


class Anexada(models.Model):
    materia_principal = models.ForeignKey(
        MateriaLegislativa, related_name='materia_principal_set',
        on_delete=models.CASCADE,
        verbose_name=_('Matéria Principal'))
    materia_anexada = models.ForeignKey(
        MateriaLegislativa, related_name='materia_anexada_set',
        on_delete=models.CASCADE,
        verbose_name=_('Matéria Anexada'))
    data_anexacao = models.DateField(verbose_name=_('Data Anexação'))
    data_desanexacao = models.DateField(
        blank=True, null=True, verbose_name=_('Data Desanexação'))

    class Meta:
        verbose_name = _('Anexada')
        verbose_name_plural = _('Anexadas')
        ordering = ['id']

    def __str__(self):
        return _('Principal: %(materia_principal)s'
                 ' - Anexada: %(materia_anexada)s') % {
            'materia_principal': self.materia_principal,
            'materia_anexada': self.materia_anexada}


class AssuntoMateria(models.Model):
    assunto = models.CharField(
        max_length=50,
        verbose_name=_('Assunto'))
    dispositivo = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_('Descrição do Dispositivo Legal'))

    class Meta:
        verbose_name = _('Assunto de Matéria')
        verbose_name_plural = _('Assuntos de Matéria')
        ordering = ['assunto']

    def __str__(self):
        return self.assunto


class DespachoInicial(models.Model):
    materia = models.ForeignKey(
        MateriaLegislativa, related_name="despachoinicial_set", on_delete=models.CASCADE)
    comissao = models.ForeignKey(
        Comissao, on_delete=models.CASCADE, verbose_name="Comissão")

    class Meta:
        verbose_name = _('Despacho Inicial')
        verbose_name_plural = _('Despachos Iniciais')
        ordering = ['id']

    def __str__(self):
        return _('%(materia)s - %(comissao)s') % {
            'materia': self.materia,
            'comissao': self.comissao}


class TipoDocumento(models.Model):
    descricao = models.CharField(
        max_length=50, verbose_name=_('Tipo Documento'))

    tipo_proposicao = SaplGenericRelation(
        TipoProposicao,
        related_query_name='tipodocumento_set',
        fields_search=(
            ('descricao', '__icontains'),
        ))

    limite_por_autor_tramitando = models.PositiveIntegerField(
        blank=True, null=True,
        default=0,
        verbose_name=_('Limitar Protocolo por Autor'),
        )

    limite_minimo_coletivo = models.PositiveIntegerField(
        blank=True, null=True,
        default=0,
        verbose_name=_('Não Impõe Limites de Protocolo acima deste valor'),
        )

    class Meta:
        verbose_name = _('Tipo de Documento')
        verbose_name_plural = _('Tipos de Documento')
        ordering = ['descricao']

    def __str__(self):
        return self.descricao


class DocumentoAcessorio(CommonMixin):
    FIELDFILE_NAME = ('arquivo',)

    metadata = JSONField(
        verbose_name=_('Metadados'),
        blank=True, null=True, default=None, encoder=DjangoJSONEncoder)

    materia = models.ForeignKey(MateriaLegislativa, on_delete=models.CASCADE)
    tipo = models.ForeignKey(TipoDocumento,
                             on_delete=models.PROTECT,
                             verbose_name=_('Tipo'))
    nome = models.CharField(
        max_length=50, verbose_name=_('Título do Documento'))

    data = models.DateField(blank=True, null=True,
                            default=None, verbose_name=_('Data'))
    autor = models.CharField(
        max_length=200, blank=True, verbose_name=_('Autor'))
    ementa = models.TextField(blank=True, verbose_name=_('Ementa'))
    indexacao = models.TextField(blank=True)
    arquivo = PortalFileField(
        blank=True,
        null=True,
        upload_to=anexo_upload_path,
        verbose_name=_('Texto Integral'),
        storage=OverwriteStorage(),
        validators=[restringe_tipos_de_arquivo_txt],
        max_length=512)

    proposicao = GenericRelation(
        'Proposicao', related_query_name='proposicao')

    protocolo_gr = GenericRelation(
        'protocoloadm.Protocolo',
        object_id_field='conteudo_object_id',
        content_type_field='conteudo_content_type',
        related_query_name='protocolo_gr')

    data_ultima_atualizacao = models.DateTimeField(
        blank=True, null=True,
        auto_now=True,
        verbose_name=_('Data'))

    @property
    def ano(self):
        return self.data.year

    @property
    def epigrafe_short(self):
        return self.nome

    class Meta:
        verbose_name = _('Documento Acessório')
        verbose_name_plural = _('Documentos Acessórios')
        ordering = 'data', 'id'

    @property
    def is_signed(self):
        try:
            return self.metadata and self.metadata['signs'] and \
                self.metadata['signs']['arquivo'] and \
                self.metadata['signs']['arquivo']['signs']
        except:
            return False

    def __str__(self):
        return _('%(tipo)s - %(nome)s de %(data)s por %(autor)s') % {
            'tipo': self.tipo,
            'nome': self.nome,
            'data': formats.date_format(
                self.data, "SHORT_DATE_FORMAT") if self.data else '',
            'autor': self.autor}

    def delete(self, using=None, keep_parents=False):

        for p in self.proposicao.all():
            p.conteudo_gerado_related = None
            p.save()

        for p in self.protocolo_gr.all():
            p.conteudo_protocolado = None
            p.save()

        arquivo = self.arquivo

        try:
            r = models.Model.delete(
                self, using=using, keep_parents=keep_parents)
        except Exception as e:

            for p in self.proposicao.all():
                p.conteudo_gerado_related = self
                p.save()
            raise Exception(e)

        if arquivo:
            arquivo.delete(save=False)

        return r

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

        return models.Model.save(self, force_insert=force_insert,
                                 force_update=force_update,
                                 using=using,
                                 update_fields=update_fields)


class MateriaAssunto(models.Model):
    assunto = models.ForeignKey(
        AssuntoMateria,
        on_delete=models.CASCADE,
        verbose_name=_('Assunto'))
    materia = models.ForeignKey(
        MateriaLegislativa,
        on_delete=models.CASCADE,
        verbose_name=_('Matéria'))

    class Meta:
        verbose_name = _('Relação Matéria - Assunto')
        verbose_name_plural = _('Relações Matéria - Assunto')
        ordering = ['assunto__assunto']

    def __str__(self):
        return _('%(materia)s - %(assunto)s') % {
            'materia': self.materia, 'assunto': self.assunto}


class Numeracao(models.Model):
    materia = models.ForeignKey(MateriaLegislativa, on_delete=models.CASCADE)
    tipo_materia = models.ForeignKey(
        TipoMateriaLegislativa,
        on_delete=models.PROTECT,
        verbose_name=_('Tipo de Matéria'))
    numero_materia = models.CharField(max_length=5,
                                      verbose_name=_('Número'))
    ano_materia = models.PositiveSmallIntegerField(verbose_name=_('Ano'),
                                                   choices=RANGE_ANOS)
    data_materia = models.DateField(verbose_name=_('Data'), null=True)

    class Meta:
        verbose_name = _('Numeração')
        verbose_name_plural = _('Numerações')
        ordering = ('materia',
                    'tipo_materia',
                    'numero_materia',
                    'ano_materia',
                    'data_materia',)

    def __str__(self):
        return _('%(numero)s/%(ano)s') % {
            'numero': self.numero_materia,
            'ano': self.ano_materia}


class Orgao(models.Model):
    nome = models.CharField(max_length=60, verbose_name=_('Nome'))
    sigla = models.CharField(max_length=10, verbose_name=_('Sigla'))
    unidade_deliberativa = models.BooleanField(
        choices=YES_NO_CHOICES,
        verbose_name=(_('Unidade Deliberativa')),
        default=False)
    endereco = models.CharField(
        max_length=100, blank=True, verbose_name=_('Endereço'))
    telefone = models.CharField(
        max_length=50, blank=True, verbose_name=_('Telefone'))

    autor = SaplGenericRelation(Autor,
                                related_query_name='orgao_set',
                                fields_search=(
                                    ('nome', '__icontains'),
                                    ('sigla', '__icontains')
                                ))

    class Meta:
        verbose_name = _('Órgão')
        verbose_name_plural = _('Órgãos')
        ordering = ['nome']

    def __str__(self):
        return _(
            '%(nome)s - %(sigla)s') % {'nome': self.nome, 'sigla': self.sigla}


class TipoFimRelatoria(models.Model):
    descricao = models.CharField(
        max_length=50, verbose_name=_('Tipo Fim Relatoria'))

    class Meta:
        verbose_name = _('Tipo Fim de Relatoria')
        verbose_name_plural = _('Tipos Fim de Relatoria')
        ordering = ['id']

    def __str__(self):
        return self.descricao


class Relatoria(models.Model):
    materia = models.ForeignKey(MateriaLegislativa, on_delete=models.CASCADE)
    parlamentar = models.ForeignKey(Parlamentar,
                                    on_delete=models.CASCADE,
                                    verbose_name=_('Parlamentar'))
    tipo_fim_relatoria = models.ForeignKey(
        TipoFimRelatoria,
        blank=True,
        null=True,
        on_delete=models.PROTECT,
        verbose_name=_('Motivo Fim Relatoria'))
    comissao = models.ForeignKey(
        Comissao, blank=True, null=True,
        on_delete=models.CASCADE, verbose_name=_('Comissão'))
    data_designacao_relator = models.DateField(
        verbose_name=_('Data Designação'))
    data_destituicao_relator = models.DateField(
        blank=True, null=True, verbose_name=_('Data Destituição'))

    class Meta:
        verbose_name = _('Relatoria')
        verbose_name_plural = _('Relatorias')
        ordering = ['id']

    def __str__(self):
        if self.tipo_fim_relatoria:
            return _('%(materia)s - %(tipo)s - %(data)s') % {
                'materia': self.materia,
                'tipo': self.tipo_fim_relatoria,
                'data': self.data_designacao_relator.strftime("%d/%m/%Y")}
        else:
            return _('%(materia)s - %(data)s') % {
                'materia': self.materia,
                'data': self.data_designacao_relator.strftime("%d/%m/%Y")}


class Parecer(models.Model):
    relatoria = models.ForeignKey(Relatoria, on_delete=models.CASCADE)
    materia = models.ForeignKey(MateriaLegislativa, on_delete=models.CASCADE)
    tipo_conclusao = models.CharField(max_length=3, blank=True)
    tipo_apresentacao = models.CharField(
        max_length=1, choices=TIPO_APRESENTACAO_CHOICES)
    parecer = models.TextField(blank=True)

    class Meta:
        verbose_name = _('Parecer')
        verbose_name_plural = _('Pareceres')
        ordering = ['id']

    def __str__(self):
        return _('%(relatoria)s - %(tipo)s') % {
            'relatoria': self.relatoria, 'tipo': self.tipo_apresentacao
        }


class Proposicao(CommonMixin):

    FIELDFILE_NAME = ('texto_original',)

    metadata = JSONField(
        verbose_name=_('Metadados'),
        blank=True, null=True, default=None, encoder=DjangoJSONEncoder)

    autor = models.ForeignKey(Autor,
                              null=True,
                              blank=True,
                              on_delete=models.PROTECT)
    tipo = models.ForeignKey(TipoProposicao, on_delete=models.PROTECT,
                             blank=False,
                             null=True,
                             verbose_name=_('Tipo'))

    # XXX data_envio was not null, but actual data said otherwise!!!
    data_envio = models.DateTimeField(
        blank=False, null=True, verbose_name=_('Data de Envio'))
    data_recebimento = models.DateTimeField(
        blank=True, null=True, verbose_name=_('Data de Recebimento'))
    data_devolucao = models.DateTimeField(
        blank=True, null=True, verbose_name=_('Data de Devolução'))

    descricao = models.TextField(verbose_name=_('Descrição'))
    justificativa_devolucao = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_('Justificativa da Devolução'))

    ano = models.PositiveSmallIntegerField(verbose_name=_('Ano'),
                                           default=None, blank=True, null=True,
                                           choices=RANGE_ANOS)

    numero_proposicao = models.PositiveIntegerField(
        blank=True, null=True, verbose_name=_('Número'))

    numero_materia_futuro = models.PositiveIntegerField(
        blank=True, null=True, verbose_name=_('Número Matéria'))

    hash_code = models.CharField(verbose_name=_('Código do Documento'),
                                 max_length=200,
                                 blank=True)

    """
    FIXME Campo não é necessário na modelagem e implementação atual para o
    módulo de proposições.
    E - Enviada é tratado pela condição do campo data_envio - se None n enviado
        se possui uma data, enviada
    R - Recebida é uma condição do campo data_recebimento - se None não receb.
        se possui uma data, enviada, recebida e incorporada
    I - A incorporação é automática ao ser recebida

    e ainda possui a condição de Devolvida onde o campo data_devolucao é
    direfente de None, fornecedo a informação para o usuário da data que o
    responsável devolveu bem como a justificativa da devolução.
    Essa informação fica disponível para o Autor até que ele envie novamente
    sua proposição ou resolva excluir.
    """
    # ind_enviado and ind_devolvido collapsed as char field (status)
    status = models.CharField(blank=True,
                              max_length=1,
                              choices=(('E', 'Enviada'),
                                       ('R', 'Recebida'),
                                       ('I', 'Incorporada')),
                              verbose_name=_('Status Proposição'))

    texto_original = PortalFileField(
        upload_to=materia_upload_path,
        blank=True,
        null=True,
        verbose_name=_('Texto Original'),
        storage=OverwriteStorage(),
        validators=[restringe_tipos_de_arquivo_txt],
        max_length=512)

    texto_articulado = GenericRelation(
        TextoArticulado, related_query_name='texto_articulado')

    materia_de_vinculo = models.ForeignKey(
        MateriaLegislativa, blank=True, null=True,
        on_delete=models.CASCADE,
        verbose_name=_('Matéria anexadora'),
        related_name=_('proposicao_set'))

    proposicao_vinculada = models.ForeignKey(
        'self', blank=True, null=True,
        on_delete=models.CASCADE,
        verbose_name=_('Proposição Vinculada'),
        related_name=_('proposicao_vinculada_set'))

    content_type = models.ForeignKey(
        ContentType, default=None, blank=True, null=True,
        verbose_name=_('Tipo de Material Gerado'),
        on_delete=PROTECT)
    object_id = models.PositiveIntegerField(
        blank=True, null=True, default=None)
    conteudo_gerado_related = SaplGenericForeignKey(
        'content_type', 'object_id', verbose_name=_('Conteúdo Gerado'))

    observacao = models.TextField(
        blank=True, verbose_name=_('Observação'))
    cancelado = models.BooleanField(verbose_name=_('Cancelada ?'),
                                    choices=YES_NO_CHOICES,
                                    default=False)

    """# Ao ser recebida, irá gerar uma nova matéria ou um documento acessorio
    # de uma já existente
    materia_gerada = models.ForeignKey(
        MateriaLegislativa, blank=True, null=True,
        related_name=_('materia_gerada'))
    documento_gerado = models.ForeignKey(
        DocumentoAcessorio, blank=True, null=True)"""

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
    ultima_edicao = models.DateTimeField(
        verbose_name=_('Data e Hora da Edição'),
        blank=True, null=True
    )

    @property
    def perfis(self):
        return self.tipo.perfis.all()

    @property
    def title_type(self):
        return '%s nº _____ %s' % (
            self.tipo, formats.date_format(
                self.data_envio if self.data_envio else timezone.now(),
                r"\d\e d \d\e F \d\e Y"))

    class Meta:
        ordering = ['-data_recebimento']
        verbose_name = _('Proposição')
        verbose_name_plural = _('Proposições')
        unique_together = (('content_type', 'object_id'),)
        permissions = (
            ('detail_proposicao_enviada',
             _('Pode acessar detalhes de uma proposição enviada.')),
            ('detail_proposicao_devolvida',
             _('Pode acessar detalhes de uma proposição devolvida.')),
            ('detail_proposicao_incorporada',
             _('Pode acessar detalhes de uma proposição incorporada.')),
        )

    def __str__(self):
        if self.ano and self.numero_proposicao:
            return '%s %s/%s' % (Proposicao._meta.verbose_name,
                                 self.numero_proposicao,
                                 self.ano)
        else:
            if len(self.descricao) < 30:
                descricao = self.descricao[:28] + ' ...'
            else:
                descricao = self.descricao

            return '%s %s/%s' % (Proposicao._meta.verbose_name,
                                 self.id,
                                 descricao)

    @property
    def epigrafe(self):
        return _('%(tipo)s nº %(numero)s de %(data)s') % {
            'tipo': self.tipo,
            'numero': self.numero_proposicao,
            'data': defaultfilters.date(
                self.data_envio if self.data_envio else timezone.now(),
                r"d \d\e F \d\e Y"
            )}

    def delete(self, using=None, keep_parents=False):
        if self.texto_original:
            self.texto_original.delete()

        return models.Model.delete(
            self, using=using, keep_parents=keep_parents)

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):

        if not self.pk and self.texto_original:
            texto_original = self.texto_original
            self.texto_original = None
            models.Model.save(self, force_insert=force_insert,
                              force_update=force_update,
                              using=using,
                              update_fields=update_fields)
            self.texto_original = texto_original

        return models.Model.save(self, force_insert=force_insert,
                                 force_update=force_update,
                                 using=using,
                                 update_fields=update_fields)


class StatusTramitacao(models.Model):
    INDICADOR_CHOICES = Choices(('F', 'fim', _('Fim')),
                                ('R', 'retorno', _('Retorno')))

    sigla = models.CharField(max_length=10, verbose_name=_('Sigla'))
    descricao = models.CharField(max_length=60, verbose_name=_('Descrição'))
    indicador = models.CharField(
        blank=True,
        max_length=1, verbose_name=_('Indicador da Tramitação'),
        choices=INDICADOR_CHOICES)

    class Meta:
        verbose_name = _('Status de Tramitação')
        verbose_name_plural = _('Status de Tramitação')
        ordering = ['descricao']

    def __str__(self):
        return _('%(descricao)s') % {
            'descricao': self.descricao}


class UnidadeTramitacaoManager(models.Manager):
    """
        Esta classe permite ordenar alfabeticamente a unidade de tramitacao
        através da concatenação de 3 fields
    """

    def get_queryset(self):
        return super(UnidadeTramitacaoManager, self).get_queryset().annotate(
            nome_composto=Concat('orgao__nome',
                                 'comissao__sigla',
                                 'parlamentar__nome_parlamentar')
        ).order_by('nome_composto')


class UnidadeTramitacao(models.Model):
    comissao = models.ForeignKey(
        Comissao, blank=True, null=True,
        on_delete=models.PROTECT, verbose_name=_('Comissão'))
    orgao = models.ForeignKey(
        Orgao, blank=True, null=True,
        on_delete=models.PROTECT, verbose_name=_('Órgão'))
    parlamentar = models.ForeignKey(
        Parlamentar, blank=True, null=True,
        on_delete=models.PROTECT, verbose_name=_('Parlamentar'))

    objects = UnidadeTramitacaoManager()

    ativo = models.BooleanField(verbose_name=_('Ativo ?'),
                                  choices=YES_NO_CHOICES,
                                  default=True)

    class Meta:
        verbose_name = _('Unidade de Tramitação')
        verbose_name_plural = _('Unidades de Tramitação')
        ordering = ['id']

    def __str__(self):
        if self.orgao and self.comissao and self.parlamentar:
            return _('%(comissao)s - %(orgao)s - %(parlamentar)s') % {
                'comissao': self.comissao, 'orgao': self.orgao,
                'parlamentar': self.parlamentar
            }
        elif self.orgao and self.comissao and not self.parlamentar:
            return _('%(comissao)s - %(orgao)s') % {
                'comissao': self.comissao, 'orgao': self.orgao
            }
        elif self.orgao and not self.comissao and self.parlamentar:
            return _('%(orgao)s - %(parlamentar)s') % {
                'orgao': self.orgao, 'parlamentar': self.parlamentar
            }
        elif not self.orgao and self.comissao and self.parlamentar:
            return _('%(comissao)s - %(parlamentar)s') % {
                'comissao': self.comissao, 'parlamentar': self.parlamentar
            }
        elif not self.orgao and self.comissao and not self.parlamentar:
            return _('%(comissao)s') % {'comissao': self.comissao}
        elif self.orgao and not self.comissao and not self.parlamentar:
            return _('%(orgao)s') % {'orgao': self.orgao}
        else:
            return _('%(parlamentar)s') % {'parlamentar': self.parlamentar}


class Tramitacao(models.Model):
    TURNO_CHOICES = Choices(
        ('P', 'primeiro', _('Primeiro')),
        ('S', 'segundo', _('Segundo')),
        ('U', 'unico', _('Único')),
    )

    status = models.ForeignKey(StatusTramitacao, on_delete=models.PROTECT,
                               null=True,
                               verbose_name=_('Status'))
    materia = models.ForeignKey(MateriaLegislativa, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(default=timezone.now)
    data_tramitacao = models.DateField(verbose_name=_('Data Tramitação'))
    unidade_tramitacao_local = models.ForeignKey(
        UnidadeTramitacao,
        related_name='tramitacoes_origem',
        on_delete=models.PROTECT,
        verbose_name=_('Unidade Local'))
    data_encaminhamento = models.DateField(
        blank=True, null=True, verbose_name=_('Data Encaminhamento'))
    unidade_tramitacao_destino = models.ForeignKey(
        UnidadeTramitacao,
        null=True,
        related_name='tramitacoes_destino',
        on_delete=models.PROTECT,
        verbose_name=_('Unidade Destino'))
    urgente = models.BooleanField(verbose_name=_('Urgente ?'),
                                  choices=YES_NO_CHOICES,
                                  default=False)
    turno = models.CharField(
        max_length=1, blank=True, verbose_name=_('Turno'),
        choices=TURNO_CHOICES)
    texto = models.TextField(verbose_name=_('Texto da Ação'))
    data_fim_prazo = models.DateField(
        blank=True, null=True, verbose_name=_('Data Fim Prazo'))
    user = models.ForeignKey(
        get_settings_auth_user_model(),
        verbose_name=_('Usuário'),
        on_delete=models.PROTECT,
        null=True,
        blank=True
    )
    ip = models.CharField(verbose_name=_('IP'),
                          max_length=30,
                          blank=True,
                          default='')

    class Meta:
        verbose_name = _('Tramitação')
        verbose_name_plural = _('Tramitações')
        ordering = ('-data_tramitacao', '-id',)

    def __str__(self):
        return _('%(materia)s | %(status)s | %(data)s') % {
            'materia': self.materia,
            'status': self.status,
            'data': self.data_tramitacao.strftime("%d/%m/%Y")}


class MateriaEmTramitacao(models.Model):
    materia = models.ForeignKey(
        MateriaLegislativa, on_delete=models.DO_NOTHING)
    tramitacao = models.ForeignKey(Tramitacao, on_delete=models.DO_NOTHING)

    unidade_tramitacao_atual = models.ForeignKey(
        UnidadeTramitacao,
        null=True,
        related_name='materiasemtramitacao_set',
        on_delete=models.PROTECT,
        verbose_name=_('Unidade Atual'))

    class Meta:
        managed = False
        db_table = "materia_materiaemtramitacao"
        ordering = ('-id',)

    def __str__(self):
        return '{}/{}'.format(self.materia, self.tramitacao)

class AnaliseSimilaridade(models.Model):
    materia_1 = models.ForeignKey(
        MateriaLegislativa, related_name='materia_1_set',
        on_delete=models.CASCADE,
        verbose_name=_('Matéria 1'))
    materia_2 = models.ForeignKey(
        MateriaLegislativa, related_name='materia_2_set',
        on_delete=models.CASCADE,
        verbose_name=_('Matéria 2'))

    analise = models.TextField(
        blank=True, null=True, verbose_name=_('Análise de Similaridade'))
    data_analise = models.DateTimeField(
        blank=True, null=True, verbose_name=_('Data da Análise'))
    ia_name = models.CharField(
        max_length=50, blank=True, null=True,
        verbose_name=_('Nome do Algoritmo de IA'))

    qtd_assuntos_comuns = models.SmallIntegerField(
        verbose_name=_("Qtd de Assuntos Comuns"), default=-0)

    similaridade = models.SmallIntegerField(
        verbose_name=_("Similaridade"), default=-1)

    class Meta:
        verbose_name = _('Análise de Similaridade')
        verbose_name_plural = _('Análises de Similaridade')
        ordering = ['-data_analise', '-qtd_assuntos_comuns']

    def __str__(self):
        return _('Matéria 1: %(materia_1)s'
                 ' - Matéria 2: %(materia_2)s'
                 ' - Similaridade: %(similaridade)s') % {
            'materia_1': self.materia_1,
            'materia_2': self.materia_2,
            'similaridade': self.similaridade
        }

