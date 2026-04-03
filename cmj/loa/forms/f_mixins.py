import logging

from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.utils.translation import gettext_lazy as _
from django_filters import ModelMultipleChoiceFilter

from sapl.materia.models import MateriaLegislativa

logger = logging.getLogger(__name__)


class LoaParlModelMultipleChoiceFilter(ModelMultipleChoiceFilter):

    def get_queryset(self, request):
        if self.parent.loa.materia and self.parent.loa.materia.normajuridica():
            return self.parent.loa.parlamentares.filter(
                emendaloaparlamentar_set__isnull=False
            ).distinct()
        else:
            return self.parent.loa.parlamentares.all()


class MateriaCheckFormMixin:

    def clean(self):

        cleaned_data = super().clean()
        if not self.is_valid():
            return cleaned_data

        materia = cleaned_data["numero_materia"]
        ano_materia = cleaned_data["ano_materia"]
        tipo_materia = cleaned_data["tipo_materia"]

        if materia and ano_materia and tipo_materia:
            try:
                logger.debug(
                    "Tentando obter MateriaLegislativa %s nº %s/%s."
                    % (tipo_materia, materia, ano_materia)
                )
                materia = MateriaLegislativa.objects.get(
                    numero=materia, ano=ano_materia, tipo=tipo_materia
                )
            except ObjectDoesNotExist:
                msg = _(
                    "A matéria %s nº %s/%s não existe no cadastro"
                    " de matérias legislativas." % (tipo_materia, materia, ano_materia)
                )
                logger.error(
                    "A MateriaLegislativa %s nº %s/%s não existe no cadastro"
                    " de matérias legislativas." % (tipo_materia, materia, ano_materia)
                )
                raise ValidationError(msg)
            else:
                logger.info(
                    "MateriaLegislativa %s nº %s/%s obtida com sucesso."
                    % (tipo_materia, materia, ano_materia)
                )
                cleaned_data["materia"] = materia

        else:
            cleaned_data["materia"] = None
