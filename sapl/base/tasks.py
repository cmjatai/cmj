import logging
from cmj.celery import app
from sapl.base.email_utils import do_envia_email_tramitacao
from sapl.materia.models import StatusTramitacao, UnidadeTramitacao, MateriaLegislativa
from sapl.protocoloadm.models import StatusTramitacaoAdministrativo, DocumentoAdministrativo

logger = logging.getLogger(__name__)

@app.task(queue='cq_base')
def task_envia_email_tramitacao(kwargs):
    print(f'task_envia_email_tramitacao: {kwargs}')
    log.info(f'task_envia_email_tramitacao: {kwargs}')

    tipo = kwargs.get("tipo")
    doc_mat_id = kwargs.get("doc_mat_id")
    tramitacao_status_id = kwargs.get("tramitacao_status_id")
    tramitacao_unidade_tramitacao_destino_id = kwargs.get(
        "tramitacao_unidade_tramitacao_destino_id")
    base_url = kwargs.get("base_url")

    if tipo == 'documento':
        doc_mat = DocumentoAdministrativo.objects.get(id=doc_mat_id)
        status = StatusTramitacaoAdministrativo.objects.get(
            id=tramitacao_status_id)

    elif tipo == 'materia':
        doc_mat = MateriaLegislativa.objects.get(id=doc_mat_id)
        status = StatusTramitacao.objects.get(id=tramitacao_status_id)

    unidade_destino = UnidadeTramitacao.objects.get(
        id=tramitacao_unidade_tramitacao_destino_id)

    do_envia_email_tramitacao(base_url, tipo, doc_mat, status, unidade_destino)
