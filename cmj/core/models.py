
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.base_user import BaseUserManager, AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin, Group
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from django.db.models.deletion import PROTECT, CASCADE, SET_NULL
from django.db.models.fields.json import JSONField
from django.utils import timezone
from django.utils.decorators import classonlymethod
from django.utils.translation import gettext_lazy as _
from image_cropping import ImageCropField, ImageRatioField

from cmj.globalrules import PERMS_FOR_USERS, GROUP_SOCIAL_USERS
from cmj.mixins import CmjChoices, CmjModelMixin, CmjAuditoriaModelMixin
from cmj.utils import get_settings_auth_user_model, normalize, YES_NO_CHOICES,\
    UF, texto_upload_path
from sapl.utils import hash_sha512, PortalFileField, OverwriteStorage


def group_social_users_add_user(user):
    if user.groups.filter(name=GROUP_SOCIAL_USERS).exists():
        return

    g = Group.objects.get_or_create(name=GROUP_SOCIAL_USERS)[0]
    user.groups.add(g)
    user.save()


def groups_remove_user(user, groups_name):
    if not isinstance(groups_name, list):
        groups_name = [groups_name, ]
    for group_name in groups_name:
        if not group_name or not user.groups.filter(
                name=group_name).exists():
            continue
        g = Group.objects.get_or_create(name=group_name)[0]
        user.groups.remove(g)


def groups_add_user(user, groups_name):
    if not isinstance(groups_name, list):
        groups_name = [groups_name, ]
    for group_name in groups_name:
        if not group_name or user.groups.filter(
                name=group_name).exists():
            continue
        g = Group.objects.get_or_create(name=group_name)[0]
        user.groups.add(g)


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self,
                     email, password, is_staff, is_superuser, **extra_fields):
        """
        Creates and saves a User with the given username, email and password.
        """
        now = timezone.now()
        if not email:
            raise ValueError('The given email must be set')
        email = self.normalize_email(email)
        user = self.model(email=email,
                          is_staff=is_staff,
                          is_active=True,
                          is_superuser=is_superuser,
                          date_joined=now, **extra_fields)
        user.set_password(password)
        try:
            user.save(using=self._db)
        except:
            user = self.model.objects.get_by_natural_key(email)

        group_social_users_add_user(user)
        return user

    def create_user(self, email, password=None, **extra_fields):
        return self._create_user(email, password, False, False, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        return self._create_user(email, password, True, True, **extra_fields)


def sizeof_fmt(num, suffix='B'):
    """
    Shamelessly copied from StackOverflow:
    http://stackoverflow.com/questions/1094841/reusable-library-to-get-human-readable-version-of-file-size

    :param num:
    :param suffix:
    :return:
    """
    for unit in ['', 'Ki', 'Mi', 'Gi', 'Ti', 'Pi', 'Ei', 'Zi']:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, 'Yi', suffix)


def avatar_validation(image):
    if image:
        # 10 MB
        max_file_size = 10 * 1024 * 1024
        if image.size > max_file_size:
            raise forms.ValidationError(
                _('The maximum file size is {0}').format(sizeof_fmt(max_file_size)))


