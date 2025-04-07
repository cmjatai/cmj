import logging

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist
from django.db.models import Q
from django.urls.base import reverse
from drf_spectacular.utils import extend_schema_field
from image_cropping.utils import get_backend
from rest_framework import serializers
from rest_framework.fields import SerializerMethodField

from sapl.base.models import Autor, CasaLegislativa, Metadata
from sapl.materia.models import MateriaLegislativa
from sapl.parlamentares.models import Parlamentar, Mandato, Legislatura
from sapl.sessao.models import OrdemDia, SessaoPlenaria


class SaplSerializerMixin(serializers.ModelSerializer):
    __str__ = SerializerMethodField()
    # metadata = SerializerMethodField()
    link_detail_backend = SerializerMethodField()

    class Meta:
        fields = '__all__'

    def get_link_detail_backend(self, obj) -> str:
        try:
            return reverse(f'{self.Meta.model._meta.app_config.name}:{self.Meta.model._meta.model_name}_detail',
                           kwargs={'pk': obj.pk})
        except:
            return ''

    def get___str__(self, obj) -> str:
        return str(obj)

    """def get_metadata(self, obj) -> dict:
        try:
            metadata = Metadata.objects.get(
                content_type=ContentType.objects.get_for_model(
                    obj._meta.model),
                object_id=obj.id
            ).metadata
        except:
            metadata = {}
        finally:
            return metadata"""


class ChoiceSerializer(serializers.Serializer):
    value = serializers.SerializerMethodField()
    text = serializers.SerializerMethodField()

    def get_text(self, obj):
        return obj[1]

    def get_value(self, obj):
        return obj[0]


class ModelChoiceSerializer(ChoiceSerializer):

    def get_text(self, obj):
        return str(obj)

    def get_value(self, obj):
        return obj.id


@extend_schema_field({'type': 'string'})
class ModelChoiceObjectRelatedField(serializers.RelatedField):

    def to_representation(self, value):
        return ModelChoiceSerializer(value).data


class AutorSerializer(SaplSerializerMixin):

    autor_related = ModelChoiceObjectRelatedField(read_only=True)

    class Meta:
        model = Autor
        fields = '__all__'


class CasaLegislativaSerializer(SaplSerializerMixin):
    version = serializers.SerializerMethodField()

    def get_version(self, obj):
        return settings.PORTALCMJ_VERSION

    class Meta:
        model = CasaLegislativa
        fields = '__all__'


class MateriaLegislativaSerializer(SaplSerializerMixin):
    anexadas = serializers.SerializerMethodField()
    desanexadas = serializers.SerializerMethodField()

    class Meta:
        model = MateriaLegislativa
        fields = '__all__'

    def get_anexadas(self, obj):
        return obj.anexadas.materias_anexadas().values_list('id', flat=True)

    def get_desanexadas(self, obj):
        return obj.anexadas.materias_desanexadas().values_list('id', flat=True)


class ParlamentarSerializerPublic(SaplSerializerMixin):

    class Meta:
        model = Parlamentar
        exclude = ["cpf", "rg", "fax",
                   "endereco_residencia", "municipio_residencia",
                   "uf_residencia", "cep_residencia", "situacao_militar",
                   "telefone_residencia", "titulo_eleitor", "fax_residencia"]


class ParlamentarSerializerVerbose(SaplSerializerMixin):
    titular = serializers.SerializerMethodField('check_titular')
    partido = serializers.SerializerMethodField('check_partido')
    fotografia_cropped = serializers.SerializerMethodField('crop_fotografia')
    logger = logging.getLogger(__name__)

    def crop_fotografia(self, obj):
        try:
            return obj.fotografia.url_cropped(size=128)

        except Exception as e:
            self.logger.error(e)
            self.logger.error('erro processando arquivo: %s' %
                              obj.fotografia.path)

        return ''

    def check_titular(self, obj):
        is_titular = None
        if not Legislatura.objects.exists():
            self.logger.error("Não há legislaturas cadastradas.")
            return ""

        try:
            legislatura = Legislatura.objects.get(
                id=self.context.get('legislatura'))
        except ObjectDoesNotExist:
            legislatura = Legislatura.objects.first()
        mandato = Mandato.objects.filter(
            parlamentar=obj,
            data_inicio_mandato__gte=legislatura.data_inicio,
            data_fim_mandato__lte=legislatura.data_fim
        ).order_by('-data_inicio_mandato').first()
        if mandato:
            is_titular = 'Sim' if mandato.titular else 'Não'
        else:
            is_titular = '-'
        return is_titular

    def check_partido(self, obj):
        # Coloca a filiação atual ao invés da última
        # As condições para mostrar a filiação são:
        # A data de filiacao deve ser menor que a data de fim
        # da legislatura e data de desfiliação deve nula, ou maior,
        # ou igual a data de fim da legislatura

        username = self.context['request'].user.username
        if not Legislatura.objects.exists():
            self.logger.error("Não há legislaturas cadastradas.")
            return ""
        try:
            legislatura = Legislatura.objects.get(
                id=self.context.get('legislatura'))
        except ObjectDoesNotExist:
            legislatura = Legislatura.objects.first()

        try:
            self.logger.debug("user=" + username + ". Tentando obter filiação do parlamentar com (data<={} e data_desfiliacao>={}) "
                              "ou (data<={} e data_desfiliacao=Null))."
                              .format(legislatura.data_fim, legislatura.data_fim, legislatura.data_fim))
            filiacao = obj.filiacao_set.get(Q(
                data__lte=legislatura.data_fim,
                data_desfiliacao__gte=legislatura.data_fim) | Q(
                data__lte=legislatura.data_fim,
                data_desfiliacao__isnull=True))

        # Caso não exista filiação com essas condições
        except ObjectDoesNotExist:
            self.logger.warning("user=" + username + ". Parlamentar com (data<={} e data_desfiliacao>={}) "
                                "ou (data<={} e data_desfiliacao=Null)) não possui filiação."
                                .format(legislatura.data_fim, legislatura.data_fim, legislatura.data_fim))
            filiacao = 'Não possui filiação'

        # Caso exista mais de uma filiação nesse intervalo
        # Entretanto, NÃO DEVE OCORRER
        except MultipleObjectsReturned:
            self.logger.error("user=" + username + ". O Parlamentar com (data<={} e data_desfiliacao>={}) "
                              "ou (data<={} e data_desfiliacao=Null)) possui duas filiações conflitantes"
                              .format(legislatura.data_fim, legislatura.data_fim, legislatura.data_fim))
            filiacao = 'O Parlamentar possui duas filiações conflitantes'

        # Caso encontre UMA filiação nessas condições
        else:
            self.logger.debug("user=" + username +
                              ". Filiação encontrada com sucesso.")
            filiacao = filiacao.partido.sigla

        return filiacao

    class Meta:
        model = Parlamentar
        fields = ['id', 'nome_parlamentar', 'fotografia_cropped',
                  'fotografia', 'ativo', 'partido', 'titular', ]


