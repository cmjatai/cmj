import json
import logging

import yaml
from django.conf import settings
from django.contrib import messages
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from cmj.core.models import IAQuota
from cmj.utils.genia.base import IAGenaiBase
from cmj.utils.genia.extracao import extract_clean_text_from_path
from sapl.base.models import Metadata

logger = logging.getLogger(__name__)


class IAClassificacaoMateriaService(IAGenaiBase):
    """
    Classificação de um registro (hoje, MateriaLegislativa) a partir dos seus
    PDFs e do prompt YAML do tipo. O resultado fica em Metadata, chave "genia".

    Spec: docs/specs/genia/classificacao-materia.md
    """

    quota_service_name = IAQuota.ServicosAutorizados.IA_CLASSIFICACAO_MATERIA_SERVICE

    METADATA_KEY = "genia"
    METADATA_TEMPLATE = "table1"

    _model = None  # Model from app django
    _content_type = None  # ContentType from app django
    _object = None  # Object from app django

    @property
    def model(self):
        if not self._model:
            raise Exception("Model not configured")

        return self._model

    @model.setter
    def model(self, model):
        self._model = model
        self._content_type = ContentType.objects.get_for_model(model)

    @property
    def content_type(self):
        if not self._content_type:
            raise Exception("ContentType not configured")

        return self._content_type

    @content_type.setter
    def content_type(self, content_type):
        self._content_type = content_type

    @property
    def object(self):
        if not self._object:
            raise Exception("Object not configured")
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
                raise Exception("Registro não encontrado.")
        else:
            raise Exception("Registro não encontrado.")

    def run(self, *args, **kwargs):
        """
        Executa a ação de IA, que pode ser gerar ou deletar
        """
        self.request = kwargs.get("request", {})
        self.GET = self.request.GET if hasattr(self.request, "GET") else {}
        if not self.GET:
            self.GET = {
                "action": kwargs.get("action", "generate"),
                "temperature": kwargs.get("temperature", self.temperature),
                "top_k": kwargs.get("top_k", self.top_k),
                "top_p": kwargs.get("top_p", self.top_p),
            }
            self.action = self.GET.get("action", "generate")
        else:
            self.action = self.GET.get("ia_run", "generate")

        if self.action.startswith("generate"):
            self.delete()
            self.temperature = self.GET.get("temperature", self.temperature)
            self.top_k = self.GET.get("top_k", self.top_k)
            self.top_p = self.GET.get("top_p", self.top_p)
            return self.generate()
        elif self.action == "delete":
            self.delete()
            if self.request:
                messages.add_message(
                    self.request, messages.SUCCESS, _("Análise removida com sucesso!")
                )

    def delete(self):
        obj = self.object
        Metadata.objects.filter(
            object_id=obj.id, content_type=self.content_type
        ).delete()

    def has_analise(self):
        """
        Verifica se o objeto já possui análise gerada
        """
        return self.get_analise() is not None

    def get_analise(self):
        """
        Retorna a análise gerada, ou None se não houver
        """
        metadata = Metadata.objects.filter(
            object_id=self.object.id, content_type=self.content_type
        ).first()

        if not metadata or self.METADATA_KEY not in metadata.metadata:
            return None

        return metadata.metadata[self.METADATA_KEY]

    def make_prompt(self, context):
        obj = self.object

        prompt_mask = obj.tipo.prompt
        if not prompt_mask:
            return ""

        yaml_data = yaml.load(prompt_mask, Loader=yaml.FullLoader)

        status = False
        for prompt_object in yaml_data["PROMPTs"]:
            status = prompt_object["status"]
            if status:
                break

        if not status:
            return ""

        if self.action == "generate":
            self.ia_model_name = prompt_object.get("ia_model_name", self.ia_model_name)
            self.temperature = prompt_object.get("temperature", self.temperature)
            self.top_k = prompt_object.get("top_k", self.top_k)
            self.top_p = prompt_object.get("top_p", self.top_p)
        elif self.action == "generate_custom":
            self.ia_model_name = prompt_object.get("ia_model_name", self.ia_model_name)
            self.temperature = float(self.GET.get("temperature", self.temperature))
            self.top_p = float(self.GET.get("top_p", self.top_p))
            self.top_k = int(self.GET.get("top_k", self.top_k))

        prompt_mask = prompt_object.get("mask", "")

        if not prompt_mask:
            return ""

        prompt = prompt_mask.format(context=context)
        while "  " in prompt:
            prompt = prompt.replace("  ", " ")

        return prompt

    def extract_text(self):
        obj = self.object

        text = ""
        for fn in obj.FIELDFILE_NAME:
            if not getattr(obj, fn):
                continue

            text += extract_clean_text_from_path(getattr(obj, fn).path)
        return text

    def generate(self):
        try:
            context = self.extract_text()
            prompt = self.make_prompt(context=context)

            if not prompt:
                return

            answer = self.generate_content(prompt, ascending=False)

            obj = self.object

            md = Metadata()
            md.content_object = obj
            analise = json.loads(answer.text)
            analise.update(
                model_name=self.ia_model_name,
                template=self.METADATA_TEMPLATE,
                temperature=self.temperature,
                top_k=self.top_k,
                top_p=self.top_p,
            )
            md.metadata = {self.METADATA_KEY: analise}

            if settings.DEBUG:
                md.created = timezone.localtime()
                md.modified = timezone.localtime()

            md.save()

            if self.request:
                messages.add_message(
                    self.request, messages.SUCCESS, _("Análise gerada com sucesso!")
                )

            return md

        except Exception as e:
            logger.error(e)

            if self.request:
                messages.add_message(
                    self.request,
                    messages.ERROR,
                    _("Ocorreu erro na geração da análise!"),
                )
