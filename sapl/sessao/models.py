from operator import xor

from django.contrib.contenttypes.fields import GenericRelation
from django.core.exceptions import ValidationError
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from django.db.models import Q, F
from django.db.models.fields.json import JSONField
from django.db.models.fields.related import ManyToManyField
from django.utils import timezone, formats
from django.utils.translation import gettext_lazy as _
from model_utils import Choices

from cmj.core.models import CertidaoPublicacao
from cmj.diarios.models import DiarioOficial, VinculoDocDiarioOficial
from cmj.mixins import CmjChoices
from cmj.videos.models import VideoParte
from sapl.base.models import Autor
from sapl.materia.models import MateriaLegislativa, Tramitacao
from sapl.parlamentares.models import (CargoMesa, Legislatura, Parlamentar,
                                       Partido, SessaoLegislativa)
from sapl.utils import (YES_NO_CHOICES, SaplGenericRelation,
                        get_settings_auth_user_model,
                        restringe_tipos_de_arquivo_txt, texto_upload_path,
                        OverwriteStorage, PortalFileField)


class TipoSessaoPlenaria(models.Model):

    TIPO_NUMERACAO_CHOICES = Choices(
        (1, 'quizenal', 'Quinzenal'),
        (2, 'mensal', 'Mensal'),
        (10, 'anual', 'Anual'),
        (11, 'sessao_legislativa', 'Sessão Legislativa'),
        (12, 'legislatura', 'Legislatura'),
        (99, 'unica', 'Numeração Única'),
    )

    TIPOGERAL_SESSAO = 10
    TIPOGERAL_REUNIAO = 20
    TIPOGERAL_AUDIENCIA = 30
    TIPOGERAL_JOVEM = 40

    TIPOGERAL_CHOICES = CmjChoices(
        (TIPOGERAL_SESSAO, 'sessao', 'Sessão'),
        (TIPOGERAL_REUNIAO, 'reuniao', 'Reunião'),
        (TIPOGERAL_AUDIENCIA, 'audiencia', 'Audiência'),
        (TIPOGERAL_JOVEM, 'jovem', 'Jovem Vereador'),
    )

    nome = models.CharField(max_length=30, verbose_name=_('Descrição do Tipo'))
    quorum_minimo = models.PositiveIntegerField(
        verbose_name=_('Quórum mínimo'))

    tipo_numeracao = models.PositiveIntegerField(
        verbose_name=_('Tipo de Numeração'),
        choices=TIPO_NUMERACAO_CHOICES, default=11)

    tipogeral = models.PositiveIntegerField(
        verbose_name=_('Tipo Geral'),
        choices=TIPOGERAL_CHOICES,
        default=10
    )

    gera_selo_votacao = models.BooleanField(blank=True, default=True,
                                            verbose_name=_('Gera Selo de Votação?'))

    class Meta:
        verbose_name = _('Tipo de Sessão Plenária')
        verbose_name_plural = _('Tipos de Sessão Plenária')
        ordering = ['nome']

    def __str__(self):
        return self.nome

    def queryset_tipo_numeracao(self, legislatura, sessao_legislativa, data):

        qs = Q(tipo=self)
        tnc = self.TIPO_NUMERACAO_CHOICES

        if self.tipo_numeracao == tnc.unica:
            pass
        elif self.tipo_numeracao == tnc.legislatura:
            qs &= Q(legislatura=legislatura)
        elif self.tipo_numeracao == tnc.sessao_legislativa:
            qs &= Q(sessao_legislativa=sessao_legislativa)
        elif self.tipo_numeracao == tnc.anual:
            qs &= Q(data_inicio__year=data.year)
        elif self.tipo_numeracao in (tnc.mensal, tnc.quizenal):
            qs &= Q(data_inicio__year=data.year, data_inicio__month=data.month)

            if self.tipo_numeracao == tnc.quizenal:
                if data.year == 2023 and data.month == 2:
                    if data.day <= 14:
                        qs &= Q(data_inicio__day__lte=14)
                    else:
                        qs &= Q(data_inicio__day__gt=14)
                else:
                    if data.day <= 15:
                        qs &= Q(data_inicio__day__lte=15)
                    else:
                        qs &= Q(data_inicio__day__gt=15)
        return qs


def get_sessao_media_path(instance, subpath, filename):
    return './sapl/sessao/%s/%s/%s' % (instance.numero, subpath, filename)


def pauta_upload_path(instance, filename):
    return texto_upload_path(
        instance, filename, subpath='pauta', pk_first=True)
    # return get_sessao_media_path(instance, 'pauta', filename)


def ata_upload_path(instance, filename):
    return texto_upload_path(instance, filename, subpath='ata', pk_first=True)
    # return get_sessao_media_path(instance, 'ata', filename)


