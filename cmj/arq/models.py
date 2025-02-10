from time import sleep
import glob
import logging
import os
import pathlib
import re
import shutil

from unipath import Path

from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from django.db.models.deletion import PROTECT, CASCADE
from django.db.models.fields.json import JSONField
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from cmj.mixins import CmjAuditoriaModelMixin, CommonMixin
from cmj.utils import get_settings_auth_user_model, texto_upload_path, normalize
from sapl.utils import PortalFileField


logger = logging.getLogger(__name__)


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

    def __str__(self):
        return self.descricao

    def delete(self, using=None, keep_parents=False):
        root_path = Path(
            settings.MEDIA_ROOT,
            f'cmj/private/draftmidia/{self.owner.id}/{self.id}/'
            )
        remove_files_and_folders(os.path.dirname(root_path))
        return models.Model.delete(self, using=using, keep_parents=keep_parents)


def remove_files_and_folders(directory):

    list_elements = []
    try:
        list_elements = glob.glob(f'{directory}/**', recursive=True)
        list_elements_ocult = glob.glob(f'{directory}/.*', recursive=True)
        list_elements.extend(list_elements_ocult)
        list_elements.sort(reverse=True)
    except Exception as e:
        logger.error(f'Erro ao listar elementos de: {directory}. {e}')
        return

    for f in list_elements:
        try:
            if os.path.isfile(f):
                os.remove(f)
            elif os.path.isdir(f):
                os.rmdir(f)
        except Exception as e:
            logger.error(f'Erro na exclusão de: {f}. {e}')


def draftmidia_path(instance, filename):

    filename = re.sub(r'\s', '_', normalize(filename.strip()).lower())
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

    METADATA_PDFA_NONE = 0
    METADATA_PDFA_AGND = 10
    METADATA_PDFA_PROC = 20
    METADATA_PDFA_PDFA = 99

    metadata = JSONField(
        verbose_name=_('Metadados'),
        blank=True, null=True, default=None, encoder=DjangoJSONEncoder)

    draft = models.ForeignKey(
        Draft,
        verbose_name=_('Draft Midia'), related_name='draftmidia_set',
        on_delete=CASCADE)

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
        verbose_name=_('Arquivo'),
        max_length=512)
    # validators=[restringe_tipos_de_arquivo_midias])

    class Meta:
        ordering = ('draft', 'sequencia',)

        verbose_name = _('Mídia')
        verbose_name_plural = _('Mídias')

    def delete(self, using=None, keep_parents=False):
        if self.arquivo:
            self.clear_cache()
            self.arquivo.delete()

        return models.Model.delete(self, using=using, keep_parents=keep_parents)

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):

        if not self.pk and self.arquivo:
            self.clear_cache()
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

    def clear_cache(self, page=None):
        try:
            fcache = glob.glob(
                f'{self.arquivo.path}-p{page:0>3}*'
                if page else f'{self.arquivo.path}*.png'
            )

            for f in fcache:
                os.remove(f)
        except Exception as e:
            logger.error(f'Erro ao limpar cache de: {self.arquivo.path}. {e}')


ARQCLASSE_FISICA = 100
ARQCLASSE_LOGICA = 200
PERFIL_ARQCLASSE = ((
    ARQCLASSE_FISICA, _('Classe de Localização Física')),
    (
    ARQCLASSE_LOGICA, _('Classe de Organização Lógica')),
)

