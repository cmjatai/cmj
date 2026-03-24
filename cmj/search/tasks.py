import logging
import time
from django.conf import settings
from django.db.models import Q
from cmj.celery import app as cmj_celery_app
from cmj.search.models import Embedding
from sapl.compilacao.models import Dispositivo, TextoArticulado

from sapl.norma.models import NormaJuridica

from celery.utils.log import get_task_logger

logger = get_task_logger(__name__) if not settings.DEBUG else logging.getLogger(__name__)

def task_sync_embeddings_textoarticulado_function(ta_ids=[]):

    logger.info(f'Starting task_sync_embeddings_textoarticulado_function for TextoArticulado IDs: {ta_ids}'    )

    ta_ids = Dispositivo.objects.filter(
        Q(ta__id__in=ta_ids) | Q(ta_publicado__id__in=ta_ids)
    ).values_list('ta__id', flat=True).order_by('ta__id').distinct()

    # Deleta embeddings de dispositivos que possuem dispositivo subsequente
    Embedding.objects.filter(
        dispositivo_set__dispositivo_subsequente__isnull=False,
        dispositivo_set__ta__id__in=ta_ids
        ).delete()

    # Deleta embeddings de dispositivos relacionados a TAs revogados integralmente
    textos_revogados = TextoArticulado.objects.filter(
        texto_articulado__norma_relacionada__tipo_vinculo__revoga_integralmente=True
    ).values_list('id', flat=True).order_by('id').distinct()
    Embedding.objects.filter(
        dispositivo_set__ta__id__in=textos_revogados
        ).delete()

    for ta in TextoArticulado.objects.filter(id__in=ta_ids):
        logger.info(f'T.A.: {ta.id} Iniciando processamento de chunking e embeddings.')

        if ta.is_revogado():
            Embedding.objects.filter(
                dispositivo_set__ta=ta
            ).delete()
            logger.info(f'T.A.: {ta.id} Está revogado. Embeddings relacionados foram deletados.')
            continue

        dispositivos = ta.generate_chunks()
        dispositivo_set__in=list(map(lambda d: d[0].id if d and d[0] and hasattr(d[0], 'id') else None, dispositivos))

        #count_embedding = Embedding.objects.filter(total_tokens=0).count()
        #logger.info(f'Total de dispositivos para chunking: {len(dispositivos)}')

        for emb in Embedding.objects.filter(
            total_tokens=0,
            dispositivo_set__in=dispositivo_set__in
        ):
            emb.update_total_tokens()
            logger.info(f'T.A.: {ta.id} Embedding: {emb.id} Updated total tokens: {emb.total_tokens},')
            #time.sleep(0.1)

        for emb in Embedding.objects.filter(
            total_tokens__gt=0,
            vetor1536__isnull=True,
            dispositivo_set__in=dispositivo_set__in
        ):
            emb.generate_embedding()
            emb.vetor = None
            emb.save()
            logger.info(f'T.A.: {ta.id} Embedding: {emb.id} Generated embedding.')
            #time.sleep(0.1)

        continue

        for i, (d, context) in enumerate(dispositivos):
            print(f'[{i+1}/{len(dispositivos)}] Dispositivo ID {d.id} - Nivel {d.nivel} - Tipo {d.tipo_dispositivo} - Ordem {d.ordem}')
            print(f'Rendered Text: {context["rendered"][:250]}...')
            print(f'Chunks: {len(context["chunks"])}')
            for j, chunk in enumerate(context["chunks"]):
                print(f'  Chunk {j+1} ({len(chunk.split())} words): {chunk[:250]}...')
            print('-' * 150)

@cmj_celery_app.task(queue='cq_base', bind=True)
def task_sync_embeddings_textoarticulado(self, textoarticulado_ids):

    #if settings.DEBUG:
    #    return

    try:
        task_sync_embeddings_textoarticulado_function(ta_ids=textoarticulado_ids)
    except Exception as e:
        logger.error(f'Erro ao executar task_sync_embeddings_textoarticulado: {e}')