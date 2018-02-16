
from django.db import models
from django.db.models import Q, F
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from cmj.utils import CmjChoices, get_settings_auth_user_model


class CMSMixin(models.Model):

    STATUS_RESTRICT = 1
    STATUS_PUBLIC = 0

    VISIBILIDADE_STATUS = CmjChoices(
        (STATUS_RESTRICT, 'status_restrict', _('Restrito')),
        (STATUS_PUBLIC, 'status_public', _('Público')),
    )

    created = models.DateTimeField(
        verbose_name=_('created'), editable=False, auto_now_add=True)

    public_date = models.DateTimeField(
        null=True, default=None,
        verbose_name=_('Data de Início de Publicação'))

    public_end_date = models.DateTimeField(
        null=True, default=None,
        verbose_name=_('Data de Fim de Publicação'))

    owner = models.ForeignKey(
        get_settings_auth_user_model(),
        verbose_name=_('owner'), related_name='+')

    descricao = models.TextField(
        verbose_name=_('Descrição'),
        blank=True, null=True, default=None)

    visibilidade = models.IntegerField(
        _('Visibilidade'),
        choices=VISIBILIDADE_STATUS,
        default=STATUS_RESTRICT)

    class Meta:
        abstract = True

    def clean(self):
        """
        Check for instances with null values in unique_together fields.
        """
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