class User(AbstractBaseUser, PermissionsMixin):
    FIELDFILE_NAME = ('avatar', )

    metadata = JSONField(
        verbose_name=_('Metadados'),
        blank=True, null=True, default=None, encoder=DjangoJSONEncoder)

    objects = UserManager()
    USERNAME_FIELD = 'email'

    email = models.EmailField(_('email address'), unique=True)

    first_name = models.CharField(_('first name'), max_length=30, blank=True)
    last_name = models.CharField(_('last name'), max_length=30, blank=True)
    is_staff = models.BooleanField(
        _('staff status'), default=False,
        help_text=_('Designates whether the user can log into this admin '
                    'site.'))
    is_active = models.BooleanField(
        _('active'), default=True,
        help_text=_('Designates whether this user should be treated as '
                    'active. Unselect this instead of deleting accounts.'))
    date_joined = models.DateTimeField(_('date joined'), default=timezone.now)

    # -------------------------------------------------

    avatar = ImageCropField(
        upload_to="avatars/", verbose_name=_('Avatar'),
        validators=[avatar_validation], null=True, blank=True)

    cropping = ImageRatioField(
        'avatar', '128x128',
        verbose_name=_('Seleção (Enquadramento)'), help_text=_(
            'A configuração do Avatar '
            'é possível após a atualização da fotografia.'))

    pwd_created = models.BooleanField(
        _('Usuário de Rede Social Customizou Senha?'), default=False)

    be_notified_by_email = models.BooleanField(
        _('Receber Notificações por email?'), default=True)

    class Meta(AbstractBaseUser.Meta):
        abstract = False
        permissions = PERMS_FOR_USERS
        ordering = ('-is_superuser', 'first_name', 'last_name')
        verbose_name = _('Usuário')
        verbose_name_plural = _('Usuários')

    def __str__(self):
        return self.get_display_name()

    @property
    def username(self):
        return self.get_username()

    def get_full_name(self):
        """
        Returns the first_name plus the last_name, with a space in between.
        """
        return ' '.join([self.first_name, self.last_name]).strip()

    def get_short_name(self):
        """
        Returns the short name for the user.
        """
        return self.first_name

    def get_display_name(self):
        return self.get_full_name() or self.email

    def is_only_socialuser(self):
        group_social_users_add_user(self)
        return self.groups.count() == 1

    def get_absolute_url(self):
        return 'users_profile', [self.pk], {}

    """def delete(self, using=None, keep_parents=False):

        if self.groups.all().exclude(name=GROUP_SOCIAL_USERS).exists():
            raise PermissionDenied(
                _('Você não possui permissão para se autoremover do Portal!'))

        return AbstractBaseUser.delete(
            self, using=using, keep_parents=keep_parents)"""


class AuditLogManager(models.Manager):
    use_for_related_fields = True

    def last_action_user(self):
        # for_related_fields
        qs = self.get_queryset()
        qs = qs.filter(user__isnull=False).first()
        return qs

    def first_action_user(self):
        # for_related_fields
        qs = self.get_queryset()
        qs = qs.filter(user__isnull=False).last()
        return qs

    def actions_users(self):
        # for_related_fields
        qs = self.get_queryset()
        qs = qs.filter(user__isnull=False)
        return qs


class AuditLog(models.Model):
    objects = AuditLogManager()

    STATUS_PRIVATE = 99
    STATUS_RESTRICT_PERMISSION = 2
    STATUS_RESTRICT_USER = 1
    STATUS_PUBLIC = 0

    VISIBILIDADE_STATUS = (
        (STATUS_RESTRICT_PERMISSION, _('Restrição por Permissão')),
        (STATUS_RESTRICT_USER, _('Restrição por Usuário')),
        (STATUS_PRIVATE, _('Privado')),
        (STATUS_PUBLIC, _('Público')),
    )

    OPERATION_CHOICES = (
        ('U', 'Atualizado'),
        ('C', 'Criado'),
        ('D', 'Excluído'),
        ('P', 'Pesquisa'),
    )

    visibilidade = models.IntegerField(
        _('Visibilidade'),
        choices=VISIBILIDADE_STATUS,
        blank=True, null=True, default=None)

    user = models.ForeignKey(
        get_settings_auth_user_model(),
        verbose_name=_('Usuário'),
        on_delete=SET_NULL,
        blank=True, null=True, default=None
    )

    email = models.CharField(max_length=100,
                             verbose_name=_('email'),
                             blank=True,
                             db_index=True)

    operation = models.CharField(
        max_length=1,
        verbose_name=_('operation'),
        choices=OPERATION_CHOICES,
        db_index=True)

    timestamp = models.DateTimeField(
        verbose_name=_('timestamp'),
        editable=False, auto_now_add=True)

    obj = JSONField(
        verbose_name=_('Object'),
        blank=True, null=True, default=None, encoder=DjangoJSONEncoder)

    content_type = models.ForeignKey(
        ContentType,
        blank=True, null=True, default=None,
        on_delete=PROTECT)
    object_id = models.PositiveIntegerField(
        blank=True, null=True, default=None)
    content_object = GenericForeignKey('content_type', 'object_id')

    obj_id = models.PositiveIntegerField(verbose_name=_('object_id'),
                                         db_index=True)

    model_name = models.CharField(max_length=100, verbose_name=_('model'),
                                  db_index=True)
    app_name = models.CharField(max_length=100,
                                verbose_name=_('app'),
                                db_index=True)

    class Meta:
        verbose_name = _('AuditLog')
        verbose_name_plural = _('AuditLogs')
        ordering = ('-id',)

    def __str__(self):
        return "[%s] %s %s.%s %s" % (self.timestamp,
                                     self.operation,
                                     self.app_name,
                                     self.model_name,
                                     self.user,
                                     )


