
from cmj.celery import app

from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)


def task_register_emendaloa_proposicao_function(*args, **kwargs):
    from cmj.loa.models import Loa, EmendaLoa
    from sapl.base.models import OperadorAutor

    loa_id = args[0]
    user_id = args[1]

    loa = Loa.objects.get(id=loa_id)

    autor_operado = OperadorAutor.objects.filter(user_id=user_id).first()
    if not autor_operado:
        logger.error(f"User ID: {user_id} não está associado a nenhum Autor.")
        return
    autor_operado = autor_operado.autor
    operadores = OperadorAutor.objects.filter(autor=autor_operado).values_list('user_id', flat=True)

    emendas = loa.emendaloa_set.filter(
        fase=EmendaLoa.LIBERACAO_CONTABIL,
        owner_id__in=operadores
    ).order_by('tipo', 'id').distinct()


    for emenda in emendas:
        md = emenda.metadata or {}
        md['register_emendaloa_proposicao_task'] = {
            'user_id': user_id,
        }
        emenda.metadata = md
        emenda.save(update_fields=['metadata'])


    for emenda in emendas:
        try:
            if emenda.materia:
                logger.warning(f"EmendaLoa ID: {emenda.id} já está vinculada à Matéria ID: {emenda.materia.id}, pulando registro.")
                continue

            if emenda.proposicao and (emenda.proposicao.data_envio or emenda.proposicao.data_recebimento):
                logger.warning(f"EmendaLoa ID: {emenda.id} já está vinculada à Proposição ID: {emenda.proposicao.id} que já foi enviada ou aprovada, pulando registro.")
                continue

            emenda.registrar_proposicao()
        except Exception as e:
            metadata = emenda.metadata or {}
            metadata.pop('register_emendaloa_proposicao_task', None)
            emenda.metadata = metadata
            emenda.save(update_fields=['metadata'])
            logger.error(f"Erro ao registrar proposição para EmendaLoa ID: {emenda.id}: {e}")

    logger.info(f"Registering emendaloa proposicao for LOA ID: {loa_id} by User ID: {user_id}")


@app.task(queue='cq_base', bind=True)
def task_register_emendaloa_proposicao(self, *args, **kwargs):
    return task_register_emendaloa_proposicao_function(*args, **kwargs)