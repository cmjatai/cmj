import json
import logging
import re
import time

import pymupdf
import yaml
from django.conf import settings
from django.contrib import messages
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from google import genai
from google.genai import types

from cmj.core.models import IAQuota
from cmj.utils import clean_text
from cmj.utils.genia.genia_system_instruction_v3 import rag_system_instruction
from sapl.base.models import Metadata

logger = logging.getLogger(__name__)


class IAGenaiBase:
    ia_model_name = "gemini-3-flash-preview"
    temperature = 0.1
    top_k = 40
    top_p = 0.95
    response_mime_type = "application/json"

    _chat = None
    _chat_quota = None

    def __init__(self, *args, **kwargs):
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)

    def update_or_create_llm_models_in_quotamodel(self):
        models = self.client.models.list()
        for model in models.page:
            model_name = model.name.split("/")[-1]
            quota, created = IAQuota.objects.update_or_create(modelo=model_name)
            if created:
                quota.servicos_autorizados = []

            quota.descricao = repr(model)
            quota.save()

    def chat_send_message(self, message, history, tools=None):
        if not self._chat:
            self.response_mime_type = "text/plain"
            self._chat_quota = self.retrieve_quota_if_available()
            config = self.update_generation_config(tools=tools)
            self._chat = self.client.chats.create(
                model=self.ia_model_name,
                config=config,
                history=history,
            )

        message = str(message)
        response = self._chat.send_message(message)
        print(self._chat.get_history())

        if self._chat_quota:
            self._chat_quota.create_log()

        return response

    def update_generation_config(self, tools=None):

        if tools:

            # Carece de revisão de Prompts para permitir pesquisa Online
            # grounding_tool = types.Tool(
            #    google_search=types.GoogleSearch()
            # )

            self.generation_config = types.GenerateContentConfig(
                system_instruction=rag_system_instruction,
                temperature=self.temperature,
                top_p=self.top_p,
                top_k=self.top_k,
                response_mime_type=self.response_mime_type,
                tools=tools,
                automatic_function_calling=genai.types.AutomaticFunctionCallingConfig(
                    maximum_remote_calls=10
                ),
            )
            return self.generation_config

        self.generation_config = types.GenerateContentConfig(
            temperature=self.temperature,
            top_p=self.top_p,
            top_k=self.top_k,
            response_mime_type=self.response_mime_type,
        )
        return self.generation_config

    def retrieve_quota_if_available(self, ia_model_name=None, ascending=True):

        e_message = _("Nenhum Modelo com Quota para consumo disponível.")

        qms = IAQuota.objects.quotas_with_margin(ascending=ascending)
        qms = qms.filter(
            servicos_autorizados__contains=[
                self.__class__.__name__,
            ]
        )
        if not qms:
            raise Exception(e_message)

        qms_custom = qms
        if ia_model_name:
            qms_custom = qms.filter(modelo=ia_model_name)
            if not qms_custom:
                raise Exception(e_message)

        self.ia_model_name = qms_custom.first().modelo
        return qms_custom.first()

    def generate_content(
        self, contents, ia_model_name=None, tools=None, ascending=True
    ):
        quota = self.retrieve_quota_if_available(
            ia_model_name=ia_model_name, ascending=ascending
        )
        self.update_generation_config()
        config = self.generation_config
        if tools:
            config = types.GenerateContentConfig(
                system_instruction=rag_system_instruction,
                temperature=self.temperature,
                top_p=self.top_p,
                top_k=self.top_k,
                response_mime_type=self.response_mime_type,
                tools=tools,
                automatic_function_calling=genai.types.AutomaticFunctionCallingConfig(
                    maximum_remote_calls=10
                ),
            )

        response = self.client.models.generate_content(
            model=quota.modelo,
            contents=contents,
            config=config,
        )

        quota.create_log()
        return response

    def _extract_pdf_text(self, doc):

        text_parts = []

        for page in doc:
            try:
                page_text = page.get_text()
                private_use_pattern = re.compile(r"[\ue000-\uf8ff]")
                private_use_count = len(private_use_pattern.findall(page_text))

                if private_use_count > len(page_text) * 0.1:
                    rect = pymupdf.Rect(
                        0, 80, page.rect.width - 45, page.rect.height - 55
                    )
                    pix = page.get_pixmap(clip=rect, dpi=300)
                    # pix.save("/tmp/temp_page.png")
                    bpix = pix.pdfocr_tobytes()
                    bpdf = pymupdf.open(stream=bpix)
                    bpage = bpdf[0]
                    page_text = bpage.get_textpage_ocr()
                    page_text = page_text.extractText()

                text_parts.append(page_text)

            except Exception as e:
                logger.warning(f"Erro ao extrair texto da página: {e}")
                text_parts.append("")

        return " ".join(text_parts)

    def count_tokens_in_text(self, text):
        try:
            # self.ia_model_name = "gemini-3-pro-preview"
            response = self.client.models.count_tokens(
                model=self.ia_model_name, contents=text
            )
            return response.total_tokens
        except Exception as e:
            logger.error(f"Erro ao contar tokens: {e}")
            return 0

    def embed_content(self, text):
        try:
            response = self.client.models.embed_content(
                model="gemini-embedding-001",
                contents=[text],
                config=types.EmbedContentConfig(
                    task_type="RETRIEVAL_QUERY",
                    output_dimensionality=1536,
                ),
            )
            [embedding_object] = response.embeddings
            # print(len(embedding_object.values))
            return embedding_object.values
        except Exception as e:
            logger.error(f"Erro ao gerar embedding: {e}")
            return []
