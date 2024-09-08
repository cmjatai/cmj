from decimal import Decimal
import logging

from django.apps.registry import apps
from django.core.validators import RegexValidator
from django.db.models import Q, F
from django.db.models.aggregates import Sum
from django.db.models.functions import Substr
from django.forms.models import model_to_dict
from django.http.response import HttpResponse
from django.template.loader import render_to_string
from django.utils import formats
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
import pymupdf
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.fields import RegexField, DecimalField, CharField
from rest_framework.response import Response

from cmj.loa.models import OficioAjusteLoa, EmendaLoa, Loa, EmendaLoaParlamentar,\
    DespesaConsulta, EmendaLoaRegistroContabil, UnidadeOrcamentaria, Despesa,\
    Orgao, Funcao, SubFuncao, Programa, Acao, Natureza
from drfautoapi.drfautoapi import ApiViewSetConstrutor, customize
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


@customize(Loa)
class _LoaViewSet:

    class LoaPermission(SaplModelPermissions):
        def has_permission(self, request, view):
            has_perm = super().has_permission(request, view)

            if has_perm:
                return has_perm

            u = request.user
            if u.is_anonymous:

                if request.method == 'POST' and view.action == 'despesas_agrupadas':
                    return True

            return False

    permission_classes = (LoaPermission, )

    @action(methods=['post', ], detail=True)
    def despesas_agrupadas(self, request, *args, **kwargs):
        loa_id = kwargs['pk']

        filters_base = [
            'orgao',
            'unidade',
            'funcao',
            'subfuncao',
            'programa',
            'acao',
            'natureza_1',
            'natureza_2',
            'natureza_3',
            'natureza_4',
            'natureza_5'
        ]

        filters = request.data

        try:
            itens = filters.pop('itens')
            itens = min(25, int(itens))
        except:
            itens = 20

        grup_str = filters.pop('agrupamento')
        agrup = {}

        if 'natureza' not in grup_str:
            agrup['codigo'] = F(f'{grup_str}__codigo')
            agrup['especificacao'] = F(f'{grup_str}__especificacao')
            order_by = f'{grup_str}__codigo'
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
            order_by = 'natureza__codigo'

        filters = {
            f'{k}_id': v
            for k, v in filters.items() if v and k in filters_base
        }
        filters['loa_id'] = loa_id

        rs = list(Despesa.objects.filter(**filters).values(
            **agrup
        ).order_by(
            order_by
        ).annotate(
            vm=Sum('valor_materia'),
            vn=Sum('valor_norma'),
            alt=Sum('registrocontabil_set__valor')))

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

        return Response(r)


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
    def updatevalorparlamentar(self, request, *args, **kwargs):
        #instance = self.get_object()

        data = request.data
        data['emendaloa_id'] = kwargs['pk']
        dvalor = data.pop('valor')
        try:
            valor = Decimal(dvalor)
        except:
            valor = Decimal('0.00')

        u = request.user
        if not u.is_superuser and u.operadorautor_set.exists():
            p = u.operadorautor_set.first().autor.autor_related

            if p.id == int(data['parlamentar_id']) and valor <= Decimal('0.00'):
                raise ValidationError(
                    'Você não pode zerar o Valor do Parlamentar '
                    'ao qual seu usuário está ligado. '
                    'Caso queira, você pode excluir esse registro '
                    'clicando em excluir na tela de consulta.')

        elp, created = EmendaLoaParlamentar.objects.get_or_create(**data)
        elp.valor = valor
        elp.save()
        el = elp.emendaloa

        if not elp.valor:
            elp.delete()

        el.atualiza_valor().save()

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


@customize(DespesaConsulta)
class _DespesaConsulta:

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

    valor = DecimalField(14, 2, error_messages={
        'invalid': _('O campo "Valor da Despesa" deve ser prenchido e seguir o formado 999999,99. Valores negativos serão direcionados ao Art. 1º, valores positivos ao Art. 2º.')})

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
            raise ValidationError('Órgão não encontrado nos anexos da LOA.')

        if not UnidadeOrcamentaria.objects.filter(
                codigo=attrs['unidade'],
                orgao__codigo=attrs['orgao'],
                loa_id=loa_id
        ).exists():
            raise ValidationError(
                'Unidade Orçamentária no Órgão informado não encontrada '
                'nos anexos da LOA.')

        if not Funcao.objects.filter(codigo=codigo['funcao'], loa_id=loa_id).exists():
            raise ValidationError(
                'Função não encontrada na base de funções.'
            )

        if not SubFuncao.objects.filter(
                codigo=codigo['subfuncao'],
                loa_id=loa_id
        ).exists():
            raise ValidationError(
                'SubFunção não encontrada na base de subfunções.'
            )

        return attrs

    def validate_valor(self, obj, *args, **kwargs):
        if obj == Decimal('0.00'):
            raise ValidationError(
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

    permission_classes = (EmendaLoaRegistroContabilPermission, )

    @action(methods=['post', ], detail=False)
    def create_for_emendaloa_update(self, request, *args, **kwargs):
        self.serializer_class = EmendaLoaRegistroContabilSerializer
        try:
            return super().create(request, *args, **kwargs)

        except ValidationError as verror:
            if "code='unique'" in str(verror):
                raise ValidationError(
                    'Já existe Registro desta Despesa nesta Emenda.')
            raise ValidationError(verror.detail)

        except Exception as exc:
            raise Exception(exc)