class CmjSearchMixin(models.Model):

    search = models.TextField(blank=True, default='')

    class Meta:
        abstract = True

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None, auto_update_search=True):

        if auto_update_search and hasattr(self, 'fields_search'):
            search = ''
            for str_field in self.fields_search:
                fields = str_field.split('__')
                if len(fields) == 1:
                    try:
                        search += str(getattr(self, str_field)) + ' '
                    except:
                        pass
                else:
                    _self = self
                    for field in fields:
                        _self = getattr(_self, field)
                    search += str(_self) + ' '
            self.search = search
        self.search = normalize(self.search)

        return super(CmjSearchMixin, self).save(force_insert=force_insert, force_update=force_update, using=using, update_fields=update_fields)


class Municipio(models.Model):  # Localidade
    # TODO filter on migration leaving only cities

    REGIAO_CHOICES = (
        ('CO', 'Centro-Oeste'),
        ('NE', 'Nordeste'),
        ('NO', 'Norte'),
        ('SE', 'Sudeste'),  # TODO convert on migrate SD => SE
        ('SL', 'Sul'),
        ('EX', 'Exterior'),
    )

    nome = models.CharField(max_length=50, blank=True)
    uf = models.CharField(
        max_length=2, blank=True, choices=UF)
    regiao = models.CharField(
        max_length=2, blank=True, choices=REGIAO_CHOICES)

    class Meta:
        verbose_name = _('Município')
        verbose_name_plural = _('Municípios')
        ordering = ['id']

    def __str__(self):
        return _('%(nome)s - %(uf)s (%(regiao)s)') % {
            'nome': self.nome, 'uf': self.uf, 'regiao': self.regiao
        }


class Cep(models.Model):
    numero = models.CharField(max_length=9, verbose_name=_('CEP'), unique=True)

    class Meta:
        verbose_name = _('CEP')
        verbose_name_plural = _("CEP's")
        ordering = ('numero'),

    def __str__(self):
        return self.numero


class RegiaoMunicipal(models.Model):

    TIPO_CHOICES = [
        ('AU', _('Área Urbana')),
        ('AR', _('Área Rural')),
        ('UA', _('Área Única'))]

    nome = models.CharField(
        max_length=254, verbose_name=_('Região Municipal'))
    tipo = models.CharField(
        max_length=2,
        default='AU',
        choices=TIPO_CHOICES, verbose_name='Tipo da Região')

    class Meta:
        verbose_name = _('Região Municipal')
        verbose_name_plural = _('Regiões Municipais')
        unique_together = (
            ('nome', 'tipo'),)
        ordering = ['id']

    def __str__(self):
        return '%s - %s' % (
            self.nome, self.get_tipo_display())


class Distrito(models.Model):
    nome = models.CharField(
        max_length=254,
        verbose_name=_('Nome do Distrito'),
        unique=True)

    class Meta:
        verbose_name = _('Distrito')
        verbose_name_plural = _("Distritos")
        ordering = ['id']

    def __str__(self):
        return self.nome


class Bairro(models.Model):
    nome = models.CharField(
        max_length=254,
        verbose_name=_('Bairro'),
        unique=True)

    codigo = models.PositiveIntegerField(
        default=0,
        verbose_name='Código',
        help_text=_('Código do Bairro no Cadastro Oficial do Município'))

    outros_nomes = models.TextField(
        blank=True,
        verbose_name=_('Outros Nomes'),
        help_text=_('Ocorrências similares'))

    class Meta:
        ordering = ('nome',)
        verbose_name = _('Bairro')
        verbose_name_plural = _("Bairros")

    def __str__(self):
        return self.nome


class TipoLogradouro(models.Model):
    nome = models.CharField(
        max_length=254,
        verbose_name=_('Tipo de Logradouro'),
        unique=True)

    class Meta:
        verbose_name = _('Tipo de Logradouro')
        verbose_name_plural = _("Tipos de Logradouros")
        ordering = ('nome',)

    def __str__(self):
        return self.nome