def anexo_upload_path(instance, filename):
    return texto_upload_path(
        instance, filename, subpath='anexo', pk_first=True)
    # return get_sessao_media_path(instance, 'anexo', filename)


class SessaoPlenaria(models.Model):
    FIELDFILE_NAME = ('upload_pauta', 'upload_ata', 'upload_anexo')

    metadata = JSONField(
        verbose_name=_('Metadados'),
        blank=True, null=True, default=None, encoder=DjangoJSONEncoder)

    cod_andamento_sessao = models.PositiveIntegerField(blank=True, null=True)

    painel_aberto = models.BooleanField(blank=True, default=False,
                                        verbose_name=_('Painel está aberto?'))

    titulo = models.CharField(
        max_length=256,
        verbose_name=_('Título'),
        blank=True, default=''
    )

    tipo = models.ForeignKey(TipoSessaoPlenaria,
                             on_delete=models.PROTECT,
                             verbose_name=_('Tipo'))
    sessao_legislativa = models.ForeignKey(
        SessaoLegislativa,
        on_delete=models.CASCADE,
        verbose_name=_('Sessão Legislativa'))
    legislatura = models.ForeignKey(Legislatura,
                                    on_delete=models.PROTECT,
                                    verbose_name=_('Legislatura'))
    # XXX seems to be empty
    data_inicio = models.DateField(verbose_name=_('Abertura'))
    hora_inicio = models.CharField(
        max_length=5, verbose_name=_('Horário (hh:mm)'))
    hora_fim = models.CharField(
        max_length=5, blank=True, verbose_name=_('Horário (hh:mm)'))
    numero = models.PositiveIntegerField(verbose_name=_('Número'))
    data_fim = models.DateField(
        blank=True, null=True, verbose_name=_('Encerramento'))
    url_audio = models.URLField(
        max_length=150, blank=True,
        verbose_name=_('URL Arquivo Áudio (Formatos MP3 / AAC)'))
    url_video = models.URLField(
        max_length=150, blank=True,
        verbose_name=_('URL Arquivo Vídeo (Formatos MP4 / FLV / WebM)'))
    upload_pauta = PortalFileField(
        blank=True,
        null=True,
        upload_to=pauta_upload_path,
        verbose_name=_('Pauta da Sessão'),
        storage=OverwriteStorage(),
        validators=[restringe_tipos_de_arquivo_txt])
    upload_ata = PortalFileField(
        blank=True,
        null=True,
        upload_to=ata_upload_path,
        storage=OverwriteStorage(),
        verbose_name=_('Ata da Sessão'),
        validators=[restringe_tipos_de_arquivo_txt])
    upload_anexo = PortalFileField(
        blank=True,
        null=True,
        storage=OverwriteStorage(),
        upload_to=anexo_upload_path,
        verbose_name=_('Anexo da Sessão'))
    iniciada = models.BooleanField(null=True, blank=True,
                                   choices=YES_NO_CHOICES,
                                   verbose_name=_('Sessão iniciada?'),
                                   default=True)
    finalizada = models.BooleanField(null=True, blank=True,
                                     choices=YES_NO_CHOICES,
                                     verbose_name=_('Sessão finalizada?'),
                                     default=False)
    selo_votacao_adicionado = models.BooleanField(null=True, blank=True,
                                                  choices=YES_NO_CHOICES,
                                                  verbose_name=_(
                                                      'Selo de Votação Adicionado?'),
                                                  default=False)
    interativa = models.BooleanField(null=True, blank=True,
                                     choices=YES_NO_CHOICES,
                                     verbose_name=_('Sessão interativa'))
    tema_solene = models.TextField(
        blank=True, max_length=500, verbose_name=_('Tema da Sessão Solene'))

    data_ultima_atualizacao = models.DateTimeField(
        blank=True, null=True,
        auto_now=True,
        verbose_name=_('Data'))

    _certidao = GenericRelation(
        CertidaoPublicacao, related_query_name='sessaoplenaria_cert')

    _diario = GenericRelation(
        VinculoDocDiarioOficial, related_query_name='sessaoplenaria_diario')

    _videoparte = SaplGenericRelation(
        VideoParte,
        related_query_name='sessaoplenaria_videoparte',
        fields_search=(
            ('video__titulo', '__icontains'),
        )
    )

    class Meta:
        verbose_name = _('Sessão Plenária')
        verbose_name_plural = _('Sessões Plenárias')
        ordering = ['id']

    @property
    def __descr__(self):
        o = self
        return f"""
            Abertura: {o.data_inicio.strftime("%d/%m/%Y")} às {o.hora_inicio}<br>
            Encerramento: {o.data_fim.strftime("%d/%m/%Y")} às {o.hora_fim}<br>

        """

    @property
    def videoparte(self):
        return self._videoparte.all().first()

    @property
    def certidao(self):
        return self._certidao.order_by('-id').first()

    @property
    def epigrafe(self):
        return self.str_short()

    @property
    def render_description(self):
        return self.str_subtitle

    @property
    def diariooficial(self):
        try:
            return self._diario.all().first().diario
        except:
            return None

    def __str__(self):

        if self.titulo:
            return self.titulo

        tnc = self.tipo.TIPO_NUMERACAO_CHOICES

        base = '{}ª {}'.format(self.numero, self.tipo.nome)

        if self.tipo.tipo_numeracao == tnc.quizenal:
            if self.data_inicio.year == 2023 and self.data_inicio.month == 2:
                base += ' da {}ª Quinzena'.format(
                    1 if self.data_inicio.day <= 14 else 2)
            else:
                base += ' da {}ª Quinzena'.format(
                    1 if self.data_inicio.day <= 15 else 2)

        if self.tipo.tipo_numeracao <= tnc.mensal:
            base += ' do mês de {}'.format(
                formats.date_format(self.data_inicio, 'F')
            )

        if self.tipo.tipo_numeracao <= tnc.anual:
            base += ' de {}'.format(self.data_inicio.year)

        if self.tipo.tipo_numeracao <= tnc.sessao_legislativa:
            base += ' da {}ª Sessão Legislativa'.format(
                self.sessao_legislativa.numero)

        if self.tipo.tipo_numeracao <= tnc.legislatura:
            base += ' da {}ª Legislatura'.format(
                self.legislatura.numero)

        return base

        """return _('%(numero)sª Sessão %(tipo_nome)s'
                 ' da %(sessao_legislativa_numero)sª Sessão Legislativa'
                 ' da %(legislatura_id)sª Legislatura') % {

            'numero': self.numero,
            'tipo_nome': self.tipo.nome,
            'sessao_legislativa_numero': self.sessao_legislativa.numero,
            # XXX check if it shouldn't be legislatura.numero
            'legislatura_id': self.legislatura.numero}
        """

    def str_short(self):

        tnc = self.tipo.TIPO_NUMERACAO_CHOICES

        base = '{}ª {}'.format(self.numero, self.tipo.nome)

        if self.tipo.tipo_numeracao == tnc.quizenal:
            base += ' da {}ª Quinzena'.format(
                1 if self.data_inicio.day <= 15 else 2)

        if self.tipo.tipo_numeracao <= tnc.mensal:
            base += ' do mês de {}'.format(
                formats.date_format(self.data_inicio, 'F')
            )

        if self.tipo.tipo_numeracao <= tnc.anual:
            base += ' de {}'.format(self.data_inicio.year)

        return base

    def str_title(self):
        return self.str_short()

    def str_subtitle(self):

        tnc = self.tipo.TIPO_NUMERACAO_CHOICES

        base = ''
        if self.tipo.tipo_numeracao <= tnc.sessao_legislativa:
            base = '{}ª Sessão Legislativa'.format(
                self.sessao_legislativa.numero)

        if self.tipo.tipo_numeracao <= tnc.legislatura:
            base += ' da {}ª Legislatura'.format(
                self.legislatura.numero)

        return base

    def delete(self, using=None, keep_parents=False):
        if self.upload_pauta:
            self.upload_pauta.delete()

        if self.upload_ata:
            self.upload_ata.delete()

        if self.upload_anexo:
            self.upload_anexo.delete()

        return models.Model.delete(
            self, using=using, keep_parents=keep_parents)

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        yt = 'https://www.youtube.com/live'

        if self.url_video.startswith(yt):
            self.url_video = self.url_video.replace(yt, 'https://youtu.be')

        if not self.pk and (self.upload_pauta or self.upload_ata or
                            self.upload_anexo):
            upload_pauta = self.upload_pauta
            upload_ata = self.upload_ata
            upload_anexo = self.upload_anexo
            self.upload_pauta = None
            self.upload_ata = None
            self.upload_anexo = None
            models.Model.save(self, force_insert=force_insert,
                              force_update=force_update,
                              using=using,
                              update_fields=update_fields)

            self.upload_pauta = upload_pauta
            self.upload_ata = upload_ata
            self.upload_anexo = upload_anexo

        models.Model.save(self, force_insert=force_insert,
                          force_update=force_update,
                          using=using,
                          update_fields=update_fields)

        self.ordemdia_set.exclude(
            data_ordem=F('sessao_plenaria__data_inicio')
        ).update(data_ordem=self.data_inicio)

        self.expedientemateria_set.exclude(
            data_ordem=F('sessao_plenaria__data_inicio')
        ).update(data_ordem=self.data_inicio)

    @property
    def ano(self):
        return self.data_inicio.year


