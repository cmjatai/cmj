from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db.models.fields.json import JSONField
from django.core.cache import cache
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from django.db.models.deletion import CASCADE, PROTECT
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from cmj.mixins import CmjAuditoriaModelMixin, CmjModelMixin
from cmj.utils import get_settings_auth_user_model
from sapl.utils import (LISTA_DE_UFS, YES_NO_CHOICES)

RELATORIO_ATOS_ACESSADOS = (('S', _('Sim')),
                            ('N', _('Não')))

SEQUENCIA_NUMERACAO_PROTOCOLO = (('A', _('Sequencial por ano')),
                                 ('L', _('Sequencial por legislatura')),
                                 ('U', _('Sequencial único')))

SEQUENCIA_NUMERACAO_PROPOSICAO = (('A', _('Sequencial por ano para cada autor')),
                                  ('B', _('Sequencial por ano indepententemente do autor')))

ESFERA_FEDERACAO_CHOICES = (('M', _('Municipal')),
                            ('E', _('Estadual')),
                            ('F', _('Federal')),
                            )

ASSINATURA_ATA_CHOICES = (
    ('M', _('Mesa Diretora da Sessão')),
    ('P', _('Apenas o Presidente da Sessão')),
    ('T', _('Todos os Parlamentares Presentes na Sessão')),
)


class CasaLegislativa(models.Model):
    FIELDFILE_NAME = ('logotipo', )

    metadata = JSONField(
        verbose_name=_('Metadados'),
        blank=True, null=True, default=None, encoder=DjangoJSONEncoder)

    codigo = models.CharField(max_length=100,
                              blank=True,
                              verbose_name=_('Codigo'))
    nome = models.CharField(max_length=100, verbose_name=_('Nome'))
    sigla = models.CharField(max_length=100, verbose_name=_('Sigla'))
    endereco = models.CharField(max_length=100, verbose_name=_('Endereço'))
    cep = models.CharField(max_length=100, verbose_name=_('CEP'))
    municipio = models.CharField(max_length=50, verbose_name=_('Município'))
    uf = models.CharField(max_length=2,
                          choices=LISTA_DE_UFS,
                          verbose_name=_('UF'))
    telefone = models.CharField(
        max_length=100, blank=True, verbose_name=_('Telefone'))
    fax = models.CharField(
        max_length=100, blank=True, verbose_name=_('Fax'))
    logotipo = models.ImageField(
        blank=True,
        upload_to='sapl/public/casa/logotipo/',
        verbose_name=_('Logotipo'))
    endereco_web = models.URLField(
        max_length=100, blank=True, verbose_name=_('HomePage'))
    email = models.EmailField(
        max_length=100, blank=True, verbose_name=_('E-mail'))
    informacao_geral = models.TextField(
        max_length=100,
        blank=True,
        verbose_name=_('Informação Geral'))

    class Meta:
        verbose_name = _('Casa Legislativa')
        verbose_name_plural = _('Casa Legislativa')
        ordering = ['id']

    def __str__(self):
        return _('Casa Legislativa de %(municipio)s') % {
            'municipio': self.municipio}