mask_conta = ['{:03}', '{:02}', '{:02}', '{:02}', '{:01}']


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
        verbose_name=_('Raiz'),
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

        super(Parent, self).clean()

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

    checkcheck = models.BooleanField(
        verbose_name=_('Arquivado'), default=False)

    render_tree2 = models.BooleanField(
        verbose_name=_('Renderização em Tree2'), default=False)

    can_arqdoc = models.BooleanField(
        verbose_name=_('Permitir Adição de ArqDoc'), default=False)

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
        choices=PERFIL_ARQCLASSE,
        default=ARQCLASSE_FISICA)

    created = models.DateTimeField(
        verbose_name=_('created'), editable=False, auto_now_add=True)

    owner = models.ForeignKey(
        get_settings_auth_user_model(),
        verbose_name=_('owner'), related_name='+',
        on_delete=PROTECT)

    class Meta:
        ordering = ('codigo',)

        verbose_name = _('ArqClasse')
        verbose_name_plural = _('ArqClasses')

    @property
    def conta(self):
        ct = [str(p.codigo) for p in self.parents]
        ct.append(str(self.codigo))

        while len(mask_conta) < len(ct):
            mask_conta.append(mask_conta[-1])

        for i, c in enumerate(ct):
            ct[i] = mask_conta[i].format(int(c))
        return '.'.join(ct)

    @property
    def nivel(self):
        parents = self.parents
        return len(parents)

    @property
    def strparents(self):
        if not self.parent:
            return []

        parents = self.parent.strparents + [self.parent.titulo, ]
        return parents

    @property
    def parents(self):
        if not self.parent:
            return []

        parents = self.parent.parents + [self.parent, ]
        return parents

    def __str__(self):
        parents = self.strparents
        parents.append(self.titulo)

        return ' : '.join(parents)

    def arqdoc_set(self):
        if self.perfil == ARQCLASSE_FISICA:
            return self.arqdoc_estrutural_set
        elif self.perfil == ARQCLASSE_LOGICA:
            return self.arqdoc_logica_set
        else:
            return self.arqdoc_logica_set.none()

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):

        r = super().save(force_insert=force_insert, force_update=force_update,
                         using=using, update_fields=update_fields)

        if self.checkcheck:
            for c in self.childs.all():
                c.checkcheck = True
                c.save(update_fields=('checkcheck', ))

            for d in self.arqdoc_set().all():
                d.checkcheck = True
                d.save(update_fields=('checkcheck', ))
        else:
            if self.parent:
                self.parent.checkcheck = False
                self.parent.save()

        return r


def arqdoc_path(instance, filename):

    filename = re.sub(r'\s', '_', normalize(filename.strip()).lower())
    filename = filename.split('.')

    filename = '' if len(filename[-1]) > 4 else f'.{filename[-1]}'

    str_path = (
        './cmj/private/%(model_name)s/%(classe_estrutural)s/%(arqdoc)s/%(filename)s')

    path = str_path % \
        {
            'model_name': instance._meta.model_name,
            'classe_estrutural': instance.classe_estrutural.id,
            'arqdoc': instance.id,
            'filename': f'{instance.id:09}{filename}'
        }

    return path


class ArqDoc(CommonMixin, Parent, CmjAuditoriaModelMixin):

    FIELDFILE_NAME = ('arquivo',)

    checkcheck = models.BooleanField(
        verbose_name=_('Arquivado?'), default=False)

    editado = models.BooleanField(
        verbose_name=_('Editado Manualmente?'), default=False)

    codigo = models.PositiveIntegerField(verbose_name=_('Código'), default=0)

    titulo = models.CharField(
        verbose_name=_('Título'),
        max_length=250,)

    descricao = models.TextField(
        verbose_name=_('Descrição'),)

    data = models.DateField(
        verbose_name=_('Data do Documento'),)

    arquivo = PortalFileField(
        blank=True,
        null=True,
        # storage=media_protected_storage,
        upload_to=arqdoc_path,
        verbose_name=_('Arquivo'),
        max_length=512)

    classe_logica = models.ForeignKey(
        ArqClasse,
        verbose_name=_('Classificação Lógica'),
        related_name='arqdoc_logica_set',
        blank=True, null=True, default=None,
        on_delete=PROTECT)

    classe_estrutural = models.ForeignKey(
        ArqClasse,
        verbose_name=_('Classificação Estrutural'),
        related_name='arqdoc_estrutural_set',
        on_delete=PROTECT)

    class Meta:
        ordering = ('codigo',)

        verbose_name = _('ArqDoc')
        verbose_name_plural = _('ArcDocs')

    @property
    def conta_classe_logica(self):
        return self.classe_logica.conta

    @property
    def conta_classe_estrutural(self):
        return self.classe_estrutural.conta

    @property
    def conta_logica(self):
        ct = [self.classe_logica.conta, ]
        ct.append(str(self.codigo))
        return '.'.join(ct)

    @property
    def conta_estrutural(self):
        ct = [self.classe_estrutural.conta, ]
        ct.append(str(self.codigo))
        return '.'.join(ct)

    @property
    def conta(self):
        ct = [self.classe_logica.conta, ]
        ct.append(str(self.codigo))
        return '.'.join(ct)

    def __str__(self):
        return self.titulo or ''

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
