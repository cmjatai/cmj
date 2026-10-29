from django.conf import settings
from django.contrib.postgres.search import SearchVector
from django.core.management.base import BaseCommand

from cmj.search.models import Embedding
from cmj.search.tasks import task_sync_embeddings_textoarticulado_function
from sapl.compilacao.models import (
    CHUNK_TIPOS_INDIVIDUALIZAVEIS,
    Dispositivo,
    TextoArticulado,
)


class Command(BaseCommand):
    help = (
        "Completa o índice do chat RAG: reindexa (chunks) textos articulados "
        "publicados e vetoriza os embeddings pendentes (sem vetor1536)."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--ta-ids",
            nargs="+",
            type=int,
            default=[],
            help="Reindexa estes Textos Articulados.",
        )
        parser.add_argument(
            "--tipos",
            nargs="+",
            default=[],
            metavar="TIPO",
            help="Reindexa os T.A. publicados que possuem dispositivos vigentes "
            'desses tipos (ex.: "Anexo" "Texto Não Estruturado").',
        )
        parser.add_argument(
            "--sem-embedding",
            action="store_true",
            help="Reindexa os T.A. publicados que não têm nenhum embedding.",
        )
        parser.add_argument(
            "--todos-publicados",
            action="store_true",
            help="Reindexa todos os T.A. publicados (ex.: para gerar a estratégia v2).",
        )
        parser.add_argument(
            "--sem-pendentes",
            action="store_true",
            help="Não vetoriza nem conta tokens (não consome a API do Gemini): "
            "apenas reindexa os chunks.",
        )
        parser.add_argument(
            "--estrategia",
            choices=["v1", "v2"],
            default=None,
            help="Estratégia de chunking a processar (padrão: settings.RAG_CHUNK_STRATEGY). "
            "Os pendentes vetorizados são apenas os dessa estratégia.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Apenas mostra o que seria processado.",
        )

    def get_ta_ids(self, options):
        ta_ids = set(options["ta_ids"])
        published = TextoArticulado.objects.filter(editing_locked=True)

        if options["tipos"]:
            ta_ids.update(
                Dispositivo.objects.filter(
                    dispositivo_subsequente__isnull=True,
                    tipo_dispositivo__nome__in=options["tipos"],
                    ta__in=published,
                )
                .order_by()
                .values_list("ta_id", flat=True)
                .distinct()
            )

        if options["todos_publicados"]:
            ta_ids.update(published.values_list("id", flat=True))

        if options["sem_embedding"]:
            with_embedding = Embedding.objects.order_by().values(
                "dispositivo_set__ta_id"
            )
            ta_ids.update(
                published.exclude(id__in=with_embedding).values_list("id", flat=True)
            )

        return sorted(ta_ids)

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        estrategia = options["estrategia"] or getattr(
            settings, "RAG_CHUNK_STRATEGY", "v1"
        )
        da_estrategia = Embedding.strategy_filter(estrategia)
        ta_ids = self.get_ta_ids(options)

        self.stdout.write(f"Estratégia: {estrategia}")
        self.stdout.write(
            f"Tipos individualizáveis (v1): {', '.join(CHUNK_TIPOS_INDIVIDUALIZAVEIS)}"
        )
        self.stdout.write(f"T.A. a reindexar: {len(ta_ids)}")

        pendentes = Embedding.objects.filter(da_estrategia, vetor1536__isnull=True)
        sem_tsvector = Embedding.objects.filter(
            da_estrategia, search_vector__isnull=True
        )

        if dry_run:
            self.stdout.write(
                f"Embeddings sem vetor: {pendentes.count()} | "
                f"sem search_vector: {sem_tsvector.count()}"
            )
            return

        for i, ta_id in enumerate(ta_ids, start=1):
            try:
                task_sync_embeddings_textoarticulado_function(
                    [ta_id],
                    strategy=estrategia,
                    vectorize=not options["sem_pendentes"],
                )
            except Exception as e:
                self.stderr.write(f"T.A. {ta_id}: erro ao reindexar: {e}")
            if i % 50 == 0:
                self.stdout.write(f"  {i}/{len(ta_ids)} T.A. processados")

        sem_tsvector.update(search_vector=SearchVector("chunk", config="portuguese"))

        if not options["sem_pendentes"]:
            total = pendentes.count()
            self.stdout.write(f"Vetorizando {total} embeddings pendentes...")
            done = Embedding.generate_embeddings_for_queryset(pendentes)
            self.stdout.write(
                f"Vetorizados: {done} | ainda pendentes: {pendentes.count()}"
            )