class AppConfig(models.Model):

    POLITICA_PROTOCOLO_CHOICES = (
        ('O', _('Sempre Gerar Protocolo')),
        ('C', _('Perguntar se é pra gerar protocolo ao incorporar')),
        ('N', _('Nunca Protocolar ao incorporar uma proposição')),
    )
    estatisticas_acesso_normas = models.CharField(
        max_length=1,
        verbose_name=_('Estatísticas de acesso a normas'),
        choices=RELATORIO_ATOS_ACESSADOS, default='N')

    sequencia_numeracao_proposicao = models.CharField(
        max_length=1,
        verbose_name=_('Sequência de numeração de proposições'),
        choices=SEQUENCIA_NUMERACAO_PROPOSICAO, default='A')

    sequencia_numeracao_protocolo = models.CharField(
        max_length=1,
        verbose_name=_('Sequência de numeração de protocolos'),
        choices=SEQUENCIA_NUMERACAO_PROTOCOLO, default='A')

    esfera_federacao = models.CharField(
        max_length=1,
        blank=True,
        default="",
        verbose_name=_('Esfera Federação'),
        choices=ESFERA_FEDERACAO_CHOICES)

    # TODO: a ser implementado na versão 3.2
    # painel_aberto = models.BooleanField(
    #     verbose_name=_('Painel aberto para usuário anônimo'),
    #     choices=YES_NO_CHOICES, default=False)

    texto_articulado_proposicao = models.BooleanField(
        verbose_name=_('Usar Textos Articulados para Proposições'),
        choices=YES_NO_CHOICES, default=False)

    texto_articulado_materia = models.BooleanField(
        verbose_name=_('Usar Textos Articulados para Matérias'),
        choices=YES_NO_CHOICES, default=False)

    texto_articulado_norma = models.BooleanField(
        verbose_name=_('Usar Textos Articulados para Normas'),
        choices=YES_NO_CHOICES, default=True)

    proposicao_incorporacao_obrigatoria = models.CharField(
        verbose_name=_('Regra de incorporação de proposições e protocolo'),
        max_length=1, choices=POLITICA_PROTOCOLO_CHOICES, default='O')

    assinatura_ata = models.CharField(
        verbose_name=_('Quem deve assina a ata'),
        max_length=1, choices=ASSINATURA_ATA_CHOICES, default='T')

    receber_recibo_proposicao = models.BooleanField(
        verbose_name=_('Protocolar proposição somente com recibo?'),
        choices=YES_NO_CHOICES, default=True)

    protocolo_manual = models.BooleanField(
        verbose_name=_('Informar data e hora de protocolo?'),
        choices=YES_NO_CHOICES, default=False)

    escolher_numero_materia_proposicao = models.BooleanField(
        verbose_name=_(
            'Indicar número da matéria a ser gerada na proposição?'),
        choices=YES_NO_CHOICES, default=False)

    tramitacao_materia = models.BooleanField(
        verbose_name=_(
            'Tramitar matérias anexadas junto com as matérias principais?'),
        choices=YES_NO_CHOICES, default=True)

    tramitacao_documento = models.BooleanField(
        verbose_name=_(
            'Tramitar documentos anexados junto com os documentos principais?'),
        choices=YES_NO_CHOICES, default=True)

    # MÓDULO PAINEL

    mostrar_brasao_painel = models.BooleanField(
        default=False,
        verbose_name=_('Mostrar brasão da Casa no painel?'))

    mostrar_voto = models.BooleanField(
        verbose_name=_(
            'Exibir voto do Parlamentar antes de encerrar a votação?'),
        choices=YES_NO_CHOICES, default=False)

    cronometro_discurso = models.DurationField(
        verbose_name=_('Cronômetro do Discurso'),
        blank=True,
        null=True)

    cronometro_aparte = models.DurationField(
        verbose_name=_('Cronômetro do Aparte'),
        blank=True,
        null=True)

    cronometro_ordem = models.DurationField(
        verbose_name=_('Cronômetro da Ordem'),
        blank=True,
        null=True)

    cronometro_consideracoes = models.DurationField(
        verbose_name=_('Cronômetro de Considerações Finais'),
        blank=True,
        null=True)

    disabled = models.TextField(
        blank=True,
        default='',
        verbose_name=_('URLs Desativadas (urls completas / relativas / regex ignorecase ) - YAML Format'))

    class Meta:
        verbose_name = _('Configurações da Aplicação')
        verbose_name_plural = _('Configurações da Aplicação')
        permissions = (
            ('menu_sistemas', _('Renderizar Menu Sistemas')),
            ('view_tabelas_auxiliares', _('Visualizar Tabelas Auxiliares')),
        )
        ordering = ('-id',)

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):

        if not self.disabled:
            now = timezone.localtime()
            self.disabled = f'''
- periodo:
  start: {now.isoformat()} # ISOFORMAT datetime local
  end: {now.isoformat()}   # ISOFORMAT datetime local
  urls:
  - url: ^$ # path completo, relativo, regex
'''

        return models.Model.save(self, force_insert=force_insert, force_update=force_update, using=using, update_fields=update_fields)

    @classmethod
    def attr(cls, attr):
        value = cache.get(f'portalcmj_{attr}') if not settings.DEBUG else None
        if not value is None:
            return value

        config = AppConfig.objects.first()

        if not config:
            config = AppConfig()
            config.save()

        value = getattr(config, attr)
        if not settings.DEBUG:
            cache.set(f'portalcmj_{attr}', value, 600)

        return value

    def __str__(self):
        return _('Configurações da Aplicação - %(id)s') % {
            'id': self.id}


