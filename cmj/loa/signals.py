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

    # LOA-FASE-067: quem muda a fase informa o usuário em instance._usuario_fase antes
    # do save(). O atributo é consumido aqui para não valer num save() seguinte.
    usuario = instance.__dict__.pop("_usuario_fase", None)

    if not instance.pk:
        return

    historico_fase = instance.emendaloahistoricofase_set.first()
    if not historico_fase or historico_fase.fase != instance.fase:
        if usuario is not None and not getattr(usuario, "is_authenticated", False):
            usuario = None
        historico_fase = instance.emendaloahistoricofase_set.create(
            fase=instance.fase, usuario=usuario
        )


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


# LOA-AGR-046: ao sair do agrupamento, a emenda mantém os registros contábeis que
# tinha por ele; não há mais signal que os apague na remoção do vínculo


def chaves_do_cartao(ids):
    """Chaves do cartão das emendas: uma para anônimo e outra para usuário
    logado (LOA-LST-040)."""
    return [
        make_template_fragment_key("l.el.l", [i, logado])
        for i in set(ids)
        if i
        for logado in (True, False)
    ]


def emendas_do_cartao(instance):
    """Ids das emendas cujo cartão na listagem mostra dados da instância.

    LOA-LST-041: só apaga o cartão de quem é afetado; model fora do mapa não
    apaga nada.
    """
    from django.core.exceptions import FieldDoesNotExist

    from cmj.loa.models import (
        Empenho,
        EmpenhoEmendaAjuste,
        Entidade,
        Loa,
        UnidadeOrcamentaria,
    )
    from sapl.materia.models import (
        DocumentoAcessorio,
        MateriaLegislativa,
        Tramitacao,
    )
    from sapl.parlamentares.models import Parlamentar

    emendas = EmendaLoa.all_objects.all_objects()

    if isinstance(instance, EmendaLoa):
        return [instance.id]
    if isinstance(instance, MateriaLegislativa):
        return list(emendas.filter(materia=instance).values_list("id", flat=True))
    if isinstance(instance, (Tramitacao, DocumentoAcessorio)):
        return list(
            emendas.filter(materia_id=instance.materia_id).values_list("id", flat=True)
        )
    if isinstance(instance, Empenho):
        return list(
            EmpenhoEmendaAjuste.objects.filter(empenho=instance).values_list(
                "emendaloa_id", flat=True
            )
        )
    for model, campo in (
        (Entidade, "entidade"),
        (UnidadeOrcamentaria, "unidade"),
        (Parlamentar, "parlamentares"),
        (Loa, "loa"),
    ):
        if isinstance(instance, model):
            return list(
                emendas.filter(**{campo: instance}).values_list("id", flat=True)
            )

    # Models que apontam para a emenda (FK ou M2M declarados neles)
    try:
        campo = instance._meta.get_field("emendaloa")
    except FieldDoesNotExist:
        return []
    if campo.auto_created:
        return []
    if campo.many_to_many:
        if not instance.pk:
            return []
        return list(instance.emendaloa.values_list("id", flat=True))
    return [instance.emendaloa_id] if instance.emendaloa_id else []


@receiver([post_save, post_delete])
def signal_loa_emendaloa_disable_cache(sender, **kwargs):
    if not sender or not hasattr(sender, "_meta"):
        return
    if sender._meta.app_label not in ("loa", "materia", "parlamentares"):
        return
    try:
        ids = emendas_do_cartao(kwargs.get("instance"))
        if ids:
            cache.delete_many(chaves_do_cartao(ids))
    except Exception as e:
        logger.error("Erro ao tentar invalidar cache: {}".format(e))
