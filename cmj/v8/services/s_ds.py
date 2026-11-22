"""Design system do v8: as seções da vitrine, os temas e os dados de amostra.

Tudo aqui é fixo e fictício (docs/specs/v8/ds.md), escrito neste módulo: a
vitrine só mostra como o padrão visual está.
"""

from dataclasses import dataclass

from django.urls import reverse

from cmj.v8.services import s_global

PASTA_SECOES = "v8/partials/ds/"


@dataclass(frozen=True)
class Secao:
    """Seção da vitrine: âncora ``ds-<id>``, rótulo do índice e parcial."""

    id: str
    rotulo: str

    @property
    def ancora(self):
        return f"ds-{self.id}"

    @property
    def parcial(self):
        return f"{PASTA_SECOES}{self.id}.html"


# Ordem do índice e da página. A parcial de cada seção sai só deste registro.
SECOES = (Secao("cores", "Cores"),)


def temas(em_vigor):
    """Os temas do registro, na ordem dele, com as URLs e a marca do que vale."""
    return [
        {
            "nome": nome,
            "rotulo": rotulo,
            "em_vigor": nome == em_vigor,
            "url_previa": reverse(f"cmj.v8:ds_tema_{nome}"),
            "url_usar": reverse(f"cmj.v8:ds_tema_usar_{nome}"),
        }
        for nome, rotulo in s_global.TEMAS.items()
    ]


def tema(nome, em_vigor):
    """Um tema do registro, como em ``temas``. Nome fora do registro é erro."""
    return next(item for item in temas(em_vigor) if item["nome"] == nome)
