from _collections import OrderedDict
from decimal import Decimal
import logging

from django.apps.registry import apps
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.validators import RegexValidator
from django.db.models import Q, F
from django.db.models.aggregates import Sum
from django.db.models.functions import Substr
from django.http.response import HttpResponse
from django.template.loader import render_to_string
from django.utils import formats
from django.utils.datastructures import OrderedSet
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.fields import RegexField, DecimalField, CharField, \
    SerializerMethodField
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet
import pymupdf

from cmj import loa
from cmj.loa.models import OficioAjusteLoa, EmendaLoa, Loa, EmendaLoaParlamentar, \
    DespesaConsulta, EmendaLoaRegistroContabil, UnidadeOrcamentaria, Despesa, \
    Orgao, Funcao, SubFuncao, Programa, Acao, Natureza,\
    AgrupamentoRegistroContabil, AgrupamentoEmendaLoa, Agrupamento, quantize
from cmj.utils import run_sql
from drfautoapi.drfautoapi import ApiViewSetConstrutor, customize,\
    wrapper_queryset_response_for_drf_action
from sapl.api.mixins import ResponseFileMixin
from sapl.api.permissions import SaplModelPermissions
from sapl.api.serializers import SaplSerializerMixin
from sapl.parlamentares.models import Parlamentar
from sapl.relatorios.views import make_pdf


logger = logging.getLogger(__name__)

ApiViewSetConstrutor.build_class(
    [
        apps.get_app_config('loa')
    ]
)


@customize(SubFuncao)
class _SubFuncaoViewSet:

    def get_queryset(self, *args, **kwargs):
        qs = super().get_queryset(*args, **kwargs)

        qp = self.request.query_params
        if 'despesa_set__isnull' in qp:
            dsisnull = qp['despesa_set__isnull'] == 'true'
            qs = qs.filter(despesa_set__isnull=dsisnull).order_by(
                'codigo').distinct()

        return qs


filters_base = [
    ('orgao', Orgao),
    ('unidade', UnidadeOrcamentaria),
    ('funcao', Funcao),
    ('subfuncao', SubFuncao),
    ('programa', Programa),
    ('acao', Acao),
    ('natureza_1', Natureza),
    ('natureza_2', Natureza),
    ('natureza_3', Natureza),
    ('natureza_4', Natureza),
    ('natureza_5', Natureza),
]
dict_filter_base = dict(filters_base)