class Logradouro(models.Model):
    nome = models.CharField(
        max_length=254,
        verbose_name=_('Logradouro'),
        unique=True)

    class Meta:
        verbose_name = _('Logradouro')
        verbose_name_plural = _("Logradouros")
        ordering = ('nome',)

    def __str__(self):
        return self.nome


class Trecho(CmjSearchMixin, CmjModelMixin):
    logradouro = models.ForeignKey(
        Logradouro,
        blank=True, null=True, default=None,
        related_name='trechos_set',
        verbose_name=_('Logradouro'),
        on_delete=PROTECT)

    tipo = models.ForeignKey(
        TipoLogradouro,
        blank=True, null=True, default=None,
        related_name='trechos_set',
        verbose_name=_('Tipo de Logradouro'),
        on_delete=PROTECT)

    bairro = models.ForeignKey(
        Bairro,
        blank=True, null=True, default=None,
        related_name='trechos_set',
        verbose_name=_('Bairro'),
        on_delete=PROTECT)

    distrito = models.ForeignKey(
        Distrito,
        blank=True, null=True, default=None,
        related_name='trechos_set',
        verbose_name=_('Distrito'),
        on_delete=PROTECT)

    regiao_municipal = models.ForeignKey(
        RegiaoMunicipal,
        blank=True, null=True, default=None,
        related_name='trechos_set',
        verbose_name=_('Região Municipal'),
        on_delete=PROTECT)

    municipio = models.ForeignKey(
        Municipio,
        related_name='trechos_set',
        verbose_name=_('Município'),
        on_delete=PROTECT)

    LADO_CHOICES = [
        ('NA', _('Não Aplicável')),
        ('AL', _('Ambos os Lados')),
        ('LE', _('Lado Esquerdo')),
        ('LD', _('Lado Direito'))]

    lado = models.CharField(
        max_length=2,
        default='AL',
        choices=LADO_CHOICES, verbose_name='Lado do Logradouro')

    numero_inicial = models.PositiveIntegerField(
        blank=True, null=True, verbose_name='Número Inicial')
    numero_final = models.PositiveIntegerField(
        blank=True, null=True, verbose_name='Número Final')

    # http://mundogeo.com/blog/2006/03/01/eixo-de-logradouro-conceitos-e-beneficios-parte-1/
    # Pelo que vi, os correios afirmar não haver mais de um cep por trecho,
    # portanto essa relação poderia ser 1xN, mas pra evitar contratempos
    # futuros.
    cep = models.ManyToManyField(
        Cep,
        related_name='trechos_set',
        verbose_name=_('Cep'))

    @property
    def fields_search(self):
        return [
            'tipo__nome',
            'logradouro__nome',
            'bairro__nome',
            'distrito__nome',
            'regiao_municipal__nome',
            'municipio__nome',
            'cep']

    class Meta:
        verbose_name = _('Trecho de Logradouro')
        verbose_name_plural = _("Trechos de Logradouro")
        ordering = [
            'municipio__nome',
            'regiao_municipal__nome',
            'distrito__nome',
            'bairro__nome',
            'tipo__nome',
            'logradouro__nome']
        unique_together = (
            ('municipio',
                'regiao_municipal',
                'distrito',
                'bairro',
                'logradouro',
                'tipo',
                'lado',
                'numero_inicial',
                'numero_final'),)

    def __str__(self):
        uf = str(self.municipio.uf) if self.municipio else ''
        municipio = str(self.municipio.nome) + '-' if self.municipio else ''
        tipo = str(self.tipo) + ' ' if self.tipo else ''
        logradouro = str(self.logradouro) + ' - ' if self.logradouro else ''
        bairro = self.bairro.nome + ' - ' if self.bairro else ''
        distrito = self.distrito.nome + ' - ' if self.distrito else ''
        rm = self.regiao_municipal.nome + \
            ' - ' if self.regiao_municipal else ''

        join_cep = ' - '.join(self.cep.values_list('numero', flat=True))
        join_cep = ' - ' + join_cep if join_cep else ''

        return '%s%s%s%s%s%s%s%s' % (
            tipo, logradouro, bairro, distrito, rm, municipio, uf, join_cep
        )


