import json
import logging

from django.conf import settings
from django.contrib import messages
from django.contrib.contenttypes.models import ContentType
from django.urls.base import reverse
from django.utils.translation import gettext_lazy as _
import pymupdf
import yaml
from django.utils import timezone
from cmj.utils import clean_text
from sapl.base.models import Metadata
import google.generativeai as genai

logger = logging.getLogger(__name__)

class GoogleGenerativeIA:

    ia_model_name = "gemini-2.0-flash-exp"

    _model = None # Model from app django
    _content_type = None # ContentType from app django
    _object = None # Object from app django

    temperature = 0.1
    top_k = 40
    top_p = 0.95

    @property
    def model(self):
        if not self._model:
            raise Exception('Model not configured')

        return self._model

    @model.setter
    def model(self, model):
        self._model = model
        self._content_type = ContentType.objects.get_for_model(model)

    @property
    def content_type(self):
        if not self._content_type:
            raise Exception('ContentType not configured')

        return self._content_type

    @content_type.setter
    def content_type(self, content_type):
        self._content_type = content_type

    @property
    def object(self):
        if not self._object:
            raise Exception('Object not configured')
        return self._object

    @object.setter
    def object(self, obj):
        if isinstance(obj, self.model):
            self._object = obj
        elif isinstance(obj, int) or isinstance(obj, str):
            try:
                obj = int(obj)
                self._object = self.model.objects.get(pk=obj)
            except Exception as e:
                raise Exception('Registro não encontrado.')
        else:
            raise Exception('Registro não encontrado.')


    def run(self, *args, **kwargs):
        """
        Executa a ação de IA, que pode ser gerar ou deletar
        """
        self.request = kwargs.get('request', {})
        self.GET = self.request.GET if hasattr(self.request, 'GET') else {}
        if not self.GET:
            self.GET = {
                'action': kwargs.get('action', 'generate'),
                'temperature': kwargs.get('temperature', self.temperature),
                'top_k': kwargs.get('top_k', self.top_k),
                'top_p': kwargs.get('top_p', self.top_p),
            }
            self.action = self.GET.get('action', 'generate')
        else:
            self.action = self.GET.get('ia_run', 'generate')

        if self.action.startswith('generate'):
            self.delete()
            self.temperature = self.GET.get('temperature', self.temperature)
            self.top_k = self.GET.get('top_k', self.top_k)
            self.top_p = self.GET.get('top_p', self.top_p)
            return self.generate()
        elif self.action == 'delete':
            self.delete()
            if self.request:
                messages.add_message(
                    self.request, messages.SUCCESS,
                    _('Análise removida com sucesso!'))

    def delete(self):
        obj = self.object
        Metadata.objects.filter(
            object_id=obj.id,
            content_type=self.content_type
        ).delete()

    def has_analise(self):
        """
        Verifica se o objeto já possui análise gerada
        """
        obj = self.object
        if not obj:
            return False

        metadata = Metadata.objects.filter(
            object_id=obj.id,
            content_type=self.content_type
        ).first()

        if not metadata:
            return False

        if 'genia' not in metadata.metadata:
            return False

        return True

    def get_analise(self):
        """
        Retorna a análise gerada
        """
        obj = self.object
        if not obj:
            return None

        metadata = Metadata.objects.filter(
            object_id=obj.id,
            content_type=self.content_type
        ).first()

        if not metadata:
            return None

        if 'genia' not in metadata.metadata:
            return None

        return metadata.metadata['genia']

    def get_model_configured(self):
        generation_config = {
          "temperature": self.temperature,
          "top_p": self.top_p,
          "top_k": self.top_k,
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
        obj = self.object

        prompt_mask = obj.tipo.prompt
        if not prompt_mask:
            return ''

        yaml_data = yaml.load(prompt_mask, Loader=yaml.FullLoader)

        status = False
        for prompt_object in yaml_data['PROMPTs']:
            status = prompt_object['status']
            if status:
                break

        if not status:
            return ''

        if self.action == 'generate':
            self.temperature = prompt_object.get('temperature', self.temperature)
            self.top_k = prompt_object.get('top_k', self.top_k)
            self.top_p = prompt_object.get('top_p', self.top_p)
        elif self.action == 'generate_custom':
            self.temperature = float(self.GET.get('temperature', self.temperature))
            self.top_p = float(self.GET.get('top_p', self.top_p))
            self.top_k = int(self.GET.get('top_k', self.top_k))

        prompt_mask = prompt_object.get('mask', '')

        if not prompt_mask:
            return ''

        prompt = prompt_mask.format(context=context)
        while '  ' in prompt:
            prompt = prompt.replace('  ', ' ')

        return prompt

    def extract_text(self):
        obj = self.object

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

            ia_model = self.get_model_configured()
            answer = ia_model.generate_content(prompt)

            obj = self.object

            md = Metadata()
            md.content_object = obj
            metadata = {'genia': json.loads(answer.text)}
            metadata['genia']['model_name'] = self.ia_model_name
            metadata['genia']['template'] = 'table1'
            metadata['genia']['temperature'] = self.temperature
            metadata['genia']['top_k'] = self.top_k
            metadata['genia']['top_p'] = self.top_p
            md.metadata = metadata

            if settings.DEBUG:
                md.created = timezone.localtime()
                md.modified = timezone.localtime()

            md.save()

            if self.request:
                messages.add_message(
                    self.request, messages.SUCCESS,
                    _('Análise gerada com sucesso!'))

            return md

        except Exception as e:
            logger.error(e)

            if self.request:
                messages.add_message(
                    self.request, messages.ERROR,
                    _('Ocorreu erro na geração da análise!'))

