
from django.db import models
from django.utils.translation import gettext_lazy as _


class LexmlProvedor(models.Model):  # LexmlRegistroProvedor
    id_provedor = models.PositiveIntegerField(verbose_name=_('Id do provedor'))
    nome = models.CharField(max_length=255, verbose_name=_('Nome do provedor'))
    sigla = models.CharField(max_length=15)
    email_responsavel = models.EmailField(
        max_length=50,
        blank=True,
        verbose_name=_('E-mail do responsável'))
    nome_responsavel = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_('Nome do responsável'))
    tipo = models.CharField(max_length=50)
    id_responsavel = models.PositiveIntegerField(
        blank=True, null=True, verbose_name=_('Id do responsável'))
    xml = models.TextField(
        blank=True,
        verbose_name=_('XML fornecido pela equipe do LexML:'))

    @property
    def pretty_xml(self):
        import html
        safe_xml = html.escape(self.xml)
        return safe_xml.replace('\n', '<br/>').replace(' ', '&nbsp;')

    class Meta:
        verbose_name = _('Provedor Lexml')
        verbose_name_plural = _('Provedores Lexml')
        ordering = ['id']

    def __str__(self):
        return self.nome


class LexmlPublicador(models.Model):
    id_publicador = models.PositiveIntegerField(
        verbose_name=_('Id do publicador'))
    nome = models.CharField(
        max_length=255, verbose_name=_('Nome do publicador'))
    email_responsavel = models.EmailField(
        max_length=50,
        blank=True,
        verbose_name=_('E-mail do responsável'))
    sigla = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_('Sigla do Publicador'))
    nome_responsavel = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_('Nome do responsável'))
    tipo = models.CharField(max_length=50)
    id_responsavel = models.PositiveIntegerField(
        verbose_name=_('Id do responsável'))

    class Meta:
        verbose_name = _('Publicador Lexml')
        verbose_name_plural = _('Publicadores Lexml')
        ordering = ['id']

    def __str__(self):
        return self.nome
