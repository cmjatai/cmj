from crispy_forms.helper import FormHelper
from crispy_forms.layout import Div, Fieldset
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.deletion import PROTECT
from django.urls.base import reverse
from django.utils.translation import ugettext_lazy as _
from floppyforms import ClearableFileInput
from model_utils.choices import Choices
from pdfrw.pdfreader import PdfReader
from social_core.backends.facebook import FacebookOAuth2

from cmj.utils import run_sql, get_settings_auth_user_model,\
    YES_NO_CHOICES
from sapl.crispy_layout_mixin import to_row, SaplFormLayout,\
    form_actions


class FacebookOAuth2(FacebookOAuth2):
    STATE_PARAMETER = False
    REDIRECT_STATE = False


class ImageThumbnailFileInput(ClearableFileInput):
    template_name = 'floppyforms/image_thumbnail.html'


class CmjChoices(Choices):
    def _process(self, choices, triple_collector=None, double_collector=None):
        Choices._process(self, choices, triple_collector=triple_collector,
                         double_collector=double_collector)

        self._triple_map = {
            value: {
                'component_tag': triple.replace('_', '-'),
                'text': text
            } for value, triple, text in self._triples
        }

        self._triple_map_component = {
            triple.replace('_', '-'): {
                'id': value,
                'text': text
            } for value, triple, text in self._triples
        }

    def triple(self, value):
        return self._triple_map[value]['component_tag']

    @property
    def triple_map(self):
        return self._triple_map

    @property
    def triple_map_component(self):
        return self._triple_map_component

    def __add__(self, other):
        if isinstance(other, self.__class__):
            other = other._triples
        else:
            other = list(other)
        return CmjChoices(*(self._triples + other))

    def __radd__(self, other):
        # radd is never called for matching types, so we don't check here
        other = list(other)
        return CmjChoices(*(other + self._triples))


class BtnCertMixin:

    @property
    def extras_url(self):
        r = [self.btn_certidao('texto_integral')]
        r = list(filter(None, r))
        return r

    def btn_certidao(self, field_name):

        btn = []
        if self.object.certidao:

            btn = [
                reverse('cmj.core:certidaopublicacao_detail',
                        kwargs={'pk': self.object.certidao.pk}),
                'btn-success',
                _('Certidão de Publicação')
            ]

        elif self.request.user.has_perm('core.add_certidaopublicacao'):

            btn = [
                reverse(
                    'cmj.core:certidaopublicacao_create',
                    kwargs={
                        'pk': self.kwargs['pk'],
                        'content_type': ContentType.objects.get_for_model(
                            self.object._meta.model).id,
                        'field_name': field_name
                    }),
                'btn-primary',
                _('Gerar Certidão de Publicação')
            ]

        return btn


class CommonMixin(models.Model):

    _paginas = models.IntegerField(
        default=0, verbose_name=_('Número de Páginas'))

    FIELDFILE_NAME = ''

    class Meta:
        abstract = True

    @property
    def paginas(self):
        if not self.FIELDFILE_NAME:
            raise Exception

        if not self.id:
            raise Exception

        if self._paginas > 0:
            return self._paginas
        elif self._paginas == -1:
            return 0

        count_pages = 0
        try:
            for field in self.FIELDFILE_NAME:
                if not getattr(self, field):
                    return 0

                path = getattr(self, field).file.name

                if path.endswith('.pdf'):
                    pdf = PdfReader(path)
                    count_pages += len(pdf.pages)
                    getattr(self, field).file.close()
                elif '.doc' in path:
                    return 0

        except Exception as e:
            count_pages = -1

        finally:
            self._paginas = count_pages
            run_sql(
                """update {}
                        set _paginas = {}
                        where id = {};""".format(
                    '%s_%s' % (self._meta.app_label,
                               self._meta.model_name),
                    count_pages,
                    self.id
                ))
            if count_pages == -1:
                return 0
            return count_pages


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


class GoogleRecapthaMixin:

    def __init__(self, *args, **kwargs):

        title_label = kwargs.pop('title_label')
        action_label = kwargs.pop('action_label')

        row1 = to_row(
            [
                (Div(
                 css_class="g-recaptcha float-right",  # if not settings.DEBUG else '',
                 data_sitekey=settings.GOOGLE_RECAPTCHA_SITE_KEY
                 ), 5),
                ('email', 7),

            ]
        )

        self.helper = FormHelper()
        self.helper.layout = SaplFormLayout(
            Fieldset(
                title_label,
                row1
            ),
            actions=form_actions(label=action_label)
        )

        super().__init__(*args, **kwargs)

    def clean(self):

        super().clean()

        cd = self.cleaned_data

        recaptcha = self.data.get('g-recaptcha-response', '')
        if not recaptcha:
            raise ValidationError(
                _('Verificação do reCAPTCHA não efetuada.'))

        import urllib3
        import json

        #encoded_data = json.dumps(fields).encode('utf-8')

        url = ('https://www.google.com/recaptcha/api/siteverify?'
               'secret=%s'
               '&response=%s' % (settings.GOOGLE_RECAPTCHA_SECRET_KEY,
                                 recaptcha))

        http = urllib3.PoolManager()
        try:
            r = http.request('POST', url)
            data = r.data.decode('utf-8')
            jdata = json.loads(data)
        except Exception as e:
            raise ValidationError(
                _('Ocorreu um erro na validação do reCAPTCHA.'))

        if jdata['success']:
            return cd
        else:
            raise ValidationError(
                _('Ocorreu um erro na validação do reCAPTCHA.'))

        return cd