class TipoAutor(models.Model):
    descricao = models.CharField(
        max_length=50, verbose_name=_('Descrição'),
        help_text=_('Obs: Não crie tipos de autores '
                    'semelhante aos tipos fixos. '))

    content_type = models.OneToOneField(
        ContentType,
        null=True, default=None,
        verbose_name=_('Modelagem no SAPL'),
        on_delete=PROTECT)

    class Meta:
        ordering = ['descricao']
        verbose_name = _('Tipo de Autor')
        verbose_name_plural = _('Tipos de Autor')

    def __str__(self):
        return self.descricao


class Autor(models.Model):

    operadores = models.ManyToManyField(
        get_settings_auth_user_model(),
        through='OperadorAutor',
        through_fields=('autor', 'user'),
        symmetrical=False,
        related_name='autor_set',
        verbose_name='Operadores')

    tipo = models.ForeignKey(TipoAutor, verbose_name=_('Tipo do Autor'),
                             on_delete=models.PROTECT)

    content_type = models.ForeignKey(
        ContentType,
        blank=True, null=True, default=None,
        on_delete=PROTECT)
    object_id = models.PositiveIntegerField(
        blank=True, null=True, default=None)
    autor_related = GenericForeignKey('content_type', 'object_id')

    nome = models.CharField(
        max_length=120, blank=True, verbose_name=_('Nome do Autor'))

    cargo = models.CharField(max_length=50, blank=True)


    sign_compression = models.BooleanField(
        verbose_name=_('Assinatura com compressão'),
        choices=YES_NO_CHOICES, default=False)

    class Meta:
        verbose_name = _('Autor')
        verbose_name_plural = _('Autores')
        unique_together = (('content_type', 'object_id'), )
        ordering = ('nome',)

    def __str__(self):
        if self.autor_related:
            return str(self.autor_related)
        else:
            if self.nome:
                if self.cargo:
                    return '{} - {}'.format(self.nome, self.cargo)
                else:
                    return str(self.nome)

        if self.operadores.exists():
            return str(self.operadores.first())
        return '?'


class OperadorAutor(CmjAuditoriaModelMixin):

    user = models.ForeignKey(
        get_settings_auth_user_model(),
        verbose_name=_('Operador do Autor'),
        related_name='operadorautor_set',
        on_delete=CASCADE)

    autor = models.ForeignKey(
        Autor,
        related_name='operadorautor_set',
        verbose_name=_('Autor'),
        on_delete=CASCADE)

    operador_principal = models.BooleanField(
        verbose_name=_('Operador Principal do Autor'),
        choices=YES_NO_CHOICES, default=False)

    enviar_email = models.BooleanField(
        verbose_name=_('Enviar emails de notificação a este usuário'),
        choices=YES_NO_CHOICES, default=False)

    visibilidade_restrita = models.BooleanField(
        verbose_name=_('Ver apenas proposições criadas por este usuário'),
        choices=YES_NO_CHOICES, default=False)

    @property
    def user_name(self):
        return '%s - %s' % (
            self.user.get_display_name(),
            self.user.email)

    class Meta:
        verbose_name = _('Operador do Autor')
        verbose_name_plural = _('Operadores do Autor')
        unique_together = (
            ('user', 'autor', ),)
        ordering = ['id']

    def __str__(self):
        return self.user_name


class Metadata(CmjModelMixin):
    content_type = models.ForeignKey(
        ContentType,
        blank=True,
        null=True,
        default=None,
        on_delete=models.PROTECT)
    object_id = models.PositiveIntegerField(
        blank=True,
        null=True,
        default=None)
    content_object = GenericForeignKey('content_type', 'object_id')

    metadata = JSONField(
        verbose_name=_('Metadados'),
        blank=True, null=True, default=None, encoder=DjangoJSONEncoder)

    class Meta:
        verbose_name = _('Metadado')
        verbose_name_plural = _('Metadados')
        unique_together = (('content_type', 'object_id'), )
        ordering = ['id']

    def __str__(self):
        return f'Metadata de {self.content_object}'
