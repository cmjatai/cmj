import logging

from django.conf import settings
from django.utils.translation import gettext_lazy as _
from google import genai
from google.genai import types

from cmj.core.models import IAQuota

logger = logging.getLogger(__name__)


class IAQuotaUnavailableError(Exception):
    """Nenhuma IAQuota ativa, autorizada e com margem para o serviço."""


class IAGenaiBase:
    """
    Conexão com a API Gemini e controle de cota do modelo em uso.

    Não conhece prompts nem regras de nenhuma funcionalidade: cada serviço
    herda desta classe e declara a sua chave de cota e os seus parâmetros de
    geração. Spec: docs/specs/genia/conexao-e-cotas.md
    """

    # Chave do serviço em IAQuota.servicos_autorizados. Sem chave, o serviço
    # não consegue obter cota.
    quota_service_name = None

    # True: o serviço chama `ia_model_name` direto, sem consultar nem
    # registrar IAQuota.
    quota_exempt = False

    # Modelo padrão. Em serviço com cota, é substituído pelo modelo da
    # IAQuota selecionada a cada chamada.
    ia_model_name = "gemini-3.5-flash-lite"

    # Parâmetros de geração. None deixa o padrão da API.
    temperature = 0.1
    top_k = 40
    top_p = 0.95
    response_mime_type = "application/json"
    system_instruction = None
    max_remote_calls = 10  # limite de function calling automático, com tools

    def __init__(self):
        if not settings.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY não configurada.")
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)

    # ------------------------------------------------------------------
    # Cota
    # ------------------------------------------------------------------

    def retrieve_quota_if_available(self, ia_model_name=None, ascending=True):
        """
        Retorna a IAQuota a consumir e fixa `self.ia_model_name` no modelo
        dela. `ascending=True` prefere a menor cota diária; `False`, a maior.
        Levanta IAQuotaUnavailableError se não houver cota para o serviço.
        """
        e_message = _("Nenhum Modelo com Quota para consumo disponível.")

        if not self.quota_service_name:
            raise IAQuotaUnavailableError(e_message)

        qms = IAQuota.objects.quotas_with_margin(ascending=ascending).filter(
            servicos_autorizados__contains=[str(self.quota_service_name)]
        )
        if ia_model_name:
            qms = qms.filter(modelo=ia_model_name)

        quota = qms.first()
        if not quota:
            raise IAQuotaUnavailableError(e_message)

        self.ia_model_name = quota.modelo
        return quota

    def update_or_create_llm_models_in_quotamodel(self):
        """Sincroniza os modelos listados pela API com os registros de IAQuota."""
        # Iterar o Pager percorre todas as páginas da listagem.
        for model in self.client.models.list():
            IAQuota.objects.update_or_create(
                modelo=model.name.split("/")[-1],
                defaults={"descricao": repr(model)},
            )

    # ------------------------------------------------------------------
    # Geração
    # ------------------------------------------------------------------

    def build_generation_config(self, tools=None):
        params = {
            "temperature": self.temperature,
            "top_p": self.top_p,
            "top_k": self.top_k,
            "response_mime_type": self.response_mime_type,
            "system_instruction": self.system_instruction,
        }
        if tools:
            params["tools"] = tools
            params["automatic_function_calling"] = types.AutomaticFunctionCallingConfig(
                maximum_remote_calls=self.max_remote_calls
            )
        return types.GenerateContentConfig(
            **{k: v for k, v in params.items() if v is not None}
        )

    def generate_content(
        self, contents, ia_model_name=None, tools=None, ascending=True, quota=None
    ):
        """
        Gera conteúdo com o modelo da cota disponível e registra o consumo
        depois da resposta. Serviço `quota_exempt` usa `ia_model_name` direto.
        Com `quota`, consome essa cota sem consultar a disponibilidade de novo.
        """
        if quota:
            model = quota.modelo
            self.ia_model_name = model
        elif self.quota_exempt:
            model = ia_model_name or self.ia_model_name
        else:
            quota = self.retrieve_quota_if_available(
                ia_model_name=ia_model_name, ascending=ascending
            )
            model = quota.modelo

        response = self.client.models.generate_content(
            model=model,
            contents=contents,
            config=self.build_generation_config(tools=tools),
        )

        if quota:
            quota.create_log()
        return response

    def count_tokens_in_text(self, text):
        try:
            response = self.client.models.count_tokens(
                model=self.ia_model_name, contents=text
            )
            return response.total_tokens
        except Exception as e:
            logger.error(f"Erro ao contar tokens: {e}")
            return 0
