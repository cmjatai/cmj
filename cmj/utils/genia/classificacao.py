import json
import logging

import yaml
from django.conf import settings
from django.contrib import messages
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from cmj.core.models import IAQuota
from cmj.utils.genia.base import IAGenaiBase, IAQuotaUnavailableError
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
        Executa a ação de IA: "generate", "generate_custom" ou "delete".
        Com `request`, a ação vem de `?ia_run=` e os parâmetros de
        "generate_custom", da query string. Sem `request`, vêm dos kwargs.
        """
        request = kwargs.get("request")
        self.request = request if hasattr(request, "GET") else None

        if self.request:
            self.GET = self.request.GET
            self.action = self.GET.get("ia_run") or "generate"
        else:
            self.GET = {
                k: kwargs[k] for k in ("temperature", "top_k", "top_p") if k in kwargs
            }
            self.action = kwargs.get("action") or "generate"

        if self.action.startswith("generate"):
            return self.generate()
        elif self.action == "delete":
            self.delete()
            self.add_message(messages.SUCCESS, _("Análise removida com sucesso!"))

    def add_message(self, level, message):
        if self.request:
            messages.add_message(self.request, level, message)

    def get_metadata(self):
        """Metadata do objeto (único por content_type e object_id), ou None."""
        return Metadata.objects.filter(
            object_id=self.object.id, content_type=self.content_type
        ).first()

    def delete(self):
        """
        Remove só a chave "genia". O Metadata é apagado se ficar vazio.
        """
        md = self.get_metadata()
        if not md or self.METADATA_KEY not in (md.metadata or {}):
            return

        md.metadata.pop(self.METADATA_KEY)
        if md.metadata:
            md.save()
        else:
            md.delete()

    def has_analise(self):
        """
        Verifica se o objeto já possui análise gerada
        """
        return self.get_analise() is not None

    def get_analise(self):
        """
        Retorna a análise gerada, ou None se não houver
        """
        md = self.get_metadata()
        return (md.metadata or {}).get(self.METADATA_KEY) if md else None

    def save_analise(self, analise):
        """
        Grava a análise na chave "genia", preservando as outras chaves do
        Metadata do objeto.
        """
        md = self.get_metadata()
        if not md:
            md = Metadata()
            md.content_object = self.object

        md.metadata = {**(md.metadata or {}), self.METADATA_KEY: analise}

        if settings.DEBUG:
            if not md.pk:
                md.created = timezone.localtime()
            md.modified = timezone.localtime()

        md.save()
        return md

    def get_prompt_object(self):
        """
        Primeiro item ativo da lista `PROMPTs` do YAML do tipo, ou None.
        """
        prompt_yaml = self.object.tipo.prompt
        if not prompt_yaml:
            return None

        yaml_data = yaml.safe_load(prompt_yaml) or {}

        for prompt_object in yaml_data.get("PROMPTs") or []:
            if prompt_object.get("status"):
                return prompt_object
        return None

    def set_generation_params(self, prompt_object):
        """
        "generate" usa o YAML e os padrões da classe; "generate_custom", a
        query string (ou os kwargs de `run`). Levanta ValueError ou TypeError
        para valor inválido.
        """
        source = self.GET if self.action == "generate_custom" else prompt_object

        self.temperature = float(source.get("temperature", self.temperature))
        self.top_k = int(source.get("top_k", self.top_k))
        self.top_p = float(source.get("top_p", self.top_p))

    def make_prompt(self, prompt_object, context):
        prompt = prompt_object["mask"].format(context=context)
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
        """
        Gera a análise e só então substitui a anterior. Sem prompt ativo, sem
        cota, com parâmetro inválido ou com erro, a análise anterior fica.
        """
        try:
            prompt_object = self.get_prompt_object()
            if not prompt_object or not prompt_object.get("mask"):
                return

            try:
                self.set_generation_params(prompt_object)
            except (TypeError, ValueError):
                self.add_message(
                    messages.ERROR,
                    _("Parâmetros de geração inválidos (temperature, top_k, top_p)."),
                )
                return

            quota = self.retrieve_quota_if_available(ascending=False)

            prompt = self.make_prompt(prompt_object, context=self.extract_text())
            answer = self.generate_content(prompt, quota=quota)

            analise = json.loads(answer.text)
            analise.update(
                model_name=self.ia_model_name,
                template=self.METADATA_TEMPLATE,
                temperature=self.temperature,
                top_k=self.top_k,
                top_p=self.top_p,
            )
            md = self.save_analise(analise)

            self.add_message(messages.SUCCESS, _("Análise gerada com sucesso!"))
            return md

        except IAQuotaUnavailableError as e:
            logger.warning(e)
            self.add_message(
                messages.WARNING,
                _(
                    "Nenhuma cota de I.A. disponível no momento. "
                    "A análise anterior foi mantida. Tente novamente mais tarde."
                ),
            )

        except Exception as e:
            logger.error(e)
            self.add_message(messages.ERROR, _("Ocorreu erro na geração da análise!"))
