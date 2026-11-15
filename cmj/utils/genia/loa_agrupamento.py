import logging

from django.utils.translation import gettext_lazy as _
from google.genai import types

from cmj.utils import clean_text
from cmj.utils.genia import IAGenaiBase

logger = logging.getLogger(__name__)


class IAEmentaEmendaColetiva(IAGenaiBase):
    """
    Classe responsável criar uma ementa de emenda coletiva a partir de varias ementas
    """

    def __init__(self, _ementas=[]):
        # ementas é uma lista de strings representando as finalidades das emendas parlamentares
        super().__init__()
        self.ementas = [clean_text(e) for e in _ementas]

    def gerar_finalidade_global(self, _ementas=None):
        if _ementas:
            self.ementas = [clean_text(e) for e in _ementas]

        if not self.ementas:
            logger.warning("Nenhuma ementa fornecida para agrupamento.")
            return ""

        try:

            # Prompt moldado para contexto legislativo/orçamentário
            prompt = f"""
Você receberá anotações brutas de emendas parlamentares com redundâncias, ruídos de sistema e repetições.

SUA MISSÃO:
Consolidar a destinação/objeto dessas emendas em EXATAMENTE UM ÚNICO PARÁGRAFO contínuo, sem quebras de linha.

REGRAS OBRIGATÓRIAS:
1. ESTRUTURA INICIAL: Comece sempre com minúsculo da seguinte forma "destinado ... ").
2. CONSOLIDAÇÃO DOS OBJETOS: Identifique o objetivo central e liste todas as finalidades/especificações que não forem sinônimos perfeitos, unindo-as e separando cada especificação por " // " (duas barras).
3. ELIMINAÇÃO DE REDUNDÂNCIAS: Elimine Razão Social seguida de CNES ou CNPJ, além de trechos de código entre colchetes ou chaves.
4. PRESERVAÇÃO DE DETALHES: Não resuma genericamente como apenas, por exemplo, "construção"; inclua os detalhes específicos citados (ex: melhorias estruturais, manutenção predial, materiais, custeio).
5. PRESERVAÇÃO DE VALORES MONETÁRIOS: Mantenha todos os valores monetários ligado aos objetos identificados nas emendas, sem arredondamentos ou omissões. Coloque os valores próximos aos objetos correspondentes. Caso haja valores descrevendo apenas a totalização dos objetos, descarte-os.
6. FORMATO: Texto corrido, único parágrafo, terminando sem ponto final.
7. CONSOLIDAÇÃO DAS LOCALIDADES: Consolide e adicione apenas se houve informações claras de bairros, cidades e estados, evitando repetições e redundâncias, mantendo todos os detalhes relevantes, concluíndo com "(Localidade beneficiada: ...)".

DADOS BRUTOS:
            {chr(10).join(f"- {e}" for e in self.ementas)}
            """

            # TODO: refatorar junto com o necessário para IAGenaiBase
            response = self.client.models.generate_content(
                model="gemini-3.1-flash-lite",
                contents=[prompt],
                config=types.GenerateContentConfig(
                    # Baixa temperatura para manter a resposta factual e determinística
                    temperature=0,
                    # system_instruction=(
                    #    "Você é um redator legislativo especialista em emendas parlamentares impositivas. "
                    #    "Sua tarefa é sintetizar textos com máxima precisão técnica, preservando divergências sem duplicar informações."
                    # ),
                ),
            )
            return response.text
        except Exception as e:
            logger.error("Erro ao agrupar ementas: %s", e)
            return ""