@customize(Loa)
class _LoaViewSet:

    class LoaPermission(SaplModelPermissions):
        def has_permission(self, request, view):
            has_perm = super().has_permission(request, view)

            if has_perm:
                return has_perm

            u = request.user

            if request.method == 'POST' and view.action in (
                'despesas_agrupadas',
            ):
                return True

            if request.method == 'GET' and view.action == 'retrieve':
                self.object = view.get_object()
                if not self.object.publicado and u.is_anonymous:
                    return False
                return True
            # elif request.method == 'GET' and view.action == 'despesas_executadas':
            #    return True

            return False

    permission_classes = (LoaPermission, )

    @action(methods=['get', ], detail=True)
    def despesas_executadas(self, request, *args, **kwargs):
        ano = kwargs['pk']
        result = run_sql(f"""SELECT
                q1.cod as orgao,
                q1.especificacao,
                q1.valor as val_orc,
                q2.valor as val_exe,
                q3.valor as val_rec_orc,
                to_char(q2.data_max, 'DD/MM/YYYY') as data_max,
                q2.codigo_max

            FROM (
                SELECT
                    lo.codigo as cod,
                    lo.especificacao as especificacao,
                    SUM(ldo.valor_materia) as valor
                FROM loa_orgao lo
                    LEFT JOIN loa_despesa ldo ON (ldo.orgao_id = lo.id)
                    INNER JOIN loa_loa ll ON (lo.loa_id = ll.id)
                WHERE ll.ano = {ano}
                    group by cod, especificacao
                    ORDER BY cod, especificacao
                ) q1
                LEFT JOIN (
                    SELECT
                        lo.codigo as cod,
                        lo.especificacao as especificacao,
                        SUM(ldp.valor) as valor,
                        MAX(ldp.data) as data_max,
                        MAX(ldp.codigo) as codigo_max
                    FROM loa_orgao lo
                        LEFT JOIN loa_despesapaga ldp ON (ldp.orgao_id = lo.id)
                        INNER JOIN loa_loa ll ON (lo.loa_id = ll.id)
                    WHERE ll.ano = {ano}
                        group by cod, especificacao
                        ORDER BY cod, especificacao
                ) q2 on (q1.cod = q2.cod)
                LEFT JOIN (
                    SELECT
                        lo.codigo as cod,
                        lo.especificacao as especificacao,
                        SUM(
                            CASE WHEN lro.codigo like '9%' then -lra.valor else lra.valor end
                            ) as valor
                    FROM loa_orgao lo
                        LEFT JOIN loa_receitaorcamentaria lro ON (lro.orgao_id = lo.id)
                        LEFT JOIN loa_receitaarrecadada lra ON (lra.receita_id = lro.id)
                        INNER JOIN loa_loa ll ON (lo.loa_id = ll.id)
                    WHERE ll.ano = {ano}
                        group by cod, especificacao
                        ORDER BY cod, especificacao
                ) q3 on (q1.cod = q3.cod)
                order by q2.valor desc nulls last;
        """)

        return Response(result)

    @action(methods=['post', ], detail=True)
    def despesas_agrupadas(self, request, *args, **kwargs):
        loa_id = kwargs['pk']

        filters_data = request.data

        try:
            itens = filters_data.pop('itens')
            itens = min(25, int(itens))

            hist = filters_data.pop('hist')
            hist = int(hist)
        except:
            itens = 20
            hist = 0

        grup_str = filters_data.pop('agrupamento')
        agrup = {}

        if 'natureza' not in grup_str:
            agrup['codigo'] = F(f'{grup_str}__codigo')
            # agrup['especificacao'] = F(f'{grup_str}__especificacao')
            order_by = [f'{grup_str}__codigo']

            if grup_str == 'unidade':
                agrup['orgao__codigo'] = F('orgao__codigo')
                order_by.insert(0, 'orgao__codigo')
                pass
        else:
            ndict = {
                1: 1,
                2: 3,
                3: 6,
                4: 9,
                5: 12
            }
            nivel = int(grup_str.split('_')[1])

            agrup['codigo'] = Substr(f'natureza__codigo', 1, ndict[nivel])
            order_by = ['natureza__codigo']

        agrup['ano'] = F('loa__ano')
        order_by.insert(0, '-loa__ano')

        f_unidade = filters_data.get('unidade', None)
        if f_unidade:
            ucod = f_unidade.split('/')
            filters_data['unidade'] = ucod[0]

        filters = {
            f'{k}__codigo': v
            for k, v in filters_data.items() if v and k in dict_filter_base
        }
        filters['loa_id'] = loa_id

        if f_unidade:
            filters['unidade__orgao_id'] = ucod[1]

        if hist:
            filters.pop('loa_id')

        rs = list(Despesa.objects.filter(**filters).values(
            **agrup
        ).order_by(
            *order_by
        ).annotate(
            vm=Sum('valor_materia'),
            vn=Sum('valor_norma'),
            alt=Sum('registrocontabil_set__valor')))

        r = []
        r_anual = OrderedDict()
        labels = {}
        for i in rs:
            ano = i['ano']
            if ano not in r_anual:
                r_anual[ano] = []

            i.pop('ano')
            try:
                codigo_unico = f'{i["codigo"]}/{i["orgao__codigo"] if "orgao__codigo" in i else ""}'
                if codigo_unico not in labels:
                    params = {
                        'loa__ano': ano,
                        f'codigo{"__startswith" if "natureza" in grup_str else ""}': i['codigo']
                    }
                    if 'orgao__codigo' in i:
                        params['orgao__codigo'] = i['orgao__codigo']

                    i['especificacao'] = dict_filter_base[grup_str].objects.filter(
                        **params
                    ).values_list('especificacao', flat=True).first()
                    labels[codigo_unico] = i['especificacao']
                else:
                    i['especificacao'] = labels[i['codigo']]

            except:
                i['especificacao'] = ''
            r_anual[ano].append(i)

        for ano, rs in r_anual.items():

            if 'natureza' not in grup_str:
                r = rs
            else:
                r = {}
                for i in rs:
                    nat = i['codigo']
                    if nat not in r:
                        r[nat] = i
                        r[nat]['vm'] = i['vm'] or Decimal('0.00')
                        r[nat]['vn'] = i['vn'] or Decimal('0.00')
                        r[nat]['alt'] = i['alt'] or Decimal('0.00')
                        continue

                    r[nat]['vm'] += i['vm'] or Decimal('0.00')
                    r[nat]['vn'] += i['vn'] or Decimal('0.00')
                    r[nat]['alt'] += i['alt'] or Decimal('0.00')
                r = r.values()

                for i in r:
                    cod = i['codigo']
                    cod = cod.split('.')
                    while len(cod) < 5:
                        cod.append('0' * 2 if len(cod) > 1 else '0')
                    cod = '.'.join(cod)
                    nat = Natureza.objects.filter(
                        loa_id=loa_id, codigo=cod).first()
                    i['especificacao'] = nat.especificacao if nat else ''

            soma = sum(map(lambda x: x['vm'], r))

            r = sorted(r, key=lambda x: -x['vm'])

            if not hist:
                outros = r[itens:] if itens else []
                r = r[:itens] if itens else r

                if outros:
                    outros[0]['vm'] = outros[0]['vm'] or Decimal('0.00')
                    outros[0]['vn'] = outros[0]['vn'] or Decimal('0.00')
                    outros[0]['alt'] = outros[0]['alt'] or Decimal('0.00')

                    for idx, item in enumerate(outros):
                        if idx:
                            outros[0]['vm'] += item['vm'] or Decimal('0.00')
                            outros[0]['vn'] += item['vn'] or Decimal('0.00')
                            outros[0]['alt'] += item['alt'] or Decimal('0.00')

                    outros[0]['codigo'] = ' ' * len(outros[0]['codigo'])
                    outros[0]['especificacao'] = 'OUTROS'
                    r.append(outros[0])

                for idx, item in enumerate(r):
                    esp = item['especificacao']
                    vm = formats.number_format(item['vm'], force_grouping=True)
                    while len(vm) < 14:
                        vm = f' {vm}'
                    item['especificacao'] = f'{esp}'
                    r[idx]['vm_str'] = vm
                    r[idx]['vp'] = int((item['vm'] / soma) * 100)

                    r[idx]['vm_soma'] = formats.number_format(
                        soma, force_grouping=True)

            r_anual[ano] = r

        if hist:
            os_esp = OrderedSet()
            new_r_anual = {}

            for ano, items in r_anual.items():
                new_r_anual[ano] = []
                codigos = map(
                    lambda i: f'{i["codigo"]}/{i["orgao__codigo"] if "orgao__codigo" in i else ""}',
                    items)
                for cod in codigos:
                    os_esp.add(cod)
            #os_esp = os_esp - {'  '}
            #os_esp = os_esp.union(['  '])
            len_osesp = len(os_esp)

            ks_esp = dict(zip(os_esp, range(len_osesp)))

            for ano in r_anual.keys():
                new_r_anual[ano] = [{}] * len_osesp

            for ano, items in r_anual.items():
                for item in items:
                    codigo_unico = f'{item["codigo"]}/{item["orgao__codigo"] if "orgao__codigo" in item else ""}'
                    new_r_anual[ano][ks_esp[codigo_unico]] = item
            anos = list(new_r_anual.keys())
            anos.reverse()
            labels = [f'{c.split("/")[0]}-{labels[c]}' for c in list(os_esp)]
            r_anual = {
                'labels': labels,
                'anos': anos,
                'pre_datasets': new_r_anual
            }

        r_anual = dict(r_anual)

        return Response(r_anual if hist else r)


