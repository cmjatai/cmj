import logging

from django.apps.registry import apps
from django.db import models

from cmj.sigad.models import RelacionamentoEntreClasses
from drfautoapi.drfautoapi import ApiViewSetConstrutor, customize

logger = logging.getLogger(__name__)

ApiViewSetConstrutor.build_class([apps.get_app_config("sigad")])


@customize(RelacionamentoEntreClasses)
class _RelacionamentoEntreClassesViewSet:

    def perform_update(self, serializer):
        serializer.save()

        classe_referente = serializer.instance.referente
        classe_referenciada = serializer.instance.referenciada
        print(
            serializer.instance.id,
            serializer.instance.ordem,
            classe_referente,
            classe_referenciada,
        )
        count = classe_referente.referenciada_set.count()
        classe_referente.referenciada_set.exclude(id=serializer.instance.id).update(
            ordem=models.F("ordem") + count
        )

        pos = 0
        for ref in classe_referente.referenciada_set.all():
            if pos == serializer.instance.ordem:
                pos += 1
            if ref.referenciada == classe_referenciada:
                continue
            ref.ordem = pos
            ref.save()
            pos += 1
