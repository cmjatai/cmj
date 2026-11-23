from django.core.management.base import BaseCommand

from cmj.core.models import AuditLog
from cmj.core.services.s_auditoria import AuditoriaService


class Command(BaseCommand):
    help = (
        "Retira dos registros de auditoria já gravados os campos que a "
        "auditoria não guarda mais (docs/specs/api/acesso.md, API-ACS-042)."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Só conta os registros que seriam alterados.",
        )

    def handle(self, *args, **options):
        registros = AuditLog.objects.all()

        if options["dry_run"]:
            total = AuditoriaService.registros_a_limpar(registros).count()
            self.stdout.write(f"{total} registros seriam alterados.")
            return

        total = AuditoriaService.limpar_registros(registros)
        self.stdout.write(f"{total} registros alterados.")
