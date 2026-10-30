import logging

from celery.utils.log import get_task_logger
from django.conf import settings
from django.db.models import Q

from cmj.celery import app as cmj_celery_app
from cmj.search.models import Embedding
from sapl.compilacao.models import Dispositivo, TextoArticulado

logger_task = get_task_logger(__name__)
logger_exec = logging.getLogger(__name__)


def logger_info(msg, logger=logger_task):
    if hasattr(logger, "info"):
        logger.info(msg)
    elif hasattr(logger, "write"):
        logger.write(msg)
    else:
        print(msg)


def task_sync_embeddings_textoarticulado_function(
    ta_ids=[], strategy=None, vectorize=True, logger=logger_task, ignore_ta_ids=set()
):
    if not ta_ids:
        return set()
    ta_ids = set(ta_ids) - set(ignore_ta_ids)
    """
    Reindexa os T.A. (chunks) e, se `vectorize`, conta tokens e vetoriza os
    embeddings pendentes (chamadas à API do Gemini).
    """
    strategy = strategy or getattr(settings, "RAG_CHUNK_STRATEGY", "v1")
    logger_info(
        f"Starting task_sync_embeddings_textoarticulado_function ({strategy}) for TextoArticulado IDs: {ta_ids}",
        logger=logger,
    )

    ta_ids = (
        Dispositivo.objects.filter(
            (Q(ta__id__in=ta_ids) | Q(ta_publicado__id__in=ta_ids)) & ~Q(ta__id__in=ignore_ta_ids)
        )
        .values_list("ta__id", flat=True)
        .order_by("ta__id")
        .distinct()
    )

    # Deleta embeddings de dispositivos que possuem dispositivo subsequente
    Embedding.objects.filter(
        dispositivo_set__dispositivo_subsequente__isnull=False,
        dispositivo_set__ta__id__in=ta_ids,
    ).delete()

    # Deleta embeddings de dispositivos relacionados a TAs revogados integralmente
    textos_revogados = (
        TextoArticulado.objects.filter(
            texto_articulado__norma_relacionada__tipo_vinculo__revoga_integralmente=True
        )
        .values_list("id", flat=True)
        .order_by("id")
        .distinct()
    )
    Embedding.objects.filter(dispositivo_set__ta__id__in=textos_revogados).delete()

    for ta in TextoArticulado.objects.filter(id__in=ta_ids):
        logger_info(
            f"T.A.: {ta.id} Iniciando processamento de chunking e embeddings.",
            logger=logger,
        )

        if ta.is_revogado():
            Embedding.objects.filter(dispositivo_set__ta=ta).delete()
            logger_info(
                f"T.A.: {ta.id} Está revogado. Embeddings relacionados foram deletados.",
                logger=logger,
            )
            continue

        if strategy == "v2":
            chunks = ta.generate_chunks_v2()
            dispositivo_set__in = sorted({c.raiz_pk for c in chunks})
        else:
            dispositivos = ta.generate_chunks()
            dispositivo_set__in = list(
                map(
                    lambda d: d[0].id if d and d[0] and hasattr(d[0], "id") else None,
                    dispositivos,
                )
            )

        # count_embedding = Embedding.objects.filter(total_tokens=0).count()
        # logger.info(f'Total de dispositivos para chunking: {len(dispositivos)}')

        if not vectorize:
            continue

        da_estrategia = Embedding.strategy_filter(strategy)

        for emb in Embedding.objects.filter(
            da_estrategia, total_tokens=0, dispositivo_set__in=dispositivo_set__in
        ):
            emb.update_total_tokens()
            logger_info(
                f"T.A.: {ta.id} Embedding: {emb.id} Updated total tokens: {emb.total_tokens},",
                logger=logger,
            )
            # time.sleep(0.1)

        qs_to_batch_process = Embedding.objects.filter(
            da_estrategia,
            vetor1536__isnull=True,
            dispositivo_set__in=dispositivo_set__in,
        )

        Embedding.generate_embeddings_for_queryset(qs_to_batch_process)

    return ta_ids


@cmj_celery_app.task(queue="cq_base", bind=True)
def task_sync_embeddings_textoarticulado(self, textoarticulado_ids):

    # if settings.DEBUG:
    #    return

    try:
        task_sync_embeddings_textoarticulado_function(ta_ids=textoarticulado_ids)
    except Exception as e:
        logger_task.error(f"Erro ao executar task_sync_embeddings_textoarticulado: {e}")