class AbstractOrdemDia(models.Model):
    TIPO_VOTACAO_CHOICES = Choices(
        (1, 'simbolica', 'Simbólica'),
        (2, 'nominal', 'Nominal'),
        (3, 'secreta', 'Secreta'),
        (4, 'leitura', 'Leitura'),
    )

    sessao_plenaria = models.ForeignKey(
        SessaoPlenaria,
        on_delete=models.CASCADE)
    materia = models.ForeignKey(
        MateriaLegislativa,
        on_delete=models.PROTECT,
        verbose_name=_('Matéria'))
    tramitacao = models.ForeignKey(
        Tramitacao,
        on_delete=models.PROTECT,
        verbose_name=_('Situação quando pautada'),
        blank=True,
        default='',
        null=True)
    data_ordem = models.DateField(verbose_name=_('Data da Sessão'))
    observacao = models.TextField(
        blank=True, verbose_name=_('Observação'))
    numero_ordem = models.PositiveIntegerField(verbose_name=_('Nº Ordem'))
    resultado = models.TextField(blank=True, verbose_name=_('Resultado'))
    tipo_votacao = models.PositiveIntegerField(
        verbose_name=_('Tipo de votação'), choices=TIPO_VOTACAO_CHOICES, default=1)
    votacao_aberta = models.BooleanField(null=True,
                                         blank=True,
                                         choices=YES_NO_CHOICES,
                                         verbose_name=_('Votação iniciada?'))

    votacao_aberta_pedido_prazo = models.BooleanField(null=True,
                                                      blank=True,
                                                      choices=YES_NO_CHOICES,
                                                      verbose_name=_('Votação de Pedido de Prazo?'))
    registro_aberto = models.BooleanField(null=True,
                                          blank=True,
                                          choices=YES_NO_CHOICES,
                                          verbose_name=_('Registro de Votação Iniciado?'))

    url_video = models.URLField(
        max_length=150, blank=True,
        verbose_name=_('URL Arquivo Vídeo (Formatos MP4 / FLV / WebM)'))

    class Meta:
        abstract = True
        ordering = ('-sessao_plenaria', 'numero_ordem',)

    @property
    def ementa(self):
        return self.materia.ementa

    def __str__(self):
        return 'Ordem do Dia/Expediente: %s - %s em %s' % (
            self.numero_ordem, self.materia, self.sessao_plenaria)


