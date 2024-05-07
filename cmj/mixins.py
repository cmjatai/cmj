
import csv
import io
import logging

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Div, Fieldset
from django.apps import apps
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError, PermissionDenied
from django.db import models
from django.db.models.deletion import PROTECT
from django.http.response import HttpResponse, JsonResponse
from django.urls.base import reverse
from django.utils.translation import ugettext_lazy as _
from model_utils.choices import Choices
from pdfminer.high_level import extract_text
from pdfrw.pdfreader import PdfReader
from xlsxwriter.workbook import Workbook as XlsxWorkbook

from cmj.utils import run_sql, get_settings_auth_user_model, ProcessoExterno
from sapl.crispy_layout_mixin import to_row, SaplFormLayout, \
    form_actions


logger = logging.getLogger(__name__)


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


class PluginSignMixin:

    plugin_path = settings.PROJECT_DIR.child(
        'scripts').child(
        'java').child(
        'PluginSignPortalCMJ').child(
        'jar').child(
        'PluginSignPortalCMJ.jar')

    _cmd_mask = [
        'java -jar "{plugin}"',
        '{comando}',
        '"{in_file}"',
        '"{certificado}"',
        '"{password}"',
        '"{data_ocorrencia}"',
        '"{hora_ocorrencia}"',
        '"{data_comando}"',
        '"{hora_comando}"',
        '"{titulopre}"',
        '"{titulo}"',
        '"{titulopos}"',
        '{x}',
        '{y}',
        '{w}',
        '{h}',
        '"{cor}"',
        '{compression}',
        '{debug}',
    ]

    cmd_mask = ' '.join(_cmd_mask)

    def run(self, cmd=""):
        try:
            log = logger if not hasattr(self, 'logger') else self.logger
            print(cmd)
            log.info(cmd)
            p = ProcessoExterno(cmd, log)
            r = p.run(timeout=300)
            return r
        except Exception as e:
            log.error(e)
            log.error(r)


class CheckCheckMixin:

    def is_checkcheck(self):

        if not hasattr(self, 'object'):
            self.object = self.get_object()

        obj = self.object

        if hasattr(self, 'crud') and hasattr(self.crud, 'parent_field'):
            checkcheck = getattr(obj, self.crud.parent_field).checkcheck
        else:
            checkcheck = obj.checkcheck if hasattr(
                obj, 'checkcheck') else False

        return checkcheck

    def _checkcheck(self, request):
        if self.is_checkcheck() and not request.user.is_superuser:
            raise PermissionDenied(
                'Documento já no arquivo morto, '
                'a edição é restrita ao gestor do sistema!'
            )

    def get(self, request, *args, **kwargs):
        self._checkcheck(request)
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self._checkcheck(request)
        return super().post(request, *args, **kwargs)