@customize(OficioAjusteLoa)
class _OficioAjusteLoaViewSet(ResponseFileMixin):

    def custom_filename(self, item):
        arcname = '{}-{}.{}'.format(
            item.loa.ano,
            slugify(item.epigrafe),
            item.arquivo.path.split('.')[-1])
        return arcname

    @action(detail=True)
    def arquivo(self, request, *args, **kwargs):
        return self.response_file(request, *args, **kwargs)


class EmendaLoaSearchSerializer(SaplSerializerMixin):

    str_valor = SerializerMethodField()
    str_parlamentares = SerializerMethodField()

    str_fase = SerializerMethodField()

    class Meta(SaplSerializerMixin.Meta):
        model = EmendaLoa

    def get_str_fase(self, obj):
        return obj.get_fase_display()

    def get_str_valor(self, obj):
        return formats.number_format(obj.valor, force_grouping=True)

    def get_str_parlamentares(self, obj):
        elps = obj.emendaloaparlamentar_set.all()

        r = []
        for elp in elps:
            r.append(str(elp))
        return r


class EmendaLoaSerializer(SaplSerializerMixin):

    class Meta(SaplSerializerMixin.Meta):
        model = EmendaLoa

    def validate_valor(self, obj, *args, **kwargs):

        obj = obj or '0.00'

        try:
            if obj and '.' in obj and ',' in obj:
                if obj.rindex(',') > obj.rindex('.'):
                    obj = obj.replace('.', '').replace(',', '.')
                else:
                    obj = obj.replace(',', '')
            elif obj and ',' in obj:
                obj = obj.replace(',', '.')

            obj = Decimal(obj)
        except:
            raise DRFValidationError(
                _('O campo "Valor Global da Emenda" deve ser prenchido e '
                  'seguir o formado 999.999.999,99. ')
            )

        if obj == Decimal('0.00'):
            raise DRFValidationError(
                _('O campo "Valor Global da Emenda" deve ser prenchido e '
                  'seguir o formado 999.999.999,99. '))

        return obj