class ExpedienteMateria(AbstractOrdemDia):
    parent = models.ForeignKey('self',
                               blank=True, null=True, default=None,
                               on_delete=models.CASCADE,
                               verbose_name=_('Expendiente Principal'))

    class Meta(AbstractOrdemDia.Meta):
        verbose_name = _('Matéria do Expediente')
        verbose_name_plural = _('Matérias do Expediente')


class TipoExpediente(models.Model):
    nome = models.CharField(max_length=100, verbose_name=_('Tipo'))
    ordenacao = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name=_("Ordenação"))

    class Meta:
        verbose_name = _('Tipo de Expediente')
        verbose_name_plural = _('Tipos de Expediente')
        ordering = ['ordenacao']

    def __str__(self):
        return self.nome


class ExpedienteSessao(models.Model):  # ExpedienteSessaoPlenaria
    sessao_plenaria = models.ForeignKey(
        SessaoPlenaria,
        on_delete=models.CASCADE,
        related_name='expedientesessao_set'
    )
    tipo = models.ForeignKey(TipoExpediente, on_delete=models.PROTECT)
    conteudo = models.TextField(
        blank=True, verbose_name=_('Conteúdo do expediente'))

    class Meta:
        verbose_name = _('Expediente de Sessão Plenaria')
        verbose_name_plural = _('Expedientes de Sessão Plenaria')
        ordering = ['id']

    def __str__(self):
        return '%s - %s' % (self.tipo, self.sessao_plenaria)


class OcorrenciaSessao(models.Model):  # OcorrenciaSessaoPlenaria
    sessao_plenaria = models.OneToOneField(SessaoPlenaria,
                                           on_delete=models.PROTECT)
    conteudo = models.TextField(
        blank=True, verbose_name=_('Ocorrências da Sessão Plenária'))

    class Meta:
        verbose_name = _('Ocorrência da Sessão Plenaria')
        verbose_name_plural = _('Ocorrências da Sessão Plenaria')
        ordering = ['id']

    def __str__(self):
        return '%s - %s' % (self.sessao_plenaria, self.conteudo)


class IntegranteMesa(models.Model):  # MesaSessaoPlenaria
    sessao_plenaria = models.ForeignKey(
        SessaoPlenaria,
        related_name='integrantemesa',
        on_delete=models.CASCADE
    )
    cargo = models.ForeignKey(CargoMesa, on_delete=models.PROTECT)
    parlamentar = models.ForeignKey(Parlamentar, on_delete=models.PROTECT)

    class Meta:
        verbose_name = _('Participação em Mesa de Sessão Plenaria')
        verbose_name_plural = _('Participações em Mesas de Sessão Plenaria')
        ordering = ['id']

    def __str__(self):
        return '%s - %s' % (self.cargo, self.parlamentar)


