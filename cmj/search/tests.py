import pytest
from django import forms
from django.utils.safestring import SafeString

from cmj.search.views import InfoFilterMixin
from sapl.base.models import Autor

pytestmark = [pytest.mark.django_db, pytest.mark.spec("LOA-PCT-063")]

TEXTO = '<b class="x">a & b</b>'
TEXTO_EXIBIDO = "&lt;b class=&quot;x&quot;&gt;a &amp; b&lt;/b&gt;"


class _ListaField(forms.Field):
    def clean(self, value):
        return list(value or [])


class _Form(forms.Form):
    search = forms.CharField(required=False, label="Busca <livre>")
    nome__in = _ListaField(required=False, label="Nome")
    tipo = forms.ChoiceField(required=False, label="Tipo", choices=[("1", "Um & Dois")])
    ativo = forms.BooleanField(required=False, label="Ativo")
    ordenacao = forms.CharField(required=False)


def _infofilter(model=None, **data):
    return InfoFilterMixin().infofilter(data, form=_Form(data), model=model)


def test_infofilter_sem_filtros_e_vazio():
    assert _infofilter() == ""
    assert _infofilter(ordenacao="x") == ""


def test_infofilter_marca_titulo_e_rotulo_em_negrito():
    html = _infofilter(ativo=True)

    assert isinstance(html, SafeString)
    assert html == (
        "<strong>FILTROS APLICADOS</strong><br><strong>Ativo:</strong> Sim<br>"
    )


def test_infofilter_exibe_texto_livre_como_texto():
    html = _infofilter(search=TEXTO)

    assert f"<strong>Busca &lt;livre&gt;:</strong> {TEXTO_EXIBIDO}" in html
    assert TEXTO not in html


def test_infofilter_exibe_itens_de_lista_como_texto():
    html = _infofilter(model=Autor, nome__in=["10", TEXTO])

    assert f"<strong>Nome:</strong> 10, {TEXTO_EXIBIDO}" in html
    assert TEXTO not in html


def test_infofilter_exibe_rotulo_da_escolha_como_texto():
    html = _infofilter(tipo="1")

    assert "<strong>Tipo:</strong> Um &amp; Dois" in html