class ImpressoEnderecamento(models.Model):
    nome = models.CharField(max_length=254, verbose_name='Nome do Impresso')

    TIPO_CHOICES = [
        ('ET', _('Folha de Etiquetas')),
        ('EV', _('Envelopes'))]

    tipo = models.CharField(
        max_length=2,
        default='ET',
        choices=TIPO_CHOICES, verbose_name='Tipo do Impresso')

    largura_pagina = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name=_('Largura da Página'),
        help_text=_('Em centímetros'))
    altura_pagina = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name=_('Altura da Página'),
        help_text=_('Em centímetros'))

    margem_esquerda = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name=_('Margem Esquerda'),
        help_text=_('Em centímetros'))
    margem_superior = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name=_('Margem Superior'),
        help_text=_('Em centímetros'))

    colunasfolha = models.PositiveSmallIntegerField(
        verbose_name=_('Colunas'))
    linhasfolha = models.PositiveSmallIntegerField(
        verbose_name=_('Linhas'))

    larguraetiqueta = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name=_('Largura da Etiqueta'),
        help_text=_('Em centímetros'))
    alturaetiqueta = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name=_('Altura da Etiquta'),
        help_text=_('Em centímetros'))

    entre_colunas = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name=_('Distância Entre Colunas'),
        help_text=_('Em centímetros'))
    entre_linhas = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name=_('Distância Entre Linhas'),
        help_text=_('Em centímetros'))

    fontsize = models.DecimalField(
        max_digits=5, decimal_places=2,
        verbose_name=_('Tamanho da Letra'),
        help_text=_('Em Pixels'))

    rotate = models.BooleanField(
        default=False,
        choices=YES_NO_CHOICES,
        verbose_name=_('Rotacionar Texto'))

    class Meta:
        verbose_name = _('Impresso para Endereçamento')
        verbose_name_plural = _("Impressos para Endereçamento")
        ordering = ['id']

    def __str__(self):
        return self.nome


class AreaTrabalhoManager(models.Manager):

    use_for_related_fields = True

    def areatrabalho_de_parlamentares(self):
        qs = self.get_queryset()
        qs = qs.filter(tipo=10, ativo=True)
        return qs

    def areatrabalho_da_instituicao(self):
        qs = self.get_queryset()
        qs = qs.filter(tipo=30, ativo=True)
        return qs

    def areatrabalho_publica(self):
        qs = self.get_queryset()
        qs = qs.filter(tipo=99, ativo=True)
        return qs


class AreaTrabalho(CmjAuditoriaModelMixin):

    from sapl.parlamentares.models import Parlamentar
    objects = AreaTrabalhoManager()

    TIPO_GABINETE = 10
    TIPO_ADMINISTRATIVO = 20
    TIPO_INSTITUCIONAL = 30
    TIPO_RECEPCAO = 40
    TIPO_PROCURADORIA = 90
    TIPO_PUBLICO = 99

    TIPO_AREATRABALHO_CHOICE = CmjChoices(
        (TIPO_GABINETE, 'tipo_gabinete', _('Gabinete Parlamentar')),
        (TIPO_ADMINISTRATIVO, 'tipo_administrativo',
         _('Setor Administrativo')),
        (TIPO_INSTITUCIONAL, 'tipo_institucional', _('Institucional')),
        (TIPO_RECEPCAO, 'tipo_recepcao', _('Recepção')),
        (TIPO_PROCURADORIA, 'tipo_procuradoria', _('Procuradoria Jurídica')),
        (TIPO_PUBLICO, 'tipo_publico', _('Documentos Públicos')),
    )

    nome = models.CharField(max_length=100, blank=True, default='',
                            verbose_name=_('Nome'))

    descricao = models.CharField(
        default='', max_length=254, verbose_name=_('Descrição'))

    operadores = models.ManyToManyField(
        get_settings_auth_user_model(),
        through='OperadorAreaTrabalho',
        through_fields=('areatrabalho', 'user'),
        symmetrical=False,
        related_name='areatrabalho_set')

    parlamentar = models.ForeignKey(
        Parlamentar,
        verbose_name=_('Parlamentar'),
        related_name='areatrabalho_set',
        blank=True, null=True, on_delete=SET_NULL)

    tipo = models.IntegerField(
        _('Tipo da Área de Trabalho'),
        choices=TIPO_AREATRABALHO_CHOICE,
        default=TIPO_GABINETE)

    ativo = models.BooleanField(
        _('Área de trabalho Ativa'),
        choices=YES_NO_CHOICES,
        default=True)

    class Meta:
        ordering = ('-ativo', '-tipo', 'parlamentar')
        verbose_name = _('Área de Trabalho')
        verbose_name_plural = _('Áreas de Trabalho')

    def __str__(self):
        return self.nome


