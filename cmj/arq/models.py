import re

from django.contrib.postgres.fields.jsonb import JSONField
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from django.db.models.deletion import PROTECT
from django.utils.translation import ugettext_lazy as _

from cmj.utils import get_settings_auth_user_model, texto_upload_path, normalize
from sapl.utils import PortalFileField


class Draft(models.Model):

    metadata = JSONField(
        verbose_name=_('Metadados'),
        blank=True, null=True, default=None, encoder=DjangoJSONEncoder)

    owner = models.ForeignKey(
        get_settings_auth_user_model(),
        verbose_name=_('owner'), related_name='+',
        on_delete=PROTECT)

    created = models.DateTimeField(
        verbose_name=_('created'), editable=False, auto_now_add=True)

    descricao = models.TextField(
        verbose_name=_('Descrição'),
        blank=True, null=True, default=None)

    class Meta:
        ordering = ('-created',)

        verbose_name = _('Draft')
        verbose_name_plural = _('Draft')


def draftmidia_path(instance, filename):

    filename = re.sub('\s', '_', normalize(filename.strip()).lower())
    filename = filename.split('.')

    filename = '' if len(filename[-1]) > 4 else f'.{filename[-1]}'

    str_path = ('./cmj/private/%(model_name)s/%(owner)s/%(draft)s/%(filename)s')

    path = str_path % \
        {
            'model_name': instance._meta.model_name,
            'owner': instance.draft.owner.id,
            'draft': instance.draft.id,
            'filename': f'{instance.id:09}{filename}'
        }

    return path


class DraftMidia(models.Model):

    FIELDFILE_NAME = ('arquivo',)

    metadata = JSONField(
        verbose_name=_('Metadados'),
        blank=True, null=True, default=None, encoder=DjangoJSONEncoder)

    draft = models.ForeignKey(
        Draft,
        verbose_name=_('Draft Midia'), related_name='draftmidia_set',
        on_delete=PROTECT)

    sequencia = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Sequência'),)

    created = models.DateTimeField(
        verbose_name=_('created'), editable=False, auto_now_add=True)

    arquivo = PortalFileField(
        blank=True,
        null=True,
        # storage=media_protected_storage,
        upload_to=draftmidia_path,
        verbose_name=_('Arquivo'),)
    # validators=[restringe_tipos_de_arquivo_midias])

    class Meta:
        ordering = ('sequencia',)

        verbose_name = _('Mídia')
        verbose_name_plural = _('Mídias')

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


CLASSE_ESTRUTURAL = 0
CLASSE_DOCUMENTAL = 1
CLASSE_MISTA = 2
PERFIL_CLASSE = ((
    CLASSE_ESTRUTURAL, _('Classe Estrutural')),
    (
    CLASSE_DOCUMENTAL, _('Classe de Conteúdo')),
    (
    CLASSE_MISTA, _('Classe Mista'))
)


class Parent(models.Model):

    parent = models.ForeignKey(
        'self',
        blank=True, null=True, default=None,
        related_name='childs',
        verbose_name=_('Filhos'),
        on_delete=PROTECT)

    raiz = models.ForeignKey(
        'self',
        blank=True, null=True, default=None,
        related_name='nodes',
        verbose_name=_('Containers'),
        on_delete=PROTECT)

    metadata = JSONField(
        verbose_name=_('Metadados'),
        blank=True, null=True, default=None, encoder=DjangoJSONEncoder)

    class Meta:
        abstract = True

    @property
    def parents(self):
        if not self.parent:
            return []

        parents = self.parent.parents + [self.parent, ]
        return parents

    @property
    def parents_and_me(self):
        if not self.parent:
            return [self]

        parents = self.parent.parents + [self.parent, self]
        return parents

    @property
    def classes_parents(self):

        if not hasattr(self, 'classe'):
            return self.parents

        _p = self.parents
        p = _p or [self]

        parents = p[0].classe.parents_and_me + _p
        return parents

    @property
    def classes_parents_and_me(self):

        if not hasattr(self, 'classe'):
            return self.parents_and_me

        p = self.parents_and_me

        parents = p[0].classe.parents_and_me + p
        return parents

    def treechilds2list(self):
        yield self
        for child in self.childs.view_childs():
            for item in child.treechilds2list():
                yield item

    def clean(self):

        # Check for instances with null values in unique_together fields.

        from django.core.exceptions import ValidationError

        super(CMSMixin, self).clean()

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


class ArqClasse(Parent):

    codigo = models.PositiveIntegerField(verbose_name=_('Código'), default=0)

    titulo = models.CharField(
        verbose_name=_('Título'),
        max_length=250,
        blank=True, null=True, default='')

    descricao = models.TextField(
        verbose_name=_('Descrição'),
        blank=True, null=True, default=None)

    perfil = models.IntegerField(
        _('Perfil da Classe'),
        choices=PERFIL_CLASSE,
        default=CLASSE_ESTRUTURAL)

    created = models.DateTimeField(
        verbose_name=_('created'), editable=False, auto_now_add=True)

    owner = models.ForeignKey(
        get_settings_auth_user_model(),
        verbose_name=_('owner'), related_name='+',
        on_delete=PROTECT)

    class Meta:
        ordering = ('codigo',)

        verbose_name = _('Classe')
        verbose_name_plural = _('Classes')

    @property
    def conta(self):
        ct = [str(p.codigo) for p in self.parents]
        ct.append(str(self.codigo))
        if len(ct[0]) < 3:
            ct[0] = '{:03,d}'.format(int(ct[0]))
        return '.'.join(ct)