@customize(EmendaLoa)
class _EmendaLoaViewSet:

    class EmendaLoaPermission(SaplModelPermissions):
        def has_permission(self, request, view):
            has_perm = super().has_permission(request, view)

            if has_perm:
                return has_perm

            u = request.user
            if u.is_anonymous:
                return False

            method = request.method.lower()
            if hasattr(self, f'has_permission_{method}'):
                return getattr(self, f'has_permission_{method}')(u)

            if request.method == 'POST':

                data = request.data

                if 'loa' in data:
                    loa = Loa.objects.get(pk=data['loa'])

                if not has_perm:
                    return u.operadorautor_set.exists() and not loa.publicado

            elif request.method == 'PATCH':

                el = EmendaLoa.objects.get(pk=view.kwargs['pk'])

                participa = False
                fase = True
                if u.operadorautor_set.exists():
                    parlamentar = u.operadorautor_set.first().autor.autor_related
                    if isinstance(parlamentar, Parlamentar):
                        participa = el.emendaloaparlamentar_set.filter(
                            parlamentar=parlamentar).exists()

                        if el.fase > EmendaLoa.PROPOSTA_LIBERADA:
                            fase = False

                return (
                    u.has_perm('loa.emendaloa_full_editor') and
                    not el.materia
                ) or (
                    u.operadorautor_set.exists() and
                    not el.materia and
                    participa and
                    fase
                )

            return False

    permission_classes = (EmendaLoaPermission, )

    @action(methods=['patch', ], detail=True)
    def update_parlassinantes(self, request, *args, **kwargs):

        data = request.data
        data['emendaloa_id'] = kwargs['pk']
        dchecked = data.pop('checked')

        el = EmendaLoa.objects.get(pk=kwargs['pk'])

        pselected = el.loa.parlamentares.filter(
            id=data['parlamentar_id']).first()
        if not dchecked:
            u = request.user
            if not u.is_superuser and u.operadorautor_set.exists():
                puser = u.operadorautor_set.first().autor.autor_related

                if puser == pselected:
                    raise DRFValidationError(
                        'Você não pode remover o Parlamentar '
                        'ao qual seu usuário está ligado. '
                        'Caso queira, você pode excluir esse registro '
                        'clicando em excluir na tela de consulta.')
            el.parlamentares.remove(pselected)
        else:
            el.parlamentares.add(pselected)
        el.atualiza_valor()

        serializer = self.get_serializer(el)
        return Response(serializer.data)

    @action(methods=['patch', ], detail=True)
    def updatevaloremenda(self, request, *args, **kwargs):
        #instance = self.get_object()

        data = request.data
        obj = data.pop('valor')
        try:
            if obj and '.' in obj and ',' in obj:
                if obj.rindex(',') > obj.rindex('.'):
                    obj = obj.replace('.', '').replace(',', '.')
                else:
                    obj = obj.replace(',', '')
            elif obj and ',' in obj:
                obj = obj.replace(',', '.')

            obj = Decimal(obj)
        except:
            obj = Decimal('0.01')

        el = EmendaLoa.objects.get(pk=kwargs['pk'])
        el.valor = obj
        el.save()
        el.atualiza_valor()

        serializer = self.get_serializer(el)
        return Response(serializer.data)

    @action(methods=['patch', ], detail=True)
    def updatevalorparlamentar(self, request, *args, **kwargs):
        #instance = self.get_object()

        data = request.data
        data['emendaloa_id'] = kwargs['pk']
        obj = data.pop('valor')
        try:
            if obj and '.' in obj and ',' in obj:
                if obj.rindex(',') > obj.rindex('.'):
                    obj = obj.replace('.', '').replace(',', '.')
                else:
                    obj = obj.replace(',', '')
            elif obj and ',' in obj:
                obj = obj.replace(',', '.')

            obj = Decimal(obj)
        except:
            obj = Decimal('0.00')

        u = request.user
        if not u.is_superuser and u.operadorautor_set.exists():
            p = u.operadorautor_set.first().autor.autor_related

            if p.id == int(data['parlamentar_id']) and obj <= Decimal('0.00'):
                raise DRFValidationError(
                    'Você não pode zerar o Valor do Parlamentar '
                    'ao qual seu usuário está ligado. '
                    'Caso queira, você pode excluir esse registro '
                    'clicando em excluir na tela de consulta.')

        elp, created = EmendaLoaParlamentar.objects.get_or_create(**data)
        elp.valor = obj
        elp.save()
        el = elp.emendaloa

        if not elp.valor:
            elp.delete()

        el.atualiza_valor()

        serializer = self.get_serializer(el)

        return Response(serializer.data)

    @property
    def art(self):
        if not hasattr(self, '_art'):
            self._art = 0

        self._art += 1
        return self._art

    @action(detail=True)
    def view(self, request, *args, **kwargs):
        #base_url = settings.MEDIA_ROOT if settings.DEBUG else request.build_absolute_uri()
        base_url = request.build_absolute_uri()

        el = self.get_object()

        if 'style' not in el.metadata:
            el.metadata['style'] = {'lineHeight': 150}
            el.save()

        if 'lineHeight' in request.GET:
            lineHeight = float(el.metadata['style']['lineHeight'])
            lineHeight = min(
                300, int(request.GET.get('lineHeight', lineHeight)))
            lineHeight = max(100, lineHeight)

            if lineHeight != el.metadata['style']['lineHeight']:
                el.metadata['style']['lineHeight'] = lineHeight
                el.save()

        context = {
            'view': self,
            'object': el,
            'lineHeight': str(el.metadata['style']['lineHeight'] / 100.0)
        }

        template = render_to_string('loa/pdf/emendaloa_preview.html', context)
        pdf_file = make_pdf(base_url=base_url, main_template=template)
        doc = pymupdf.Document(stream=pdf_file)

        try:
            p = int(request.GET.get('page', 0))
        except:
            p = 0

        d2b = doc
        ext = 'pdf'
        if p:
            ext = 'png'
            p -= 1
            page = doc[p % len(doc)]
            d2b = page.get_pixmap(dpi=300)

        bresponse = d2b.tobytes()
        doc.close()

        response = HttpResponse(
            bresponse,
            content_type='image/png' if p else 'application/pdf'
        )
        response['Content-Disposition'] = f'inline; filename="emenda_{el.id}.{ext}"'
        response['Cache-Control'] = 'no-cache'
        response['Pragma'] = 'no-cache'
        response['Expires'] = 0
        return response

        # if 'docx' in request.GET:
        #    cv = Converter(stream=bresponse)
        #    output = io.BytesIO()
        #    br = cv.convert(output)
        #    cv.close()
        #    output.seek(0)
        # return HttpResponse(output.read(), content_type='application/docx')

    @action(methods=['get', ], detail=True)
    def totais(self, request, *args, **kwargs):
        r = self.get_object().totais_contabeis
        r = {k: formats.number_format(v, force_grouping=True)
             for k, v in r.items()}

        return Response(r)

    @action(detail=False)
    def search(self, request, *args, **kwargs):

        def filter_queryset(qs):
            ano = request.GET.get('ano', None)
            query = request.GET.get('q', '')
            query = query.split(' ')

            q = Q()

            for termo in query:
                q &= (Q(unidade__especificacao__icontains=termo) |
                      Q(finalidade__icontains=termo))

            qs = qs.filter(fase__lt=EmendaLoa.LIBERACAO_CONTABIL, loa__ano=ano)
            if query:
                qs = qs.filter(q)

            return qs.order_by('-fase')
        self.serializer_class = EmendaLoaSearchSerializer
        self.filter_queryset = filter_queryset

        return self.list(request, *args, **kwargs)