class SessaoPlenariaECidadaniaSerializer(serializers.ModelSerializer):

    codReuniao = serializers.SerializerMethodField('get_pk_sessao')
    codReuniaoPrincipal = serializers.SerializerMethodField('get_pk_sessao')
    txtTituloReuniao = serializers.SerializerMethodField('get_name')
    txtSiglaOrgao = serializers.SerializerMethodField('get_sigla_orgao')
    txtApelido = serializers.SerializerMethodField('get_name')
    txtNomeOrgao = serializers.SerializerMethodField('get_nome_orgao')
    codEstadoReuniao = serializers.SerializerMethodField(
        'get_estadoSessaoPlenaria')
    txtTipoReuniao = serializers.SerializerMethodField('get_tipo_sessao')
    txtObjeto = serializers.SerializerMethodField('get_assunto_sessao')
    txtLocal = serializers.SerializerMethodField('get_endereco_orgao')
    bolReuniaoConjunta = serializers.SerializerMethodField(
        'get_reuniao_conjunta')
    bolHabilitarEventoInterativo = serializers.SerializerMethodField(
        'get_iterativo')
    idYoutube = serializers.SerializerMethodField('get_url')
    codEstadoTransmissaoYoutube = serializers.SerializerMethodField(
        'get_estadoTransmissaoYoutube')
    datReuniaoString = serializers.SerializerMethodField('get_date')

    # Constantes SessaoPlenaria (de 1-9) (apenas 3 serão usados)
    SESSAO_FINALIZADA = 4
    SESSAO_EM_ANDAMENTO = 3
    SESSAO_CONVOCADA = 2

    # Constantes EstadoTranmissaoYoutube (de 0 a 2)
    TRANSMISSAO_ENCERRADA = 2
    TRANSMISSAO_EM_ANDAMENTO = 1
    SEM_TRANSMISSAO = 0

    class Meta:
        model = SessaoPlenaria
        fields = (
            'codReuniao',
            'codReuniaoPrincipal',
            'txtTituloReuniao',
            'txtSiglaOrgao',
            'txtApelido',
            'txtNomeOrgao',
            'codEstadoReuniao',
            'txtTipoReuniao',
            'txtObjeto',
            'txtLocal',
            'bolReuniaoConjunta',
            'bolHabilitarEventoInterativo',
            'idYoutube',
            'codEstadoTransmissaoYoutube',
            'datReuniaoString'
        )

    def get_pk_sessao(self, obj):
        return obj.pk

    def get_name(self, obj):
        return obj.__str__()

    def get_estadoSessaoPlenaria(self, obj):
        if obj.finalizada:
            return self.SESSAO_FINALIZADA
        elif obj.iniciada:
            return self.SESSAO_EM_ANDAMENTO
        else:
            return self.SESSAO_CONVOCADA

    def get_tipo_sessao(self, obj):
        return obj.tipo.__str__()

    def get_url(self, obj):
        return obj.url_video if obj.url_video else None

    def get_iterativo(self, obj):
        return obj.interativa if obj.interativa else False

    def get_date(self, obj):
        return "{} {}{}".format(
            obj.data_inicio.strftime("%d/%m/%Y"),
            obj.hora_inicio,
            ":00"
        )

    def get_estadoTransmissaoYoutube(self, obj):
        if obj.url_video:
            if obj.finalizada:
                return self.TRANSMISSAO_ENCERRADA
            else:
                return self.TRANSMISSAO_EM_ANDAMENTO
        else:
            return self.SEM_TRANSMISSAO

    def get_assunto_sessao(self, obj):
        pauta_sessao = ''
        ordem_dia = OrdemDia.objects.filter(sessao_plenaria=obj.pk)
        pauta_sessao = ', '.join([i.materia.__str__() for i in ordem_dia])

        return str(pauta_sessao)

    def get_endereco_orgao(self, obj):
        return self.casa().endereco

    def get_reuniao_conjunta(self, obj):
        return False

    def get_sigla_orgao(self, obj):
        return self.casa().sigla

    def get_nome_orgao(self, obj):
        return self.casa().nome

    def casa(self):
        casa = CasaLegislativa.objects.first()
        return casa
