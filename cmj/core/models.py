
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.base_user import BaseUserManager, AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin, Group
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied
from django.db import models
from django.db.models import permalink
from django.db.models.deletion import PROTECT, CASCADE, SET_NULL
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from image_cropping import ImageCropField, ImageRatioField

from cmj.diarios.models import DiarioOficial
from cmj.globalrules import MENU_PERMS_FOR_USERS, GROUP_SOCIAL_USERS
from cmj.utils import get_settings_auth_user_model, normalize, YES_NO_CHOICES,\
    UF, CmjChoices
from sapl.materia.models import MateriaLegislativa, DocumentoAcessorio
from sapl.norma.models import NormaJuridica
from sapl.parlamentares.models import Parlamentar
from sapl.sessao.models import SessaoPlenaria


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
        permissions = MENU_PERMS_FOR_USERS
        ordering = ('first_name', 'last_name')

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

    @permalink
    def get_absolute_url(self):
        return 'users_profile', [self.pk], {}

    def delete(self, using=None, keep_parents=False):

        if self.groups.all().exclude(name=GROUP_SOCIAL_USERS).exists():
            raise PermissionDenied(
                _('Você não possui permissão para se autoremover do Portal!'))

        return AbstractBaseUser.delete(
            self, using=using, keep_parents=keep_parents)


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


class CmjCleanMixin:

    def clean(self):
        """
        Check for instances with null values in unique_together fields.
        """
        from django.core.exceptions import ValidationError

        super(CmjCleanMixin, self).clean()

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


class CmjModelMixin(CmjCleanMixin, models.Model):
    # para migração
    """created = models.DateTimeField(
        verbose_name=_('created'),
        editable=True, auto_now_add=False)
    modified = models.DateTimeField(
        verbose_name=_('modified'), editable=True, auto_now=False)"""
    # para produção
    created = models.DateTimeField(
        verbose_name=_('created'),
        editable=False, auto_now_add=True)
    modified = models.DateTimeField(
        verbose_name=_('modified'), editable=False, auto_now=True)

    class Meta:
        abstract = True

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None, clean=True):

        import inspect
        funcs = list(filter(lambda x: x == 'revision_pre_delete_signal',
                            map(lambda x: x[3], inspect.stack())))

        if clean and not funcs:
            self.clean()

        return models.Model.save(
            self,
            force_insert=force_insert,
            force_update=force_update,
            using=using,
            update_fields=update_fields)


class CmjAuditoriaModelMixin(CmjModelMixin):

    owner = models.ForeignKey(
        get_settings_auth_user_model(),
        verbose_name=_('owner'),
        related_name='+',
        on_delete=PROTECT)
    modifier = models.ForeignKey(
        get_settings_auth_user_model(),
        verbose_name=_('modifier'),
        related_name='+',
        on_delete=PROTECT)

    class Meta:
        abstract = True


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
        verbose_name=_('Logradouro'))

    tipo = models.ForeignKey(
        TipoLogradouro,
        blank=True, null=True, default=None,
        related_name='trechos_set',
        verbose_name=_('Tipo de Logradouro'))

    bairro = models.ForeignKey(
        Bairro,
        blank=True, null=True, default=None,
        related_name='trechos_set',
        verbose_name=_('Bairro'))

    distrito = models.ForeignKey(
        Distrito,
        blank=True, null=True, default=None,
        related_name='trechos_set',
        verbose_name=_('Distrito'))

    regiao_municipal = models.ForeignKey(
        RegiaoMunicipal,
        blank=True, null=True, default=None,
        related_name='trechos_set',
        verbose_name=_('Região Municipal'))

    municipio = models.ForeignKey(
        Municipio,
        related_name='trechos_set',
        verbose_name=_('Município'))

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

    objects = AreaTrabalhoManager()

    TIPO_GABINETE = 10
    TIPO_ADMINISTRATIVO = 20
    TIPO_INSTITUCIONAL = 30
    TIPO_PROCURADORIA = 90
    TIPO_PUBLICO = 99

    TIPO_AREATRABALHO_CHOICE = CmjChoices(
        (TIPO_GABINETE, 'tipo_gabinete', _('Gabinete Parlamentar')),
        (TIPO_ADMINISTRATIVO, 'tipo_administrativo',
         _('Setor Administrativo')),
        (TIPO_INSTITUCIONAL, 'tipo_institucional', _('Institucional')),
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
        blank=True, null=True, default=None)
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
        blank=True, null=True, default=None)
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
