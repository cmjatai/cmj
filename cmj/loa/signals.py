import logging

from django.db.models.signals import post_save, pre_delete
from django.dispatch.dispatcher import receiver
from cmj.loa.models import AgrupamentoRegistroContabil, AgrupamentoEmendaLoa,\
    EmendaLoaRegistroContabil


logger = logging.getLogger(__name__)


@receiver(post_save, sender=AgrupamentoRegistroContabil, dispatch_uid='signal_post_agrupamentoregistrocontabil')
def signal_post_agrupamentoregistrocontabil(sender, instance, **kwargs):
    instance.agrupamento.sync()


@receiver(post_save, sender=AgrupamentoEmendaLoa, dispatch_uid='signal_post_agrupamentoemendaloa')
def signal_post_agrupamentoemendaloa(sender, instance, **kwargs):
    instance.agrupamento.sync()


@receiver(pre_delete, sender=AgrupamentoRegistroContabil, dispatch_uid='signal_pre_agrupamentoregistrocontabil')
def signal_pre_agrupamentoregistrocontabil(sender, instance, **kwargs):
    despesa = instance.despesa
    emendas = instance.agrupamento.emendas.values_list('id', flat=True)
    EmendaLoaRegistroContabil.objects.filter(
        despesa=despesa,
        emendaloa__in=emendas
    ).delete()


@receiver(pre_delete, sender=AgrupamentoEmendaLoa, dispatch_uid='signal_pre_agrupamentoemendaloa')
def signal_pre_agrupamentoemendaloa(sender, instance, **kwargs):
    instance.emendaloa.registrocontabil_set.all().delete()
