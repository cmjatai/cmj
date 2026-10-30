from django.conf import settings
from django.contrib.postgres.search import SearchVector
from django.core.management import CommandError
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
            "--apenas-pendentes",
            action="store_true",
            help="Reindexa os T.A. publicados que têm embeddings pendentes (sem vetor1536).",
        )
        parser.add_argument(
            "--ta-sem-embedding",
            action="store_true",
            help="Reindexa os T.A. publicados que não têm nenhum embedding.",
        )
        parser.add_argument(
            "--reindexar-todos",
            action="store_true",
            help="Reindexa todos os T.A. publicados (ex.: para gerar a estratégia v2).",
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
        if ta_ids:
            return sorted(ta_ids)

        if not any(
            [
                options["reindexar_todos"],
                options["tipos"],
                options["apenas_pendentes"],
                options["ta_sem_embedding"],
            ]
        ):
            raise CommandError(
                "É necessário especificar pelo menos uma das opções: "
                "--ta-ids, --tipos, --apenas-pendente, --ta-sem-embedding ou --reindexar-todos."
            )

        published = TextoArticulado.objects.filter(editing_locked=True)

        if options["reindexar_todos"]:
            ta_ids.update(published.values_list("id", flat=True))

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

        if options["ta_sem_embedding"]:
            with_embedding = (
                self.qse.order_by()
                .values_list("dispositivo_set__ta_id", flat=True)
                .distinct()
            )
            ta_ids.update(
                published.exclude(id__in=with_embedding).values_list("id", flat=True)
            )

        if options["apenas_pendentes"]:
            ta_com_embedding_pendente = (
                self.qse.filter(vetor1536__isnull=True)
                .order_by()
                .values_list("dispositivo_set__ta_id", flat=True)
                .distinct()
            )
            ta_ids.update(
                published.filter(id__in=ta_com_embedding_pendente).values_list(
                    "id", flat=True
                )
            )

        return sorted(ta_ids)

    def handle(self, *args, **options):
        dry_run = options["dry_run"]

        estrategia = options["estrategia"] or getattr(
            settings, "RAG_CHUNK_STRATEGY", "v1"
        )

        da_estrategia = self.da_estrategia = Embedding.strategy_filter(estrategia)
        self.qse = Embedding.objects.filter(da_estrategia)

        ta_ids = self.get_ta_ids(options)

        if estrategia == "v1":
            self.stdout.write(
                f"Estratégia: {estrategia} | "
                f"Tipos individualizáveis (v1): {', '.join(CHUNK_TIPOS_INDIVIDUALIZAVEIS)}"
            )
        else:
            self.stdout.write(f"Estratégia: {estrategia}")

        # Obter embeddings apenas pendentes para os T.A. selecionados
        pendentes = self.qse.filter(
            dispositivo_set__ta_id__in=ta_ids, vetor1536__isnull=True
        )

        # Obter embeddings sem search_vector para os T.A. selecionados
        sem_tsvector = self.qse.filter(
            dispositivo_set__ta_id__in=ta_ids, search_vector__isnull=True
        )

        # Obter T.A. sem embedding para os T.A. selecionados
        ta_com_pendencia = (
            self.qse.filter(dispositivo_set__ta_id__in=ta_ids, vetor1536__isnull=True)
            .values_list("dispositivo_set__ta_id", flat=True)
            .distinct()
        )

        self.stdout.write(f"T.A. selecionados.: {len(ta_ids)}")

        self.stdout.write(
            f"T.A. com pendência: {ta_com_pendencia.count()} | "
            f"Total embeddings: {self.qse.filter(
                dispositivo_set__ta_id__in=ta_ids).count()} | "
            f"Embeddings pendentes: {pendentes.count()} | "
            f"Embeddings sem search_vector: {sem_tsvector.count()}"
        )
        if dry_run:
            return

        for i, ta_id in enumerate(ta_ids, start=1):
            try:
                task_sync_embeddings_textoarticulado_function(
                    [ta_id],
                    strategy=estrategia,
                    vectorize=not options["apenas_pendentes"],
                    logger=self.stdout
                )
            except Exception as e:
                self.stderr.write(f"T.A. {ta_id}: erro ao reindexar: {e}")
            if i % 50 == 0:
                self.stdout.write(f"  {i}/{len(ta_ids)} T.A. processados")

        sem_tsvector.update(search_vector=SearchVector("chunk", config="portuguese"))

        if options["apenas_pendentes"]:
            total = pendentes.count()
            self.stdout.write(f"Vetorizando {total} embeddings pendentes...")
            done = Embedding.generate_embeddings_for_queryset(pendentes)
            self.stdout.write(
                f"Vetorizados: {done} | ainda pendentes: {pendentes.count()}"
            )
