import logging

from django.core.cache import cache
from django.core.cache.utils import make_template_fragment_key
from django.db.models.signals import post_delete, post_save, pre_delete
from django.dispatch.dispatcher import receiver

from cmj.loa.models import (
    AgrupamentoEmendaLoa,
    AgrupamentoRegistroContabil,
    EmendaLoa,
    EmendaLoaRegistroContabil,
)

logger = logging.getLogger(__name__)


@receiver(
    post_save,
    sender=EmendaLoa,
    dispatch_uid="signal_postsave_emendaloa",
)
def signal_postsave_emendaloa(sender, instance, **kwargs):

    historico_fase = instance.emendaloahistoricofase_set.first()
    if not historico_fase or historico_fase.fase != instance.fase:
        historico_fase = instance.emendaloahistoricofase_set.create(fase=instance.fase)


@receiver(
    post_save,
    sender=AgrupamentoRegistroContabil,
    dispatch_uid="signal_post_agrupamentoregistrocontabil",
)
def signal_post_agrupamentoregistrocontabil(sender, instance, **kwargs):
    instance.agrupamento.sync()


@receiver(
    post_save,
    sender=AgrupamentoEmendaLoa,
    dispatch_uid="signal_post_agrupamentoemendaloa",
)
def signal_post_agrupamentoemendaloa(sender, instance, **kwargs):
    instance.agrupamento.sync()


@receiver(
    pre_delete,
    sender=AgrupamentoRegistroContabil,
    dispatch_uid="signal_pre_agrupamentoregistrocontabil",
)
def signal_pre_agrupamentoregistrocontabil(sender, instance, **kwargs):
    despesa = instance.despesa
    emendas = instance.agrupamento.emendas.values_list("id", flat=True)
    EmendaLoaRegistroContabil.objects.filter(
        despesa=despesa, emendaloa__in=emendas
    ).delete()


@receiver(
    pre_delete,
    sender=AgrupamentoEmendaLoa,
    dispatch_uid="signal_pre_agrupamentoemendaloa",
)
def signal_pre_agrupamentoemendaloa(sender, instance, **kwargs):
    instance.emendaloa.registrocontabil_set.all().delete()


@receiver([post_save, post_delete])
def signal_loa_emendaloa_disable_cache(sender, **kwargs):
    if sender and hasattr(sender, "_meta"):
        if sender._meta.app_label in ("loa", "sessao", "norma", "materia"):
            try:
                # keys com cache semanal
                inst = kwargs.get("instance", {})
                insts = None
                if inst:
                    if hasattr(inst, "emendaloa_id") and inst.emendaloa_id:
                        inst = inst.emendaloa_id
                    elif (
                        hasattr(inst, "emendaloa")
                        and inst.emendaloa
                        and hasattr(inst.emendaloa, "id")
                    ):
                        inst = inst.emendaloa.id
                    elif (
                        hasattr(inst, "emendaloa")
                        and inst.emendaloa
                        and hasattr(inst.emendaloa, "exists")
                        and inst.emendaloa.exists()
                    ):
                        insts = inst.emendaloa.all().values_list("id", flat=True)
                    elif hasattr(inst, "id"):
                        inst = inst.id
                    else:
                        inst = None

                    if inst:
                        key = make_template_fragment_key("l.el.l", [inst])
                        cache.delete(key)
                    if insts:
                        for i in insts:
                            key = make_template_fragment_key("l.el.l", [i])
                            cache.delete(key)

            except Exception as e:
                # logger.error(
                #    "Erro ao tentar invalidar cache de matéria: {}".format(e))
                pass
