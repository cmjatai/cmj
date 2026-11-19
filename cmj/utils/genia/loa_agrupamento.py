import logging

from cmj.utils import clean_text
from cmj.utils.genia import prompts_loa_agrupamento
from cmj.utils.genia.base import IAGenaiBase

logger = logging.getLogger(__name__)


class IAEmentaEmendaColetiva(IAGenaiBase):
    """
    Consolida as finalidades de várias emendas na ementa de uma emenda coletiva.

    Spec: docs/specs/genia/ementa-emenda-coletiva.md
    """

    # Chama o modelo fixo, sem consultar nem registrar IAQuota.
    quota_exempt = True
    ia_model_name = "gemini-3.1-flash-lite"

    # Temperatura zero para manter a resposta factual e determinística; os
    # demais parâmetros ficam no padrão da API.
    temperature = 0
    top_k = None
    top_p = None
    response_mime_type = None

    prompt_template = prompts_loa_agrupamento.PROMPT_V1

    def __init__(self, ementas=None):
        # ementas: lista de strings com as finalidades das emendas parlamentares
        super().__init__()
        self.ementas = [clean_text(e) for e in ementas or []]

    def make_prompt(self):
        return self.prompt_template.format(
            ementas="\n".join(f"- {e}" for e in self.ementas)
        )

    def gerar_finalidade_global(self, ementas=None):
        """Retorna a ementa consolidada, ou "" sem ementas ou em caso de erro."""
        if ementas:
            self.ementas = [clean_text(e) for e in ementas]

        if not self.ementas:
            logger.warning("Nenhuma ementa fornecida para agrupamento.")
            return ""

        try:
            response = self.generate_content([self.make_prompt()])
            return response.text
        except Exception as e:
            logger.error("Erro ao agrupar ementas: %s", e)
            return ""