class DespesaConsultaSerializer(SaplSerializerMixin):

    str_valor = SerializerMethodField()
    str_saldo = SerializerMethodField()

    class Meta(SaplSerializerMixin.Meta):
        model = DespesaConsulta

    def get_str_valor(self, obj):
        return formats.number_format(obj.valor_materia, force_grouping=True)

    def get_str_saldo(self, obj):
        valor = obj.valor_materia or Decimal('0.00')

        regs = EmendaLoaRegistroContabil.objects.filter(
            despesa_id=obj.id).aggregate(soma=Sum('valor'))
        saldo = valor + (regs['soma'] or Decimal('0.00'))

        return formats.number_format(saldo, force_grouping=True)


@customize(DespesaConsulta)
class _DespesaConsulta:

    serializer_class = DespesaConsultaSerializer

    @action(detail=False)
    def search(self, request, *args, **kwargs):

        def filter_queryset(qs):
            ano = request.GET.get('ano', None)
            query = request.GET.get('q', '')
            query = query.split(' ')

            q = Q()

            for termo in query:
                q &= (Q(codigo__icontains=termo) |
                      Q(especificacao__icontains=termo) |
                      Q(esp_orgao__icontains=termo) |
                      Q(esp_unidade__icontains=termo) |
                      Q(cod_natureza__icontains=termo))

            qs = qs.filter(loa__ano=ano)
            if query:
                qs = qs.filter(q)

            return qs
        self.filter_queryset = filter_queryset

        return self.list(request, *args, **kwargs)