class AbstractOrador(models.Model):  # Oradores

    FIELDFILE_NAME = ('upload_anexo',)

    metadata = JSONField(
        verbose_name=_('Metadados'),
        blank=True, null=True, default=None, encoder=DjangoJSONEncoder)

    sessao_plenaria = models.ForeignKey(SessaoPlenaria,
                                        on_delete=models.CASCADE)
    parlamentar = models.ForeignKey(Parlamentar,
                                    on_delete=models.PROTECT,
                                    verbose_name=_('Parlamentar'))
    numero_ordem = models.PositiveIntegerField(
        verbose_name=_('Ordem de pronunciamento'))
    url_discurso = models.URLField(
        max_length=150, blank=True, verbose_name=_('URL Vídeo'))
    observacao = models.CharField(
        max_length=150, blank=True, verbose_name=_('Observação'))
    upload_anexo = models.FileField(
        blank=True,
        null=True,
        storage=OverwriteStorage(),
        upload_to=anexo_upload_path,
        verbose_name=_('Anexo do Orador'))

    class Meta:
        abstract = True

    def __str__(self):
        return _('%(nome)s (%(numero)sº orador)') % {
            'nome': self.parlamentar,
            'numero': self.numero_ordem}


class Orador(AbstractOrador):  # Oradores

    class Meta:
        verbose_name = _('Orador das Explicações Pessoais')
        verbose_name_plural = _('Oradores das Explicações Pessoais')
        ordering = ['id']


class OradorExpediente(AbstractOrador):  # OradoresExpediente

    class Meta:
        verbose_name = _('Orador do Expediente')
        verbose_name_plural = _('Oradores do Expediente')
        ordering = ['id']


class OradorOrdemDia(AbstractOrador):  # OradoresOrdemDia

    class Meta:
        verbose_name = _('Orador da Ordem do Dia')
        verbose_name_plural = _('Oradores da Ordem do Dia')
        ordering = ['id']


class OrdemDiaManager(models.Manager):
    def order_by_numero_ordem(self):
        return self.get_queryset().order_by('numero_ordem')


class OrdemDia(AbstractOrdemDia):

    objects = OrdemDiaManager()

    parent = models.ForeignKey('self',
                               blank=True, null=True, default=None,
                               on_delete=models.CASCADE,
                               related_name='childs',
                               verbose_name=_('Ordem Dia Principal'))

    class Meta(AbstractOrdemDia.Meta):
        verbose_name = _('Matéria da Ordem do Dia')
        verbose_name_plural = _('Matérias da Ordem do Dia')
        ordering = ['id']


class PresencaOrdemDia(models.Model):  # OrdemDiaPresenca
    sessao_plenaria = models.ForeignKey(SessaoPlenaria,
                                        on_delete=models.CASCADE)
    parlamentar = models.ForeignKey(Parlamentar, on_delete=models.PROTECT)

    class Meta:
        verbose_name = _('Presença da Ordem do Dia')
        verbose_name_plural = _('Presenças da Ordem do Dia')
        ordering = ['parlamentar__nome_parlamentar']

    def __str__(self):
        # FIXME ambigous
        return _('Sessão: %(sessao)s Parlamentar: %(parlamentar)s') % {
            'sessao': self.sessao_plenaria,
            'parlamentar': self.parlamentar}


class TipoResultadoVotacao(models.Model):
    NATUREZA_CHOICES = Choices(
        ('A', 'aprovado', 'Aprovado'),
        ('R', 'rejeitado', 'Rejeitado'),
        ('P', 'prazo', 'Pedidos de Prazo'))
    nome = models.CharField(max_length=100, verbose_name=_('Nome do Tipo'))
    natureza = models.CharField(max_length=1,
                                blank=True,
                                choices=NATUREZA_CHOICES,
                                verbose_name=_('Natureza do Tipo'))

    class Meta:
        verbose_name = _('Tipo de Resultado de Votação')
        verbose_name_plural = _('Tipos de Resultado de Votação')
        ordering = ['id']

    def __str__(self):
        return self.nome