class OperadorAreaTrabalho(CmjAuditoriaModelMixin):

    user = models.ForeignKey(
        get_settings_auth_user_model(),
        verbose_name=_('Operador da Área de Trabalho'),
        related_name='operadorareatrabalho_set',
        on_delete=CASCADE)

    areatrabalho = models.ForeignKey(
        AreaTrabalho,
        related_name='operadorareatrabalho_set',
        verbose_name=_('Área de Trabalho'),
        on_delete=CASCADE)

    grupos_associados = models.ManyToManyField(
        Group,
        verbose_name=_('Grupos Associados'),
        related_name='operadorareatrabalho_set')

    @property
    def user_name(self):
        return '%s - %s' % (
            self.user.get_display_name(),
            self.user.email)

    class Meta:
        verbose_name = _('Operador')
        verbose_name_plural = _('Operadores')
        ordering = ['id']

    def __str__(self):
        return self.user_name


class NotificacaoManager(models.Manager):

    def unread(self):
        qs = self.get_queryset()
        qs = qs.filter(read=False)
        return qs

    def read(self):
        qs = self.get_queryset()
        qs = qs.filter(read=True)
        return qs


class Notificacao(CmjModelMixin):

    objects = NotificacaoManager()

    user = models.ForeignKey(
        get_settings_auth_user_model(),
        blank=True, null=True, default=None,
        verbose_name=_('Usuário Notificado'),
        related_name='notificacao_set',
        on_delete=CASCADE)

    user_origin = models.ForeignKey(
        get_settings_auth_user_model(),
        blank=True, null=True, default=None,
        on_delete=PROTECT,
        verbose_name=_('owner'), related_name='notificacao_origem_set')

    content_type = models.ForeignKey(
        ContentType,
        blank=True, null=True, default=None,
        on_delete=PROTECT)
    object_id = models.PositiveIntegerField(
        blank=True, null=True, default=None)
    content_object = GenericForeignKey('content_type', 'object_id')

    areatrabalho = models.ForeignKey(
        'AreaTrabalho',
        blank=True, null=True, default=None,
        on_delete=PROTECT,
        verbose_name=_('Área de Trabalho'), related_name='notificacao_set')

    read = models.BooleanField(
        _('Lida'),
        choices=YES_NO_CHOICES,
        default=False)

    class Meta:
        verbose_name = _('Notificação')
        verbose_name_plural = _('Notificações')
        ordering = ['id']
        permissions = (
            ('popup_notificacao',
             _('Visualização das notificações em Popup no Avatar do Usuário')),
        )

    @property
    def user_name(self):
        return '%s - %s' % (
            self.user.get_display_name(),
            self.user.email)

    def __str__(self):
        return self.user_name


class OcrMyPDF(models.Model):

    content_type = models.ForeignKey(
        ContentType,
        blank=True, null=True, default=None,
        on_delete=PROTECT)
    object_id = models.PositiveIntegerField(
        blank=True, null=True, default=None)
    content_object = GenericForeignKey('content_type', 'object_id')

    field = models.CharField(
        default='', max_length=254, verbose_name=_('Field'))

    created = models.DateTimeField(
        verbose_name=_('created'),
        editable=False, auto_now_add=True)

    concluido = models.DateTimeField(
        verbose_name=_('created'),
        editable=False, auto_now=True)

    sucesso = models.BooleanField(
        _('Sucesso'),
        choices=YES_NO_CHOICES,
        default=True)

    class Meta:
        ordering = ['id']


class Bi(models.Model):

    content_type = models.ForeignKey(ContentType,
                                     on_delete=PROTECT)

    ano = models.PositiveSmallIntegerField(
        verbose_name=_('Ano'),
        default=0)

    results = JSONField(
        verbose_name=_('Json results'),
        blank=True, null=True, default=None, encoder=DjangoJSONEncoder)

    modified = models.DateTimeField(
        verbose_name=_('modified'), editable=False, auto_now=True)

    class Meta:
        verbose_name = _('Bi')
        verbose_name_plural = _('Bi')
        ordering = ('-id', '-ano', 'content_type', )
        unique_together = (("ano", "content_type"),)


def certidao_create_path(instance, filename):
    return texto_upload_path(instance, filename, subpath='')


