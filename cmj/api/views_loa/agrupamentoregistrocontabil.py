import logging
from decimal import Decimal

from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.validators import RegexValidator
from django.db import IntegrityError
from django.utils.translation import gettext_lazy as _
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.fields import CharField

from cmj.api.serializers import CmjSerializerMixin
from cmj.api.views_loa.emendaloa import EmendaLoaViewSet
from cmj.loa.models import (
    Acao,
    AgrupamentoRegistroContabil,
    Despesa,
    Fonte,
    Funcao,
    Natureza,
    Orgao,
    Programa,
    SubFuncao,
    UnidadeOrcamentaria,
)

logger = logging.getLogger(__name__)


class AgrupamentoRegistroContabilSerializer(CmjSerializerMixin):

    class RegexLocalField(CharField):
        def __init__(self, regex, **kwargs):
            super().__init__(**kwargs)
            self.validator = RegexValidator(
                regex, message=self.error_messages["invalid"]
            )
            self.validators.append(self.validator)

    codigo = RegexLocalField(
        r"(?P<funcao>\d{2})\.(?P<subfuncao>\d{3})"
        r"\.(?P<programa>\d{4})\.(?P<acao>\d\.[X0-9]{3})$",
        error_messages={
            "invalid": _(
                'O campo "Código" deve serguir o padrão "99.999.9999.9.XXX". Onde, em "XXX" pode ser utilizado números ou a letra X'
            )
        },
    )

    natureza = RegexLocalField(
        r"^(\d{1,2}\.\d{1,2}\.\d{2}\.\d{2}\.[X0-9]{2})$",
        error_messages={
            "invalid": _(
                'O campo "Natureza" deve serguir o padrão "x9.x9.99.99.XX". Sendo "x" numérico e opcional. Em "XX" pode ser utilizado números ou a letra X.'
            )
        },
    )

    unidade = RegexLocalField(
        r"^(\d{2})$",
        error_messages={
            "invalid": _('O campo "Unidade Orçamentária" deve serguir o padrão "99".')
        },
    )

    orgao = RegexLocalField(
        r"^(\d{2})$",
        error_messages={"invalid": _('O campo "Órgão" deve serguir o padrão "99".')},
    )

    fonte = RegexLocalField(
        r"^(\d{3})$",
        error_messages={"invalid": _('O campo "Fonte" deve serguir o padrão "999".')},
    )

    percentual = CharField(
        required=False,
        error_messages={
            "blank": _(
                'O campo "Perc da Despesa" deve ser prenchido e seguir o formado 999,99. Valores negativos serão direcionados ao Art. 1º, valores positivos ao Art. 2º.'
            ),
        },
    )

    especificacao = CharField()

    class Meta:
        model = AgrupamentoRegistroContabil
        fields = (
            "__str__",
            "id",
            "agrupamento",
            "despesa",
            "codigo",
            "orgao",
            "unidade",
            "especificacao",
            "natureza",
            "fonte",
            "percentual",
        )

    def __init__(self, *args, **kwargs):
        return super().__init__(*args, **kwargs)

    def validate(self, attrs):
        loa_id = attrs["agrupamento"].loa_id

        codigo = (
            self.fields.fields["codigo"]
            .validator.regex.match(attrs["codigo"])
            .groupdict()
        )

        if not Orgao.objects.filter(codigo=attrs["orgao"], loa_id=loa_id).exists():
            raise DRFValidationError("Órgão não encontrado nos anexos da LOA.")

        if not UnidadeOrcamentaria.objects.filter(
            codigo=attrs["unidade"], orgao__codigo=attrs["orgao"], loa_id=loa_id
        ).exists():
            raise DRFValidationError(
                "Unidade Orçamentária no Órgão informado não encontrada "
                "nos anexos da LOA."
            )

        if not Funcao.objects.filter(codigo=codigo["funcao"], loa_id=loa_id).exists():
            raise DRFValidationError(
                "Função não encontrada na base de funções. Só podem ser criados novos Programas, Ações e Naturezas."
            )

        if not SubFuncao.objects.filter(
            codigo=codigo["subfuncao"], loa_id=loa_id
        ).exists():
            raise DRFValidationError(
                "SubFunção não encontrada na base de subfunções. Só podem ser criados novos Programas, Ações e Naturezas."
            )

        if not Fonte.objects.filter(codigo=attrs["fonte"], loa_id=loa_id).exists():
            raise DRFValidationError(
                "Fonte não encontrada na base de fontes. Só podem ser criados novos Programas, Ações e Naturezas."
            )

        return attrs

    def validate_percentual(self, obj, *args, **kwargs):

        obj = obj or "0.00"

        try:
            if obj and "." in obj and "," in obj:
                if obj.rindex(",") > obj.rindex("."):
                    obj = obj.replace(".", "").replace(",", ".")
                else:
                    obj = obj.replace(",", "")
            elif obj and "," in obj:
                obj = obj.replace(",", ".")

            obj = Decimal(obj)
        except:
            raise DRFValidationError(
                _(
                    'O campo "Perc da Despesa" deve ser prenchido e '
                    "seguir o formado 999,99. "
                    "Valores negativos serão direcionados ao Art. 1º, "
                    "valores positivos ao Art. 2º."
                )
            )

        if obj == Decimal("0.00"):
            raise DRFValidationError(
                "Valor da Despesa deve ser preenchido. "
                "Valores negativos serão lançados no Art. 1º, "
                "e valores positivos no Art. 2º."
            )

        return obj

    def create(self, validated_data):
        despesa = validated_data.get("despesa", None)

        v = validated_data
        if not despesa:
            loa_id = v["agrupamento"].loa_id

            codigo = (
                self.fields.fields["codigo"]
                .validator.regex.match(v["codigo"])
                .groupdict()
            )

            unidade = UnidadeOrcamentaria.objects.filter(
                codigo=v["unidade"], orgao__codigo=v["orgao"], loa_id=loa_id
            ).first()

            funcao = Funcao.objects.filter(
                codigo=codigo["funcao"], loa_id=loa_id
            ).first()

            subfuncao = SubFuncao.objects.filter(
                codigo=codigo["subfuncao"], loa_id=loa_id
            ).first()

            fonte = Fonte.objects.filter(codigo=v["fonte"], loa_id=loa_id).first()

            programa, created = Programa.objects.get_or_create(
                codigo=codigo["programa"], loa_id=loa_id
            )

            acao, created = Acao.objects.get_or_create(
                codigo=codigo["acao"], loa_id=loa_id
            )
            if created:
                acao.especificacao = v["especificacao"]
                acao.save()

            natureza, created = Natureza.objects.get_or_create(
                codigo=v["natureza"], loa_id=loa_id
            )

            d = Despesa()
            d.loa = v["agrupamento"].loa
            d.orgao = unidade.orgao
            d.unidade = unidade
            d.funcao = funcao
            d.subfuncao = subfuncao
            d.programa = programa
            d.acao = acao
            d.natureza = natureza
            d.fonte = fonte

            ddict = d.__dict__
            ddict.pop("id")
            ddict.pop("_state")
            ddict.pop("valor_materia", None)
            ddict.pop("valor_norma", None)
            despesa, created = Despesa.objects.get_or_create(**ddict)

        validated_data = {
            "despesa": despesa,
            "agrupamento": v["agrupamento"],
            "percentual": v["percentual"],
        }

        elrc = AgrupamentoRegistroContabil()
        elrc.agrupamento = validated_data["agrupamento"]
        elrc.despesa = validated_data["despesa"]
        elrc.percentual = validated_data["percentual"]
        elrc.save()

        vkeys_clear = set(v.keys()) - set(validated_data.keys())
        for k in vkeys_clear:
            setattr(elrc, k, v[k])

        return elrc