class RegistroVotacao(models.Model):

    tipo_resultado_votacao = models.ForeignKey(
        TipoResultadoVotacao,
        on_delete=models.PROTECT,
        verbose_name=_('Resultado da Votação'))
    materia = models.ForeignKey(MateriaLegislativa, on_delete=models.CASCADE)
    ordem = models.ForeignKey(OrdemDia,
                              blank=True,
                              null=True,
                              related_name="registrovotacao_set",
                              on_delete=models.CASCADE)
    expediente = models.ForeignKey(ExpedienteMateria,
                                   blank=True,
                                   null=True,
                                   on_delete=models.CASCADE)
    numero_votos_sim = models.PositiveIntegerField(verbose_name=_('Sim'))
    numero_votos_nao = models.PositiveIntegerField(verbose_name=_('Não'))
    numero_abstencoes = models.PositiveIntegerField(
        verbose_name=_('Abstenções'))
    observacao = models.TextField(
        blank=True, verbose_name=_('Observações'))

    subscricoes = ManyToManyField(Parlamentar,
                                  related_name='subscricoes')

    user = models.ForeignKey(get_settings_auth_user_model(),
                             on_delete=models.PROTECT,
                             null=True,
                             blank=True)
    ip = models.CharField(verbose_name=_('IP'),
                          max_length=30,
                          blank=True,
                          default='')
    data_hora = models.DateTimeField(
        verbose_name=_('Data/Hora'),
        auto_now_add=True,
        blank=True,
        null=True)

    selo_votacao = models.BooleanField(null=True,
                                       blank=True,
                                       default=False,
                                       choices=YES_NO_CHOICES,
                                       verbose_name=_('Selo de Votação Adicionado'))

    class Meta:
        verbose_name = _('Votação')
        verbose_name_plural = _('Votações')
        ordering = ('data_hora', 'id',)

    def __str__(self):
        return _('Ordem: %(ordem)s - Votação: %(votacao)s - '
                 'Matéria: %(materia)s') % {
                     'ordem': self.ordem,
                     'votacao': self.tipo_resultado_votacao,
            'materia': self.materia}

    @property
    def item_sessao(self):
        return self.ordem or self.expediente

    def clean(self):
        """Exatamente um dos campos ordem ou expediente deve estar preenchido.
        """
        # TODO remover esse método quando OrdemDia e ExpedienteMateria
        # forem reestruturados e os campos ordem e expediente forem unificados
        if not xor(bool(self.ordem), bool(self.expediente)):
            raise ValidationError(
                'RegistroVotacao deve ter exatamente um dos campos '
                'ordem ou expediente preenchido. Ambos estão preenchidos: '
                '{}, {}'. format(self.ordem, self.expediente))


class VotoParlamentar(models.Model):
    '''
    As colunas ordem e expediente são redundantes, levando em consideração
    que RegistroVotacao já possui ordem/expediente. Entretanto, para
    viabilizar a votação interativa, uma vez que ela é feita antes de haver
    um RegistroVotacao, é preciso identificar o voto por ordem/expediente.
    '''
    votacao = models.ForeignKey(RegistroVotacao,
                                blank=True,
                                null=True, on_delete=models.CASCADE)
    parlamentar = models.ForeignKey(Parlamentar, on_delete=models.PROTECT)
    voto = models.CharField(max_length=10)

    user = models.ForeignKey(get_settings_auth_user_model(),
                             on_delete=models.PROTECT,
                             null=True,
                             blank=True)
    ip = models.CharField(verbose_name=_('IP'),
                          max_length=30,
                          blank=True,
                          default='')
    data_hora = models.DateTimeField(
        verbose_name=_('Data/Hora'),
        auto_now_add=True,
        blank=True,
        null=True)

    ordem = models.ForeignKey(OrdemDia,
                              blank=True,
                              null=True, on_delete=models.CASCADE)
    expediente = models.ForeignKey(ExpedienteMateria,
                                   blank=True,
                                   null=True, on_delete=models.CASCADE)

    class Meta:
        verbose_name = _('Registro de Votação de Parlamentar')
        verbose_name_plural = _('Registros de Votações de Parlamentares')
        ordering = ['id']

    def __str__(self):
        return _('Votação: %(votacao)s - Parlamentar: %(parlamentar)s') % {
            'votacao': self.votacao, 'parlamentar': self.parlamentar}


class SessaoPlenariaPresenca(models.Model):
    sessao_plenaria = models.ForeignKey(SessaoPlenaria,
                                        on_delete=models.CASCADE)
    parlamentar = models.ForeignKey(Parlamentar, on_delete=models.PROTECT)
    data_sessao = models.DateField(blank=True, null=True)

    class Meta:
        verbose_name = _('Presença em Sessão Plenária')
        verbose_name_plural = _('Presenças em Sessões Plenárias')
        ordering = ['parlamentar__nome_parlamentar']


ORDENACAO_RESUMO = [
    ('id_basica', 'Identificação Básica'),
    ('cont_mult', 'Conteúdo Multimídia'),
    ('mesa_d', 'Mesa Diretora'),
    ('lista_p', 'Lista de Presença'),
    ('exp', 'Expedientes'),
    ('mat_exp', 'Matérias do Expediente'),
    ('v_n_mat_exp', 'Votações Nominais - Matérias do Expediente'),
    ('oradores_exped', 'Oradores do Expediente'),
    ('lista_p_o_d', 'Lista de Presença Ordem do Dia'),
    ('mat_o_d', 'Matérias da Ordem do Dia'),
    ('v_n_mat_o_d', 'Votações Nominais - Matérias da Ordem do Dia'),
    ('oradores_o_d', 'Oradores da Ordem do Dia'),
    ('oradores_expli', 'Oradores das Explicações Pessoais'),
    ('ocorr_sessao', 'Ocorrências da Sessão')
]