class CertidaoPublicacao(CmjAuditoriaModelMixin):

    FIELDFILE_NAME = ('certificado',)

    metadata = JSONField(
        verbose_name=_('Metadados'),
        blank=True, null=True, default=None, encoder=DjangoJSONEncoder)

    content_type = models.ForeignKey(
        ContentType,
        blank=True, null=True, default=None,
        on_delete=PROTECT)
    object_id = models.PositiveIntegerField(
        blank=True, null=True, default=None)
    content_object = GenericForeignKey('content_type', 'object_id')

    hash_code = models.TextField(verbose_name=_('Hash de Publicação'),
                                 max_length=200,
                                 blank=True)

    field_name = models.CharField(verbose_name=_('Field Name'),
                                  max_length=200,
                                  blank=True)

    cancelado = models.BooleanField(
        _('Cancelado '),
        choices=YES_NO_CHOICES,
        default=False)

    revogado = models.BooleanField(
        _('Certidão Revogada'),
        choices=YES_NO_CHOICES,
        default=False)

    certificado = PortalFileField(
        blank=True,
        null=True,
        upload_to=certidao_create_path,
        # storage=OverwriteStorage(),
        verbose_name=_('Certificado'),
        max_length=512)

    class Meta:
        verbose_name = _('Certidão de Publicação')
        verbose_name_plural = _('Certidões de Publicação')
        ordering = ('-id', )

    @classonlymethod
    def gerar_certidao(cls, user, obj, file_field_name, pk=None):

        path = getattr(obj, file_field_name).path
        if not path:
            return

        original__path = path.replace(
            'media/sapl', 'media/original__sapl')

        hash_code = hash_sha512(original__path)

        cp = CertidaoPublicacao()
        cp.id = pk
        cp.content_object = obj
        cp.hash_code = hash_code
        cp.owner = user
        cp.modifier = user
        cp.field_name = file_field_name
        cp.certifidado = None

        if not pk:
            cp.save()
        return cp


class IAQuotaManager(models.Manager):
    use_for_related_fields = True

    def quotas_with_margin(self):
        """
        Retorna as quotas que possuem margem para serem utilizadas hoje.
        """
        hoje = timezone.now().date()
        return self.get_queryset().filter(
            ativo=True
        ).annotate(
            total=models.Sum('iaquotaslog_set__peso', filter=models.Q(iaquotaslog_set__data=hoje))
        ).filter(
            models.Q(total__isnull=True) | models.Q(total__lt=models.F('quota_diaria'))
        ).order_by('-total', '-quota_diaria')

class IAQuota(models.Model):

    objects = IAQuotaManager()

    quota_diaria = models.PositiveIntegerField(
        verbose_name=_('Quota Diária'),
        default=0)

    modelo = models.CharField(
        max_length=100,
        unique=True,
        verbose_name=_('Modelo'), )

    ativo = models.BooleanField(
        _('Ativo'),
        choices=YES_NO_CHOICES,
        default=True)

    class Meta:
        verbose_name = _('Quota IA')
        verbose_name_plural = _('Quotas IA')
        ordering = ('-id', )

    def has_margin(self):
        """
        Verifica se a quota tem margem para ser utilizada.
        """
        if not self.ativo:
            return False

        hoje = timezone.now().date()
        sum_log = self.iaquotaslog_set.filter(data=hoje).aggregate(
            total=models.Sum('peso'))['total'] or 0

        return sum_log < self.quota_diaria

    def create_log(self, peso=1):
        """
        Cria um log de utilização da quota.
        """
        log = IAQuotasLog(
            quota=self,
            peso=peso
        )
        log.save()
        return log


class IAQuotasLog(models.Model):

    quota = models.ForeignKey(
        IAQuota,
        verbose_name=_('Quota'),
        related_name='iaquotaslog_set',
        on_delete=CASCADE)

    data = models.DateField(
        verbose_name=_('Data'),
        help_text=_('Data do Log de Quota IA'),
        default=timezone.now)

    timestamp = models.DateTimeField(
        verbose_name=_('Timestamp'),
        editable=False, auto_now_add=True)

    peso = models.PositiveIntegerField(
        verbose_name=_('Peso'),
        default=1)

    class Meta:
        verbose_name = _('Log de Quota IA')
        verbose_name_plural = _('Logs de Quota IA')
        ordering = ('-id', )