class EmendaLoaRegistroContabilSerializer(SaplSerializerMixin):

    class RegexLocalField(CharField):
        def __init__(self, regex, **kwargs):
            super().__init__(**kwargs)
            self.validator = RegexValidator(
                regex, message=self.error_messages['invalid'])
            self.validators.append(self.validator)

    codigo = RegexLocalField(
        r'(?P<funcao>\d{2})\.(?P<subfuncao>\d{3})'
        r'\.(?P<programa>\d{4})\.(?P<acao>\d\.[X0-9]{3})$', error_messages={
            'invalid': _('O campo "Código" deve serguir o padrão "99.999.9999.9.XXX". Onde, em "XXX" pode ser utilizado números ou a letra X')})

    natureza = RegexLocalField(r'^(\d{1,2}\.\d{1,2}\.\d{2}\.\d{2}\.[X0-9]{2})$', error_messages={
        'invalid': _('O campo "Natureza" deve serguir o padrão "x9.x9.99.99.XX". Sendo "x" numérico e opcional. Em "XX" pode ser utilizado números ou a letra X.')})

    unidade = RegexLocalField(r'^(\d{2})$', error_messages={
        'invalid': _('O campo "Unidade Orçamentária" deve serguir o padrão "99".')})

    orgao = RegexLocalField(r'^(\d{2})$', error_messages={
        'invalid': _('O campo "Órgão" deve serguir o padrão "99".')})

    valor = CharField(required=False, error_messages={
        'blank': _('O campo "Valor da Despesa" deve ser prenchido e seguir o formado 999.999.999,99. Valores negativos serão direcionados ao Art. 1º, valores positivos ao Art. 2º.'),
    })

    especificacao = CharField()

    class Meta:
        model = EmendaLoaRegistroContabil
        fields = (
            '__str__',
            'id',
            'emendaloa',
            'despesa',
            'codigo',
            'orgao',
            'unidade',
            'especificacao',
            'natureza',
            'valor'
        )

    def __init__(self, *args, **kwargs):
        return super().__init__(*args, **kwargs)

    def validate(self, attrs):
        loa_id = attrs['emendaloa'].loa_id

        codigo = self.fields.fields['codigo'].validator.regex.match(
            attrs['codigo']).groupdict()

        if not Orgao.objects.filter(codigo=attrs['orgao'], loa_id=loa_id).exists():
            raise DRFValidationError('Órgão não encontrado nos anexos da LOA.')

        if not UnidadeOrcamentaria.objects.filter(
                codigo=attrs['unidade'],
                orgao__codigo=attrs['orgao'],
                loa_id=loa_id
        ).exists():
            raise DRFValidationError(
                'Unidade Orçamentária no Órgão informado não encontrada '
                'nos anexos da LOA.')

        if not Funcao.objects.filter(codigo=codigo['funcao'], loa_id=loa_id).exists():
            raise DRFValidationError(
                'Função não encontrada na base de funções.'
            )

        if not SubFuncao.objects.filter(
                codigo=codigo['subfuncao'],
                loa_id=loa_id
        ).exists():
            raise DRFValidationError(
                'SubFunção não encontrada na base de subfunções.'
            )

        return attrs

    def validate_valor(self, obj, *args, **kwargs):

        obj = obj or '0.00'

        try:
            if obj and '.' in obj and ',' in obj:
                if obj.rindex(',') > obj.rindex('.'):
                    obj = obj.replace('.', '').replace(',', '.')
                else:
                    obj = obj.replace(',', '')
            elif obj and ',' in obj:
                obj = obj.replace(',', '.')

            obj = Decimal(obj)
        except:
            raise DRFValidationError(
                _('O campo "Valor da Despesa" deve ser prenchido e '
                  'seguir o formado 999.999.999,99. '
                  'Valores negativos serão direcionados ao Art. 1º, '
                  'valores positivos ao Art. 2º.')
            )

        if obj == Decimal('0.00'):
            raise DRFValidationError(
                'Valor da Despesa deve ser preenchido. '
                'Valores negativos serão lançados no Art. 1º, '
                'e valores positivos no Art. 2º.')

        return obj

    def create(self, validated_data):
        despesa = validated_data.get('despesa', None)

        v = validated_data
        if not despesa:
            loa_id = v['emendaloa'].loa_id

            codigo = self.fields.fields['codigo'].validator.regex.match(
                v['codigo']).groupdict()

            unidade = UnidadeOrcamentaria.objects.filter(
                codigo=v['unidade'], orgao__codigo=v['orgao'], loa_id=loa_id
            ).first()

            funcao = Funcao.objects.filter(
                codigo=codigo['funcao'], loa_id=loa_id
            ).first()

            subfuncao = SubFuncao.objects.filter(
                codigo=codigo['subfuncao'], loa_id=loa_id
            ).first()

            programa, created = Programa.objects.get_or_create(
                codigo=codigo['programa'], loa_id=loa_id
            )

            acao, created = Acao.objects.get_or_create(
                codigo=codigo['acao'], loa_id=loa_id
            )
            if created:
                acao.especificacao = v['especificacao']
                acao.save()

            natureza, created = Natureza.objects.get_or_create(
                codigo=v['natureza'], loa_id=loa_id
            )

            d = Despesa()
            d.loa = v['emendaloa'].loa
            d.orgao = unidade.orgao
            d.unidade = unidade
            d.funcao = funcao
            d.subfuncao = subfuncao
            d.programa = programa
            d.acao = acao
            d.natureza = natureza

            ddict = d.__dict__
            ddict.pop('id')
            ddict.pop('_state')
            despesa, created = Despesa.objects.get_or_create(**ddict)

        validated_data = {
            'despesa': despesa,
            'emendaloa': v['emendaloa'],
            'valor': v['valor']
        }

        elrc = EmendaLoaRegistroContabil()
        elrc.emendaloa = validated_data['emendaloa']
        elrc.despesa = validated_data['despesa']
        elrc.valor = validated_data['valor']
        elrc.save()

        vkeys_clear = set(v.keys()) - set(validated_data.keys())
        for k in vkeys_clear:
            setattr(elrc, k, v[k])

        return elrc


@customize(EmendaLoaRegistroContabil)
class _EmendaLoaRegistroContabilViewSet:

    class EmendaLoaRegistroContabilPermission(_EmendaLoaViewSet.EmendaLoaPermission):
        def has_permission_post(self, user):
            return user.has_perm('loa.emendaloa_full_editor')

        has_permission_delete = has_permission_post
        has_permission_patch = has_permission_post

    permission_classes = (EmendaLoaRegistroContabilPermission, )

    @action(methods=['post', ], detail=False)
    def create_for_emendaloa_update(self, request, *args, **kwargs):
        self.serializer_class = EmendaLoaRegistroContabilSerializer
        try:
            return super().create(request, *args, **kwargs)

        except DRFValidationError as verror:
            if "code='unique'" in str(verror):
                raise DRFValidationError(
                    'Já existe Registro desta Despesa nesta Emenda.')
            raise DRFValidationError(verror.detail)

        except DjangoValidationError as verror:
            raise DRFValidationError(
                'Já Existe uma Despesa Orçamentária cadastrada com os dados acima. '
                'Faça uma busca com o código informado.')

        except Exception as exc:
            raise DRFValidationError('\n'.join(exc.messages))


