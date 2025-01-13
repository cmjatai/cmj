import json
import logging

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.urls.base import reverse
from django.utils.translation import gettext_lazy as _
import pymupdf

from cmj.utils import clean_text
from sapl.base.models import Metadata
import google.generativeai as genai

logger = logging.getLogger(__name__)

class GoogleGenerativeIA:
    
    ia_model_name = "gemini-2.0-flash-exp"

    def get_btn_generate(self, viewname):
        return [
            (
                '{}?ia_run=generate'.format(
                    reverse(
                        viewname,
                        kwargs={'pk': self.kwargs['pk']}
                    )
                ),
                'btn-primary',
                _('Gerar Análise por I.A.')
            )
        ]

    def ia_run(self):
        action = self.request.GET.get('ia_run', 'generate')

        if action == 'generate':
            self.generate()
        elif action == 'delete':
            self.delete()

    def delete(self):
            obj = self.get_object()
            Metadata.objects.filter(
                object_id=obj.id,
                content_type=ContentType.objects.get_for_model(obj)
                ).delete()

    def get_model_configured(self):
        generation_config = {
          "temperature": 0.1,
          "top_p": 0.95,
          "top_k": 40,
          # "max_output_tokens": 8192,
          "response_mime_type": "application/json",
        }

        genai.configure(api_key=settings.GEMINI_API_KEY)

        model = genai.GenerativeModel(
          model_name=self.ia_model_name,
          generation_config=generation_config,
        )

        return model

    def make_prompt(self, context):
        obj = self.get_object()

        prompt_mask = obj.tipo.prompt
        if not prompt_mask:
            return ''

        prompt = prompt_mask.format(context=context)
        while '  ' in prompt:
            prompt = prompt.replace('  ', ' ')

        return prompt

    def extract_text(self):
        obj = self.get_object()

        text = ''
        for fn in obj.FIELDFILE_NAME:
            if not getattr(obj, fn):
                continue

            doc = pymupdf.open(getattr(obj, fn).path)
            doc_text = ' '.join([page.get_text() for page in doc])
            doc_text = clean_text(doc_text)

            text += doc_text
        return text

    def generate(self):
        try:

            context = self.extract_text()
            prompt = self.make_prompt(context=context)

            if not prompt:
                return

            model = self.get_model_configured()
            answer = model.generate_content(prompt)

            obj = self.get_object()

            md = Metadata()
            md.content_object = obj
            metadata = {'genia': json.loads(answer.text)}
            metadata['genia']['model_name'] = self.ia_model_name
            md.metadata = metadata
            md.save()

        except Exception as e:
            logger.error(e)