class AgrupamentoRegistroContabilViewSet:

    class AgrupamentoRegistroContabilPermission(EmendaLoaViewSet.EmendaLoaPermission):
        def has_permission_post(self, request, view):
            return request.user.has_perm("loa.emendaloa_full_editor")

        has_permission_delete = has_permission_post
        has_permission_patch = has_permission_post

    permission_classes = (AgrupamentoRegistroContabilPermission,)

    @action(
        methods=[
            "post",
        ],
        detail=False,
    )
    def create_for_agrupamento_update(self, request, *args, **kwargs):
        self.serializer_class = AgrupamentoRegistroContabilSerializer
        try:
            return super().create(request, *args, **kwargs)

        except DRFValidationError as verror:
            if "code='unique'" in str(verror):
                raise DRFValidationError(
                    "Já existe Registro desta Despesa neste Agrupamento."
                )
            raise DRFValidationError(verror.detail)

        except DjangoValidationError as verror:
            raise DRFValidationError(
                "Já Existe uma Despesa Orçamentária cadastrada com os dados acima. "
                "Faça uma busca com o código informado."
            )

        except IntegrityError as ierr:
            if "unique constraint" in str(ierr).lower():
                raise DRFValidationError(
                    "Já existe Registro desta Despesa neste Agrupamento."
                )
            raise DRFValidationError(str(ierr))

        except Exception as exc:
            raise DRFValidationError("\n".join(exc.messages))