@customize(AgrupamentoEmendaLoa)
class _AgrupamentoEmendaLoaViewSet:

    class AgrupamentoEmendaLoaPermission(_EmendaLoaViewSet.EmendaLoaPermission):
        def has_permission_post(self, user):
            return user.has_perm('loa.emendaloa_full_editor')

        has_permission_delete = has_permission_post
        has_permission_patch = has_permission_post

    permission_classes = (AgrupamentoEmendaLoaPermission, )

    @action(methods=['post', ], detail=False)
    def delete(self, request, *args, **kwargs):

        AgrupamentoEmendaLoa.objects.filter(
            agrupamento=int(request.data['agrupamento']),
            emendaloa=int(request.data['emendaloa'])).delete()

        return Response({'detail': 'Registro removido com Sucesso.'})

    def create(self, request, *args, **kwargs):
        try:
            r = super().create(request, *args, **kwargs)

            emendaloa__fase = request.data.get('emendaloa__fase', None)
            if emendaloa__fase:
                el = EmendaLoa.objects.get(pk=r.data['emendaloa'])
                el.fase = emendaloa__fase
                el.save()

            return r
        except Exception as e:
            if "code='unique'" in str(e):
                raise DRFValidationError(
                    'Esta Emenda impositiva já está adicionada em outro Agrupamento.')
            raise DRFValidationError(e)


@customize(Agrupamento)
class _Agrupamento:

    class AgrupamentoPermission(_EmendaLoaViewSet.EmendaLoaPermission):
        def has_permission_post(self, user):
            return user.has_perm('loa.emendaloa_full_editor')

        has_permission_delete = has_permission_post
        has_permission_patch = has_permission_post

    permission_classes = (AgrupamentoPermission, )

    @action(methods=['get', ], detail=True)
    def emendas(self, request, *args, **kwargs):
        return self.get_emendas(**kwargs)

    @wrapper_queryset_response_for_drf_action(model=EmendaLoa)
    def get_emendas(self, **kwargs):
        self.serializer_class = EmendaLoaSearchSerializer
        qs = self.get_queryset()
        return qs.filter(
            agrupamentoemendaloa__agrupamento_id=kwargs['pk']
        )


