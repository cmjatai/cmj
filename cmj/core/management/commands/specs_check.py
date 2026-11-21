import json
import sys
from pathlib import Path

from django.core.management.base import BaseCommand

from cmj.core.services.s_specs_check import checar, filtrar_por_spec

RAIZ = Path(__file__).resolve().parents[4]


class Command(BaseCommand):
    help = (
        "Checa a consistência dos IDs das specs com os testes e as referências "
        "(docs/specs/README.md, seção Checagem). Termina com código 1 se houver achado."
    )
    requires_system_checks = []

    def add_arguments(self, parser):
        parser.add_argument(
            "--spec",
            help="Limita a saída a uma spec, ex.: docs/specs/loa/fases-emenda.md",
        )
        parser.add_argument("--json", action="store_true", help="Saída em JSON")

    def handle(self, *args, **options):
        achados = checar(RAIZ)
        if options["spec"]:
            achados = filtrar_por_spec(RAIZ, achados, options["spec"])

        if options["json"]:
            self.stdout.write(
                json.dumps([a.as_dict() for a in achados], ensure_ascii=False, indent=2)
            )
        else:
            for a in achados:
                self.stdout.write(str(a))
            if achados:
                self.stderr.write(f"{len(achados)} achado(s).")
            else:
                self.stdout.write("Specs consistentes: nenhum achado.")

        if achados:
            sys.exit(1)
