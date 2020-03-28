from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.urls.base import reverse
from django.utils.translation import ugettext_lazy as _
from floppyforms import ClearableFileInput
from model_utils.choices import Choices
from pdfrw.pdfreader import PdfReader
from social_core.backends.facebook import FacebookOAuth2
from cmj.utils import run_sql


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


class CountPageMixin(models.Model):

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
            raise Exception

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
                raise Exception
            return count_pages