class ResumoOrdenacao(models.Model):
    '''
        Tabela para registrar em qual ordem serão renderizados os componentes
        da tela de resumo de uma sessão
    '''
    primeiro = models.CharField(
        max_length=50,
        default=ORDENACAO_RESUMO[0][0]
    )
    segundo = models.CharField(
        max_length=50,
        default=ORDENACAO_RESUMO[1][0]
    )
    terceiro = models.CharField(
        max_length=50,
        default=ORDENACAO_RESUMO[2][0]
    )
    quarto = models.CharField(
        max_length=50,
        default=ORDENACAO_RESUMO[3][0]
    )
    quinto = models.CharField(
        max_length=50,
        default=ORDENACAO_RESUMO[4][0]
    )
    sexto = models.CharField(
        max_length=50,
        default=ORDENACAO_RESUMO[5][0]
    )
    setimo = models.CharField(
        max_length=50,
        default=ORDENACAO_RESUMO[6][0]
    )
    oitavo = models.CharField(
        max_length=50,
        default=ORDENACAO_RESUMO[7][0]
    )
    nono = models.CharField(
        max_length=50,
        default=ORDENACAO_RESUMO[8][0]
    )
    decimo = models.CharField(
        max_length=50,
        default=ORDENACAO_RESUMO[9][0]
    )
    decimo_primeiro = models.CharField(
        max_length=50,
        default=ORDENACAO_RESUMO[10][0]
    )
    decimo_segundo = models.CharField(
        max_length=50,
        default=ORDENACAO_RESUMO[11][0]
    )
    decimo_terceiro = models.CharField(
        max_length=50,
        default=ORDENACAO_RESUMO[12][0]
    )
    decimo_quarto = models.CharField(
        max_length=50,
        default=ORDENACAO_RESUMO[13][0]
    )

    class Meta:
        verbose_name = _('Ordenação do Resumo de uma Sessão')
        verbose_name_plural = _('Ordenação do Resumo de uma Sessão')
        ordering = ['id']

    def __str__(self):
        return 'Ordenação do Resumo de uma Sessão'


class TipoRetiradaPauta(models.Model):
    descricao = models.CharField(max_length=150, verbose_name=_('Descrição'))

    class Meta:
        verbose_name = _('Tipo de Retirada de Pauta')
        verbose_name_plural = _('Tipos de Retirada de Pauta')
        ordering = ['descricao']

    def __str__(self):
        return self.descricao


class TipoJustificativa(models.Model):
    descricao = models.CharField(max_length=150, verbose_name=_('Descrição'))

    class Meta:
        verbose_name = _('Tipo de Justificativa')
        verbose_name_plural = _('Tipos de Justificativa')
        ordering = ['descricao']

    def __str__(self):
        return self.descricao


class JustificativaAusencia(models.Model):

    FIELDFILE_NAME = ('upload_anexo',)

    metadata = JSONField(
        verbose_name=_('Metadados'),
        blank=True, null=True, default=None, encoder=DjangoJSONEncoder)

    TIPO_AUSENCIA_CHOICES = Choices(
        (1, 'materia', 'Matéria'),
        (2, 'sessao', 'Sessão'),
    )
    parlamentar = models.ForeignKey(Parlamentar, on_delete=models.PROTECT,
                                    verbose_name=_('Parlamentar'))
    sessao_plenaria = models.ForeignKey(SessaoPlenaria,
                                        on_delete=models.CASCADE,
                                        verbose_name=_('Sessão Plenária'))
    tipo_ausencia = models.ForeignKey(TipoJustificativa, on_delete=models.PROTECT,
                                      verbose_name=_('Tipo de Justificativa'))
    data = models.DateField(verbose_name=_('Data'))
    hora = models.CharField(
        max_length=5, verbose_name=_('Horário (hh:mm)'))
    observacao = models.TextField(
        max_length=150, blank=True, verbose_name=_('Observação'))
    ausencia = models.PositiveIntegerField(
        verbose_name=_('Ausente em'), choices=TIPO_AUSENCIA_CHOICES, default=1)

    materias_do_expediente = models.ManyToManyField(
        ExpedienteMateria, blank=True, verbose_name=_('Matérias do Expediente'))

    materias_da_ordem_do_dia = models.ManyToManyField(
        OrdemDia, blank=True, verbose_name=_('Matérias do Ordem do Dia'))

    upload_anexo = models.FileField(
        blank=True,
        null=True,
        storage=OverwriteStorage(),
        upload_to=anexo_upload_path,
        verbose_name=_('Anexo de Justificativa'))

    class Meta:
        verbose_name = _('Justificativa de Ausência')
        verbose_name_plural = _('Justificativas de Ausências')
        ordering = ['id']

    def __str__(self):
        return 'Justificativa de Ausência'

    def delete(self, using=None, keep_parents=False):
        if self.upload_anexo:
            self.upload_anexo.delete()

        return models.Model.delete(
            self, using=using, keep_parents=keep_parents)

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):

        if not self.pk and self.upload_anexo:
            upload_anexo = self.upload_anexo
            self.upload_anexo = None
            models.Model.save(self, force_insert=force_insert,
                              force_update=force_update,
                              using=using,
                              update_fields=update_fields)

            self.upload_anexo = upload_anexo

        return models.Model.save(self, force_insert=force_insert,
                                 force_update=force_update,
                                 using=using,
                                 update_fields=update_fields)


