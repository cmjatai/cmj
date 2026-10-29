import pytest

from sapl.compilacao.models import (
    CHUNK_TIPOS_INDIVIDUALIZAVEIS,
    CHUNK_TNU_MIN_PALAVRAS,
    texto_plano_html,
)

pytestmark = pytest.mark.django_db


def test_texto_plano_html_remove_tags_e_entidades():
    html = (
        '<div style="text-align: right;">C&acirc;mara&nbsp;Municipal</div>\n'
        "<div>&nbsp;</div><strong>Prefeito</strong>"
    )

    assert texto_plano_html(html) == "Câmara Municipal Prefeito"
    assert texto_plano_html("") == ""
    assert texto_plano_html(None) == ""


def test_tipos_individualizaveis_cobrem_anexo_e_texto_nao_estruturado():
    assert "Anexo" in CHUNK_TIPOS_INDIVIDUALIZAVEIS
    assert "Texto Não Estruturado" in CHUNK_TIPOS_INDIVIDUALIZAVEIS
    assert CHUNK_TNU_MIN_PALAVRAS > 0
