import time
from django.conf import settings
from cmj.celery import app as cmj_celery_app
from cmj.search.models import Embedding
from sapl.compilacao.models import TextoArticulado, TipoDispositivo

from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)

def task_sync_embeddings_textoarticulado_function(ta_ids=[]):

    logger.info(f'Starting task_sync_embeddings_textoarticulado_function for TextoArticulado IDs: {ta_ids}'    )

    for ta in TextoArticulado.objects.filter(id__in=ta_ids):
        logger.info(f'T.A.: {ta.id} Iniciando processamento de chunking e embeddings.')

        dispositivos = ta.generate_chunks()

        #count_embedding = Embedding.objects.filter(total_tokens=0).count()
        #logger.info(f'Total de dispositivos para chunking: {len(dispositivos)}')

        for emb in Embedding.objects.filter(
            total_tokens=0
        ):
            emb.update_total_tokens()
            logger.info(f'T.A.: {ta.id} Embedding: {emb.id} Updated total tokens: {emb.total_tokens},')
            time.sleep(0.1)

        for emb in Embedding.objects.filter(
            total_tokens__gt=0,
            vetor1536__isnull=True
        ):
            emb.generate_embedding()
            logger.info(f'T.A.: {ta.id} Embedding: {emb.id} Generated embedding.')
            time.sleep(0.1)

        continue

        for i, (d, context) in enumerate(dispositivos):
            print(f'[{i+1}/{len(dispositivos)}] Dispositivo ID {d.id} - Nivel {d.nivel} - Tipo {d.tipo_dispositivo} - Ordem {d.ordem}')
            print(f'Rendered Text: {context["rendered"][:250]}...')
            print(f'Chunks: {len(context["chunks"])}')
            for j, chunk in enumerate(context["chunks"]):
                print(f'  Chunk {j+1} ({len(chunk.split())} words): {chunk[:250]}...')
            print('-' * 150)

@cmj_celery_app.task(queue='cq_base', bind=True)
def task_sync_embeddings_textoarticulado(self, textoarticulado_ids=[]):

    #if settings.DEBUG:
    #    return

    task_sync_embeddings_textoarticulado_function(ta_ids=textoarticulado_ids)