class RetiradaPauta(models.Model):
    materia = models.ForeignKey(MateriaLegislativa,
                                on_delete=models.CASCADE,
                                verbose_name=_('Matéria'))
    sessao_plenaria = models.ForeignKey(SessaoPlenaria,
                                        on_delete=models.CASCADE,
                                        verbose_name=_('Sessão Plenária'),
                                        blank=True,
                                        null=True)
    ordem = models.ForeignKey(OrdemDia,
                              blank=True,
                              null=True,
                              on_delete=models.CASCADE)
    expediente = models.ForeignKey(ExpedienteMateria,
                                   blank=True,
                                   null=True,
                                   on_delete=models.CASCADE)
    data = models.DateField(verbose_name=_('Data'),
                            default=timezone.now)
    observacao = models.TextField(blank=True,
                                  verbose_name=_('Observações'))
    parlamentar = models.ForeignKey(Parlamentar,
                                    on_delete=models.PROTECT,
                                    verbose_name=_('Requerente'),
                                    blank=True,
                                    null=True)
    tipo_de_retirada = models.ForeignKey(TipoRetiradaPauta,
                                         on_delete=models.PROTECT,
                                         verbose_name=_('Motivo de Retirada de Pauta'))

    class Meta:
        verbose_name = _('Retirada de Pauta')
        verbose_name_plural = _('Retirada de Pauta')
        ordering = ['id']

    def __str__(self):
        return _('Ordem: %(ordem)s - Requerente: %(requerente)s - '
                 'Matéria: %(materia)s') % {
                     'ordem': self.ordem,
                     'requerente': self.parlamentar,
                     'materia': self.materia}

    def clean(self):
        """Exatamente um dos campos ordem ou expediente deve estar preenchido.
        """
        # TODO remover esse método quando OrdemDia e ExpedienteMateria
        # forem reestruturados e os campos ordem e expediente forem unificados
        if not xor(bool(self.ordem), bool(self.expediente)):
            raise ValidationError(
                'ReritadaPauta deve ter exatamente um dos campos '
                'ordem ou expediente preenchido. Ambos estão preenchidos: '
                '{}, {}'. format(self.ordem, self.expediente))


class RegistroLeitura(models.Model):
    materia = models.ForeignKey(MateriaLegislativa, on_delete=models.CASCADE)
    ordem = models.ForeignKey(OrdemDia,
                              blank=True,
                              null=True,
                              on_delete=models.CASCADE)
    expediente = models.ForeignKey(ExpedienteMateria,
                                   blank=True,
                                   null=True,
                                   on_delete=models.CASCADE)
    observacao = models.TextField(
        blank=True, verbose_name=_('Observações'))
    user = models.ForeignKey(get_settings_auth_user_model(),
                             on_delete=models.PROTECT,
                             null=True,
                             blank=True)
    ip = models.CharField(verbose_name=_('IP'),
                          max_length=60,
                          blank=True,
                          default='')
    data_hora = models.DateTimeField(
        verbose_name=_('Data/Hora'),
        auto_now=True,
        blank=True,
        null=True)

    class Meta:
        verbose_name = _('Leitura')
        verbose_name_plural = _('Leituras')
        ordering = ['id']

    def __str__(self):
        return _('Leitura - '
                 'Matéria: %(materia)s') % {
            'materia': self.materia}

    def clean(self):
        """Exatamente um dos campos ordem ou expediente deve estar preenchido.
        """
        # TODO remover esse método quando OrdemDia e ExpedienteMateria
        # forem reestruturados e os campos ordem e expediente forem unificados
        if not xor(bool(self.ordem), bool(self.expediente)):
            raise ValidationError(
                'RegistroLeitura deve ter exatamente um dos campos '
                'ordem ou expediente preenchido. Ambos estão preenchidos: '
                '{}, {}'. format(self.ordem, self.expediente))