class BtnCertMixin:

    @property
    def extras_url(self):
        r = [self.btn_certidao('texto_integral')]
        r = list(filter(None, r))
        return r

    def btn_certidao(self, field_name,
                     btn_title_public=_('Certidão de Publicação'),
                     btn_title_admin=_('Gerar Certidão de Publicação'),
                     ):

        btn = []
        if self.object.certidao:

            btn = [
                reverse('cmj.core:certidaopublicacao_detail',
                        kwargs={'pk': self.object.certidao.pk}),
                'btn-success',
                btn_title_public
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
    def extract_epigrafe(self):

        if not self.FIELDFILE_NAME:
            raise Exception

        if not self.id:
            raise Exception

        try:
            for field in self.FIELDFILE_NAME:
                if not getattr(self, field):
                    return None

                path = getattr(self, field).path
                text = extract_text(path, maxpages=1)

                text = text.split('\n')

                text = map(lambda t: t.strip(), text)
                text = map(lambda t: t.upper(), text)
                text = list(text)

                return text[0]

        except Exception as e:
            return None

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

        if clean:
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

        # encoded_data = json.dumps(fields).encode('utf-8')

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


class AudigLogFilterMixin:

    def dispatch(self, request, *args, **kwargs):
        self.log(request, *args, **kwargs)
        return super().dispatch(request, *args, **kwargs)

    def log(self, request, *args, **kwargs):

        try:
            data = request.GET or request.POST
            data = data.lists()
            md = {}
            for k, v in data:
                v = list(filter(lambda i: i, v))
                if not v or 'csrf' in k or 'salvar' in k:
                    continue

                md[k] = v[0] if len(v) == 1 else v

            if md:
                AuditLog = apps.get_model('core', 'auditlog')
                al = AuditLog()
                al.user = None if request.user.is_anonymous else request.user
                al.email = '' if request.user.is_anonymous else request.user.email
                al.operation = 'P'
                al.obj_id = 0

                if hasattr(self, 'model'):
                    al.model_name = self.model._meta.model_name
                    al.app_name = self.model._meta.app_label
                else:
                    if 'models'in md and isinstance(md['models'], str):
                        md['models'] = [md['models'], ]

                al.obj = {
                    'params': md,
                }
                try:
                    al.obj['HTTP_X_REAL_IP'] = request.META.get(
                        'HTTP_X_REAL_IP', '')
                    # logger.info(dict(request.META))
                except:
                    pass

                al.save()
        except Exception as e:
            logger.error('Error saving auditing log object')
            logger.error(e)


class MultiFormatOutputMixin:

    formats_impl = 'csv', 'xlsx', 'json'

    queryset_values_for_formats = True

    def render_to_response(self, context, **response_kwargs):

        format_result = getattr(self.request, self.request.method).get(
            'format', None)

        if format_result:
            if format_result not in self.formats_impl:
                raise ValidationError(
                    'Formato Inválido e/ou não implementado!')

            object_list = context['object_list']
            object_list.query.low_mark = 0
            object_list.query.high_mark = 0

            return getattr(self, f'render_to_{format_result}')(context)

        return super().render_to_response(context, **response_kwargs)

    def render_to_json(self, context):

        object_list = context['object_list']

        if self.queryset_values_for_formats:
            object_list = object_list.values(
                *self.fields_report['json'])

        data = []
        for obj in object_list:
            wr = list(self._write_row(obj, 'json'))

            if not data:
                data.append([wr])
                continue

            if wr[0] != data[-1][0][0]:
                data.append([wr])
            else:
                data[-1].append(wr)

        for mri, multirows in enumerate(data):
            if len(multirows) == 1:
                v = multirows[0]
            else:
                v = multirows[0]
                for ri, cols in enumerate(multirows[1:]):
                    for rc, cell in enumerate(cols):
                        if v[rc] != cell:
                            v[rc] = f'{v[rc]}\r\n{cell}'

            data[mri] = dict(
                map(lambda i, j: (i, j), self.fields_report['json'], v))

        json_metadata = {
            'headers': dict(
                map(lambda i, j: (i, j), self.fields_report['json'], self._headers('json'))),
            'results': data
        }
        response = JsonResponse(json_metadata)
        response['Content-Disposition'] = f'attachment; filename="portalcmj_{self.request.resolver_match.url_name}.json"'
        response['Cache-Control'] = 'no-cache'
        response['Pragma'] = 'no-cache'
        response['Expires'] = 0

        return response

    def render_to_csv(self, context):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="portalcmj_{self.request.resolver_match.url_name}.csv"'
        response['Cache-Control'] = 'no-cache'
        response['Pragma'] = 'no-cache'
        response['Expires'] = 0
        writer = csv.writer(response, delimiter=";",
                            quoting=csv.QUOTE_NONNUMERIC)

        object_list = context['object_list']

        if self.queryset_values_for_formats:
            object_list = object_list.values(
                *self.fields_report['csv'])

        data = [[list(self._headers('csv'))], ]
        for obj in object_list:
            wr = list(self._write_row(obj, 'csv'))
            if wr[0] != data[-1][0][0]:
                data.append([wr])
            else:
                data[-1].append(wr)

        for mri, multirows in enumerate(data):
            if len(multirows) == 1:
                writer.writerow(multirows[0])
            else:
                v = multirows[0]
                for ri, cols in enumerate(multirows[1:]):
                    for rc, cell in enumerate(cols):
                        if v[rc] != cell:
                            v[rc] = f'{v[rc]}\r\n{cell}'

                writer.writerow(v)

        return response

    def render_to_xlsx(self, context):

        object_list = context['object_list']

        if self.queryset_values_for_formats:
            object_list = object_list.values(
                *self.fields_report['xlsx'])

        data = [[list(self._headers('xlsx'))], ]
        for obj in object_list:
            wr = list(self._write_row(obj, 'xlsx'))
            if wr[0] != data[-1][0][0]:
                data.append([wr])
            else:
                data[-1].append(wr)

        output = io.BytesIO()
        wb = XlsxWorkbook(output, {'in_memory': True})

        ws = wb.add_worksheet()

        for mri, multirows in enumerate(data):
            if len(multirows) == 1:
                for rc, cell in enumerate(multirows[0]):
                    ws.write(mri, rc, cell)
            else:
                v = multirows[0]
                for ri, cols in enumerate(multirows[1:]):
                    for rc, cell in enumerate(cols):
                        if v[rc] != cell:
                            v[rc] = f'{v[rc]}\r\n{cell}'

                for rc, cell in enumerate(v):
                    ws.write(mri, rc, cell)
        ws.autofit()
        wb.close()

        output.seek(0)

        response = HttpResponse(output.read(
        ), content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        response['Content-Disposition'] = f'attachment; filename="portalcmj_{self.request.resolver_match.url_name}.xlsx"'
        response['Cache-Control'] = 'no-cache'
        response['Pragma'] = 'no-cache'
        response['Expires'] = 0

        output.close()

        return response

    def _write_row(self, obj, format_result):

        for fname in self.fields_report[format_result]:

            if hasattr(self, f'hook_{fname}'):
                v = getattr(self, f'hook_{fname}')(obj)
                yield v
                continue

            if isinstance(obj, dict):
                yield obj[fname]
                continue

            fname = fname.split('__')

            v = obj
            for fp in fname:
                v = getattr(v, fp)

            if hasattr(v, 'all'):
                v = ' - '.join(map(lambda x: str(x), v.all()))

            yield v

    def _headers(self, format_result):

        for fname in self.fields_report[format_result]:

            verbose_name = []

            if hasattr(self, f'hook_header_{fname}'):
                h = getattr(self, f'hook_header_{fname}')()
                yield h
                continue

            fname = fname.split('__')

            m = self.model
            for fp in fname:

                f = m._meta.get_field(fp)

                vn = str(f.verbose_name) if hasattr(f, 'verbose_name') else fp
                if f.is_relation:
                    m = f.related_model
                    if m == self.model:
                        m = f.field.model

                    if vn == fp:
                        vn = str(m._meta.verbose_name_plural)
                verbose_name.append(vn.strip())

            verbose_name = '/'.join(verbose_name).strip()
            yield f'{verbose_name}'
