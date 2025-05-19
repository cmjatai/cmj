
from tracemalloc import start
from cmj.celery import app as cmj_celery_app
from cmj.utils import start_task
from sapl import materia
from sapl.base.email_utils import do_envia_email_tramitacao
from sapl.materia.models import AnaliseSimilaridade, AssuntoMateria, MateriaAssunto, StatusTramitacao, UnidadeTramitacao, MateriaLegislativa
from sapl.parlamentares.models import Legislatura
from sapl.protocoloadm.models import StatusTramitacaoAdministrativo, DocumentoAdministrativo

from cmj.genia import IAAnaliseSimilaridadeService, IAClassificacaoMateriaService
from sapl.materia.models import MateriaLegislativa
from sapl.base.models import Metadata
from django.db.models import Q
from django.utils import timezone

from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)


@cmj_celery_app.task(queue='cq_base')
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
    gen = IAClassificacaoMateriaService()
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



@cmj_celery_app.task(queue='cq_base', bind=True)
def task_classifica_materialegislativa(self, *args, **kwargs):
    # desativada, não sendo chamada - ja processou toda a base de antes de 2025.
    try:
        task_classifica_materialegislativa_function()
    except Exception as e:
        logger.error(f'Erro ao executar task_classifica_materialegislativa: {e}')

    start_task(
        'sapl.base.tasks.task_classifica_materialegislativa',
        task_classifica_materialegislativa,
        timezone.now() + timezone.timedelta(seconds=120)
    )

def task_analise_similaridade_entre_materias_function():
    # Função para analisar a similaridade entre matérias

    legislatura_atual = Legislatura.cache_legislatura_atual()
    if not legislatura_atual:
        return

    def gera_registros_de_analise_vazios():
        requerimentos = MateriaLegislativa.objects.filter(
            tipo_id=3, ano__gte=legislatura_atual['data_inicio'].year, ano__lte=legislatura_atual['data_fim'].year
        ).prefetch_related('autores', 'assuntos'
                        ).order_by('-id').distinct()

        # cria uma lista de tuplas contendo o id do requerimento, uma tumpla com os ids dos autores e uma tupla com os ids dos assuntos
        requerimentos_ids = []
        for requerimento in requerimentos:
            requerimentos_ids.append(
                (requerimento.id, tuple(requerimento.autores.values_list('id', flat=True)),
                tuple(requerimento.assuntos.values_list('id', flat=True)))
            )

        # ordena a lista pela quantidade de assuntos
        requerimentos_ids = sorted(requerimentos_ids, key=lambda x: (len(x[2]), len(x[1])), reverse=True)

        # ordena internamente cada tupla e assuntos
        for i, r in enumerate(requerimentos_ids):
            requerimentos_ids[i] = (r[0], tuple(sorted(r[1])), tuple(sorted(r[2])))

        # cria uma lista dois a dois de todos os requerimentos com todos menos com ele mesmo, e se o autor for o mesmo
        requerimentos_comparacao = {}
        for i, r1 in enumerate(requerimentos_ids):
            for j, r2 in enumerate(requerimentos_ids):
                if i == j:
                    continue
                if r1[1] == r2[1]:
                    continue
                if len(r1[1]) >=5 or len(r2[1]) >= 5:
                    continue
                set1 = set(r1[2])
                set2 = set(r2[2])
                intersection = set1.intersection(set2)
                requerimentos_comparacao[(r1[0], r2[0])] = tuple(intersection)

        # remove os requerimentos que possuem chave invertida
        # ou seja, dado (a, b), remove (b, a)

        requerimentos_comparados = {}
        for k, v in requerimentos_comparacao.items():
            if (k[1], k[0]) in requerimentos_comparados:
                continue
            requerimentos_comparados[k] = v

        # ordena a comparação pela quantidade de elementos na interseção
        requerimentos_comparados = sorted(requerimentos_comparados.items(), key=lambda x: len(x[1]), reverse=True)

        for i, r in enumerate(requerimentos_comparados):
            analise, created = AnaliseSimilaridade.objects.get_or_create(
                materia_1_id=r[0][0],
                materia_2_id=r[0][1],
            )
            analise.qtd_assuntos_comuns = len(r[1])
            analise.save()
        return

    # recupera uma analise para enviar a ia.
    analise = AnaliseSimilaridade.objects.filter(
        similaridade = -1
    ).order_by('-qtd_assuntos_comuns').first()
    if not analise:
        gera_registros_de_analise_vazios()
        analise = AnaliseSimilaridade.objects.filter(similaridade = -1).first()
    if not analise:
        return

    gen = IAAnaliseSimilaridadeService()
    gen.run(analise)


@cmj_celery_app.task(queue='cq_base', bind=True)
def task_analise_similaridade_entre_materias(self, *args, **kwargs):

    #restart = start_task(
    #    'sapl.base.tasks.task_analise_similaridade_entre_materias',
    #    task_analise_similaridade_entre_materias,
    #    timezone.now() + timezone.timedelta(seconds=120)
    #)

    #if restart:
    logger.info('Executando...')
    try:
        task_analise_similaridade_entre_materias_function()
        pass
    except Exception as e:
        logger.error(f'Erro ao executar task_analise_similaridade_entre_materias: {e}')

