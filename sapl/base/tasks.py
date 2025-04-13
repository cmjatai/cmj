import logging
from tracemalloc import start
from cmj.celery import app
from cmj.utils import start_task
from sapl.base.email_utils import do_envia_email_tramitacao
from sapl.materia.models import AssuntoMateria, MateriaAssunto, StatusTramitacao, UnidadeTramitacao, MateriaLegislativa
from sapl.protocoloadm.models import StatusTramitacaoAdministrativo, DocumentoAdministrativo

from cmj.genia import GoogleGenerativeIA
from sapl.materia.models import MateriaLegislativa
from sapl.base.models import Metadata
from django.db.models import Q
from django.utils import timezone


logger = logging.getLogger(__name__)


@app.task(queue='cq_base')
def task_envia_email_tramitacao(kwargs):
    print(f'task_envia_email_tramitacao: {kwargs}')
    logger.info(f'task_envia_email_tramitacao: {kwargs}')

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


def task_classifica_materialegislativa_function():
    """
    Função para classificar o materias legislativas que seus tipos possuem prompt definido.
    """
    gen = GoogleGenerativeIA()
    gen.model = MateriaLegislativa

    ultimo_metadata = Metadata.objects.filter(
        content_type__model='materialegislativa').order_by('-id').first()
    if ultimo_metadata:
        tempo = timezone.now() - ultimo_metadata.created
        if tempo.seconds < 60:
            return

    metadata_de_materias = Metadata.objects.filter(
        content_type__model='materialegislativa').values_list('object_id', flat=True)

    materias = MateriaLegislativa.objects.exclude(
            Q(tipo__prompt='') | Q(tipo__prompt=None) | Q(id__in=metadata_de_materias),
        ).filter(
            ano__lte=2024
        ).values_list('id', flat=True).order_by('-ano', '-numero')


    md = None
    for mid in materias[:1]:
        gen.object = mid

        analise = gen.get_analise()

        if analise:
            continue

        md = gen.run(action='generate')

        if md and md.metadata:
            temas = md.metadata.get('genia', {}).get('temas', [])

            obj = md.content_object

            for tema in temas:
                assunto, created = AssuntoMateria.objects.get_or_create(
                    assunto=tema
                )

                mass, created = MateriaAssunto.objects.get_or_create(
                    assunto=assunto,
                    materia=obj
                )
            obj.save()



@app.task(queue='cq_base', bind=True)
def task_classifica_materialegislativa(self, *args, **kwargs):

    try:
        task_classifica_materialegislativa_function()
    except Exception as e:
        logger.error(f'Erro ao executar task_classifica_materialegislativa: {e}')

    start_task(
        'sapl.base.tasks.task_classifica_materialegislativa',
        task_classifica_materialegislativa,
        timezone.now() + timezone.timedelta(seconds=120)
    )