class AgrupamentoRegistroContabilSerializer(SaplSerializerMixin):

    class RegexLocalField(CharField):
        def __init__(self, regex, **kwargs):
            super().__init__(**kwargs)
            self.validator = RegexValidator(
                regex, message=self.error_messages['invalid'])
            self.validators.append(self.validator)

    codigo = RegexLocalField(
        r'(?P<funcao>\d{2})\.(?P<subfuncao>\d{3})'
        r'\.(?P<programa>\d{4})\.(?P<acao>\d\.[X0-9]{3})$', error_messages={
            'invalid': _('O campo "Código" deve serguir o padrão "99.999.9999.9.XXX". Onde, em "XXX" pode ser utilizado números ou a letra X')})

    natureza = RegexLocalField(r'^(\d{1,2}\.\d{1,2}\.\d{2}\.\d{2}\.[X0-9]{2})$', error_messages={
        'invalid': _('O campo "Natureza" deve serguir o padrão "x9.x9.99.99.XX". Sendo "x" numérico e opcional. Em "XX" pode ser utilizado números ou a letra X.')})

    unidade = RegexLocalField(r'^(\d{2})$', error_messages={
        'invalid': _('O campo "Unidade Orçamentária" deve serguir o padrão "99".')})

    orgao = RegexLocalField(r'^(\d{2})$', error_messages={
        'invalid': _('O campo "Órgão" deve serguir o padrão "99".')})

    percentual = CharField(required=False, error_messages={
        'blank': _('O campo "Perc da Despesa" deve ser prenchido e seguir o formado 999,99. Valores negativos serão direcionados ao Art. 1º, valores positivos ao Art. 2º.'),
    })

    especificacao = CharField()

    class Meta:
        model = AgrupamentoRegistroContabil
        fields = (
            '__str__',
            'id',
            'agrupamento',
            'despesa',
            'codigo',
            'orgao',
            'unidade',
            'especificacao',
            'natureza',
            'percentual'
        )

    def __init__(self, *args, **kwargs):
        return super().__init__(*args, **kwargs)

    def validate(self, attrs):
        loa_id = attrs['agrupamento'].loa_id

        codigo = self.fields.fields['codigo'].validator.regex.match(
            attrs['codigo']).groupdict()

        if not Orgao.objects.filter(codigo=attrs['orgao'], loa_id=loa_id).exists():
            raise DRFValidationError('Órgão não encontrado nos anexos da LOA.')

        if not UnidadeOrcamentaria.objects.filter(
                codigo=attrs['unidade'],
                orgao__codigo=attrs['orgao'],
                loa_id=loa_id
        ).exists():
            raise DRFValidationError(
                'Unidade Orçamentária no Órgão informado não encontrada '
                'nos anexos da LOA.')

        if not Funcao.objects.filter(codigo=codigo['funcao'], loa_id=loa_id).exists():
            raise DRFValidationError(
                'Função não encontrada na base de funções.'
            )

        if not SubFuncao.objects.filter(
                codigo=codigo['subfuncao'],
                loa_id=loa_id
        ).exists():
            raise DRFValidationError(
                'SubFunção não encontrada na base de subfunções.'
            )

        return attrs

    def validate_percentual(self, obj, *args, **kwargs):

        obj = obj or '0.00'

        try:
            if obj and '.' in obj and ',' in obj:
                if obj.rindex(',') > obj.rindex('.'):
                    obj = obj.replace('.', '').replace(',', '.')
                else:
                    obj = obj.replace(',', '')
            elif obj and ',' in obj:
                obj = obj.replace(',', '.')

            obj = Decimal(obj)
        except:
            raise DRFValidationError(
                _('O campo "Perc da Despesa" deve ser prenchido e '
                  'seguir o formado 999,99. '
                  'Valores negativos serão direcionados ao Art. 1º, '
                  'valores positivos ao Art. 2º.')
            )

        if obj == Decimal('0.00'):
            raise DRFValidationError(
                'Valor da Despesa deve ser preenchido. '
                'Valores negativos serão lançados no Art. 1º, '
                'e valores positivos no Art. 2º.')

        return obj

    def create(self, validated_data):
        despesa = validated_data.get('despesa', None)

        v = validated_data
        if not despesa:
            loa_id = v['agrupamento'].loa_id

            codigo = self.fields.fields['codigo'].validator.regex.match(
                v['codigo']).groupdict()

            unidade = UnidadeOrcamentaria.objects.filter(
                codigo=v['unidade'], orgao__codigo=v['orgao'], loa_id=loa_id
            ).first()

            funcao = Funcao.objects.filter(
                codigo=codigo['funcao'], loa_id=loa_id
            ).first()

            subfuncao = SubFuncao.objects.filter(
                codigo=codigo['subfuncao'], loa_id=loa_id
            ).first()

            programa, created = Programa.objects.get_or_create(
                codigo=codigo['programa'], loa_id=loa_id
            )

            acao, created = Acao.objects.get_or_create(
                codigo=codigo['acao'], loa_id=loa_id
            )
            if created:
                acao.especificacao = v['especificacao']
                acao.save()

            natureza, created = Natureza.objects.get_or_create(
                codigo=v['natureza'], loa_id=loa_id
            )

            d = Despesa()
            d.loa = v['agrupamento'].loa
            d.orgao = unidade.orgao
            d.unidade = unidade
            d.funcao = funcao
            d.subfuncao = subfuncao
            d.programa = programa
            d.acao = acao
            d.natureza = natureza

            ddict = d.__dict__
            ddict.pop('id')
            ddict.pop('_state')
            despesa, created = Despesa.objects.get_or_create(**ddict)

        validated_data = {
            'despesa': despesa,
            'agrupamento': v['agrupamento'],
            'percentual': v['percentual']
        }

        elrc = AgrupamentoRegistroContabil()
        elrc.agrupamento = validated_data['agrupamento']
        elrc.despesa = validated_data['despesa']
        elrc.percentual = validated_data['percentual']
        elrc.save()

        vkeys_clear = set(v.keys()) - set(validated_data.keys())
        for k in vkeys_clear:
            setattr(elrc, k, v[k])

        return elrc


@customize(AgrupamentoRegistroContabil)
class _AgrupamentoRegistroContabilViewSet:

    class AgrupamentoRegistroContabilPermission(_EmendaLoaViewSet.EmendaLoaPermission):
        def has_permission_post(self, user):
            return user.has_perm('loa.emendaloa_full_editor')

        has_permission_delete = has_permission_post
        has_permission_patch = has_permission_post

    permission_classes = (AgrupamentoRegistroContabilPermission, )

    @action(methods=['post', ], detail=False)
    def create_for_agrupamento_update(self, request, *args, **kwargs):
        self.serializer_class = AgrupamentoRegistroContabilSerializer
        try:
            return super().create(request, *args, **kwargs)

        except DRFValidationError as verror:
            if "code='unique'" in str(verror):
                raise DRFValidationError(
                    'Já existe Registro desta Despesa neste Agrupamento.')
            raise DRFValidationError(verror.detail)

        except DjangoValidationError as verror:
            raise DRFValidationError(
                'Já Existe uma Despesa Orçamentária cadastrada com os dados acima. '
                'Faça uma busca com o código informado.')

        except Exception as exc:
            raise DRFValidationError('\n'.join(exc.messages))
