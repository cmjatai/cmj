"""Arquivos servidos pelas actions da API (docs/specs/api/arquivos.md).

Os testes exercitam o ``ResponseFileMixin`` direto, com um PDF pequeno numa
pasta temporária, sem model nem rota.
"""

import os
import time
from types import SimpleNamespace
from unittest import mock

import pymupdf
import pytest
from django.contrib.auth.models import AnonymousUser
from django.core.cache import cache
from django.core.exceptions import PermissionDenied
from django.test import RequestFactory
from model_bakery import baker
from rest_framework.exceptions import NotAuthenticated
from rest_framework.test import APIClient

from cmj.core.models import AreaTrabalho
from sapl.api.mixins import ResponseFileMixin
from sapl.api.views import SaplApiViewSetConstrutor
from sapl.materia.models import MateriaLegislativa
from sapl.parlamentares.models import Parlamentar
from sapl.protocoloadm.models import (
    DocumentoAdministrativo,
    TipoDocumentoAdministrativo,
    VinculoDocAdminMateria,
)

MARCA = b"imagem-guardada"


class _Arquivo:
    """O que o mixin lê de um campo de arquivo."""

    def __init__(self, path):
        self.path = self.file = str(path)
        self.name = f"pasta/{os.path.basename(path)}"


class _Itens:
    def __init__(self, item):
        self.item = item

    def filter(self, **kwargs):
        return self

    def first(self):
        return self.item


class _View(ResponseFileMixin):
    action = "arquivo"

    def __init__(self, arquivo, sufixo=None, campos=None):
        self.arquivo = arquivo
        self.format_kwarg = sufixo
        self.campos = campos or {}

    def get_queryset(self):
        return _Itens(SimpleNamespace(arquivo=self.arquivo, **self.campos))


SUPERUSUARIO = SimpleNamespace(is_superuser=True, is_authenticated=True, id=1)
SEM_PRIVILEGIO = SimpleNamespace(is_superuser=False, is_authenticated=True, id=2)


@pytest.fixture
def pdf(tmp_path):
    caminho = tmp_path / "documento.pdf"
    doc = pymupdf.open()
    doc.new_page().insert_text((72, 72), "Texto do documento de teste")
    doc.save(str(caminho))
    doc.close()
    return _Arquivo(caminho)


@pytest.fixture
def pdf_de_duas_paginas(tmp_path):
    caminho = tmp_path / "duas-paginas.pdf"
    doc = pymupdf.open()
    doc.new_page().insert_text((72, 72), "Primeira página")
    doc.new_page().insert_text((72, 72), "Segunda página")
    doc.save(str(caminho))
    doc.close()
    return _Arquivo(caminho)


@pytest.fixture
def cache_em_memoria(settings):
    settings.CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "api-arquivos",
        }
    }
    cache.clear()
    yield
    cache.clear()


def _pedir(arquivo, user=None, cabecalhos=None, sufixo=None, campos=None, **params):
    request = RequestFactory().get("/api/x/1/arquivo/", params, **(cabecalhos or {}))
    request.user = user or AnonymousUser()
    return _View(arquivo, sufixo, campos).response_file(request, pk=1)


def _imagem_guardada(arquivo, dpi=72):
    return f"{arquivo.path}-p001-d{dpi:0>3}.png"


def _guardar_marca(arquivo):
    """Troca a imagem guardada por uma marca, para saber se a resposta veio dela."""
    with open(_imagem_guardada(arquivo), "wb") as f:
        f.write(MARCA)


def _alterar_arquivo(arquivo):
    futuro = time.time() + 60
    os.utime(arquivo.path, (futuro, futuro))


@pytest.mark.django_db
@pytest.mark.spec("API-ARQ-020")
def test_imagem_de_pagina_e_guardada_e_reaproveitada(pdf):
    primeira = _pedir(pdf, page=1)

    assert primeira["Content-Type"] == "image/png"
    assert os.path.exists(_imagem_guardada(pdf))

    _guardar_marca(pdf)
    assert _pedir(pdf, page=1).content == MARCA


@pytest.mark.django_db
@pytest.mark.spec("API-ARQ-020")
def test_imagem_de_pagina_e_refeita_quando_o_arquivo_muda(pdf):
    _pedir(pdf, page=1)
    _guardar_marca(pdf)
    _alterar_arquivo(pdf)

    resposta = _pedir(pdf, page=1)

    assert resposta.content != MARCA
    with open(_imagem_guardada(pdf), "rb") as f:
        assert f.read() == resposta.content


@pytest.mark.django_db
@pytest.mark.spec("API-ARQ-027")
def test_sem_autenticacao_so_a_primeira_pagina_sai_como_imagem(pdf_de_duas_paginas):
    primeira = _pedir(pdf_de_duas_paginas, page=1)
    assert primeira["Content-Type"] == "image/png"

    with pytest.raises(NotAuthenticated):
        _pedir(pdf_de_duas_paginas, page=2)
    assert not os.path.exists(f"{pdf_de_duas_paginas.path}-p002-d072.png")

    segunda = _pedir(pdf_de_duas_paginas, user=SEM_PRIVILEGIO, page=2)
    assert segunda["Content-Type"] == "image/png"
    assert segunda.content != primeira.content


@pytest.mark.django_db
@pytest.mark.spec("API-ARQ-021")
@pytest.mark.parametrize("user", [None, SEM_PRIVILEGIO])
@pytest.mark.parametrize("parametro", [{"nocache": "1"}, {"grade": "10"}])
def test_parametros_de_manutencao_sao_ignorados_para_quem_nao_e_superusuario(
    pdf, user, parametro
):
    _pedir(pdf, page=1)
    _guardar_marca(pdf)

    resposta = _pedir(pdf, user=user, page=1, **parametro)

    assert resposta.content == MARCA
    assert os.path.exists(_imagem_guardada(pdf))


@pytest.mark.django_db
@pytest.mark.spec("API-ARQ-021")
@pytest.mark.parametrize("parametro", [{"nocache": "1"}, {"grade": "10"}])
def test_parametros_de_manutencao_valem_para_superusuario(pdf, parametro):
    _pedir(pdf, page=1)
    _guardar_marca(pdf)

    resposta = _pedir(pdf, user=SUPERUSUARIO, page=1, **parametro)

    assert resposta["Content-Type"] == "image/png"
    assert resposta.content != MARCA


@pytest.mark.django_db
@pytest.mark.spec("API-ARQ-022")
def test_texto_do_pdf_e_extraido_uma_vez_por_versao_do_arquivo(pdf, cache_em_memoria):
    with mock.patch("sapl.api.mixins.pymupdf.open", wraps=pymupdf.open) as abrir:
        primeira = _pedir(pdf, text=1)
        segunda = _pedir(pdf, text=1)
        assert abrir.call_count == 1

        _alterar_arquivo(pdf)
        terceira = _pedir(pdf, text=1)
        assert abrir.call_count == 2

    assert "Texto do documento de teste" in primeira.content.decode()
    assert segunda.content == primeira.content == terceira.content


def _documento(tipo_da_area, numero):
    area = baker.make(AreaTrabalho, tipo=tipo_da_area)
    tipo = baker.make(TipoDocumentoAdministrativo, workspace=area)
    return baker.make(
        DocumentoAdministrativo, tipo=tipo, workspace=area, numero=numero, ano=2026
    )


def _alcancado_pela_action_de_arquivo(documento):
    """O que a action ``texto_integral`` encontra para um anônimo, sem código de
    compartilhamento."""
    request = RequestFactory().get("/")
    request.user = AnonymousUser()
    view = SaplApiViewSetConstrutor.get_viewset_for_model(DocumentoAdministrativo)()
    view.request = request
    view.action = "texto_integral"
    view.kwargs = {"pk": documento.pk}
    view.link_share = ""
    view.permission_required = ()
    return view.get_queryset().filter(pk=documento.pk).exists()


@pytest.mark.skip(
    reason="Chama a API do Telegram: signal de rede social ao salvar a matéria."
)
@pytest.mark.django_db
@pytest.mark.spec("API-ARQ-024")
@pytest.mark.parametrize("vinculo", ["direto", "por_vinculo"])
def test_parecer_da_procuradoria_vinculado_a_materia_e_publico(vinculo):
    parecer = _documento(AreaTrabalho.TIPO_PROCURADORIA, numero=1)
    materia = baker.make(MateriaLegislativa)
    if vinculo == "direto":
        parecer.materia = materia
        parecer.save()
    else:
        baker.make(VinculoDocAdminMateria, documento=parecer, materia=materia)

    assert _alcancado_pela_action_de_arquivo(parecer)


@pytest.mark.skip(
    reason="Chama a API do Telegram: signal de rede social ao salvar a matéria."
)
@pytest.mark.django_db
@pytest.mark.spec("API-ARQ-024")
def test_documento_de_area_restrita_sem_essa_regra_nao_e_publico():
    sem_vinculo = _documento(AreaTrabalho.TIPO_PROCURADORIA, numero=1)
    de_outra_area = _documento(AreaTrabalho.TIPO_INSTITUCIONAL, numero=2)
    de_outra_area.materia = baker.make(MateriaLegislativa)
    de_outra_area.save()

    assert not _alcancado_pela_action_de_arquivo(sem_vinculo)
    assert not _alcancado_pela_action_de_arquivo(de_outra_area)


NAVEGACAO_DIRETA = {
    "HTTP_SEC_FETCH_SITE": "none",
    "HTTP_SEC_FETCH_MODE": "navigate",
    "HTTP_SEC_FETCH_DEST": "document",
}
OUTRAS_ORIGENS = {
    "sem cabeçalhos": {},
    "link em outro site": {**NAVEGACAO_DIRETA, "HTTP_SEC_FETCH_SITE": "cross-site"},
    "link no próprio site": {**NAVEGACAO_DIRETA, "HTTP_SEC_FETCH_SITE": "same-origin"},
    "imagem embutida": {
        "HTTP_SEC_FETCH_SITE": "none",
        "HTTP_SEC_FETCH_MODE": "no-cors",
        "HTTP_SEC_FETCH_DEST": "image",
    },
}


def _texto(arquivo):
    doc = pymupdf.open(arquivo.path)
    texto = "".join(page.get_text() for page in doc)
    doc.close()
    return texto


@pytest.mark.django_db
@pytest.mark.spec("API-ARQ-025")
def test_anonimizacao_por_navegacao_direta_do_superusuario_altera_o_arquivo(pdf):
    assert "documento" in _texto(pdf)

    _pedir(pdf, user=SUPERUSUARIO, cabecalhos=NAVEGACAO_DIRETA, anon="documento")

    assert "documento" not in _texto(pdf)
    assert "Texto" in _texto(pdf)


@pytest.mark.django_db
@pytest.mark.spec("API-ARQ-025")
@pytest.mark.parametrize("origem", OUTRAS_ORIGENS)
def test_anonimizacao_fora_da_navegacao_direta_e_recusada(pdf, origem):
    antes = _texto(pdf)

    with pytest.raises(PermissionDenied):
        _pedir(
            pdf,
            user=SUPERUSUARIO,
            cabecalhos=OUTRAS_ORIGENS[origem],
            anon="documento",
        )

    assert _texto(pdf) == antes


@pytest.mark.django_db
@pytest.mark.spec("API-ARQ-025")
@pytest.mark.parametrize("user", [None, SEM_PRIVILEGIO])
def test_anonimizacao_e_ignorada_para_quem_nao_e_superusuario(pdf, user):
    antes = _texto(pdf)

    resposta = _pedir(pdf, user=user, cabecalhos=NAVEGACAO_DIRETA, anon="documento")

    assert resposta.status_code == 200
    assert _texto(pdf) == antes


MUITOS_ALGARISMOS = "9" * 5000
RECORTE = {"arquivo_cropping": "0,0,200,200"}


@pytest.fixture
def imagem(tmp_path):
    """Só o nome importa: o gerador de miniaturas é trocado por mock."""
    return _Arquivo(tmp_path / "foto.png")


@pytest.fixture
def gerador_de_miniaturas():
    with mock.patch("sapl.api.mixins.get_thumbnailer") as gerador:
        gerador.return_value.get_thumbnail.return_value = SimpleNamespace(
            name="pasta/miniatura.png"
        )
        yield gerador


@pytest.mark.django_db
@pytest.mark.spec("API-ARQ-029")
@pytest.mark.parametrize("page", ["abc", "1.5", "-1", "²", MUITOS_ALGARISMOS])
def test_page_que_nao_e_inteiro_responde_400_sem_gerar_imagem(pdf, page):
    resposta = _pedir(pdf, page=page)

    assert resposta.status_code == 400
    assert "page" in resposta.content.decode()
    assert os.listdir(os.path.dirname(pdf.path)) == ["documento.pdf"]


@pytest.mark.django_db
@pytest.mark.spec("API-ARQ-029")
@pytest.mark.parametrize(
    "grade", ["abc", "1,2,3", "1,2,3,4,5", "10,a,3,4", "-1,2,3,4", "²"]
)
def test_grade_invalida_de_superusuario_responde_400(pdf, grade):
    resposta = _pedir(pdf, user=SUPERUSUARIO, page=1, grade=grade)

    assert resposta.status_code == 400
    assert "grade" in resposta.content.decode()


@pytest.mark.django_db
@pytest.mark.spec("API-ARQ-029")
@pytest.mark.parametrize("grade", ["25", "300,180,590,400", ""])
def test_grade_valida_de_superusuario_desenha_a_pagina(pdf, grade):
    resposta = _pedir(pdf, user=SUPERUSUARIO, page=1, grade=grade)

    assert resposta.status_code == 200
    assert resposta["Content-Type"] == "image/png"


@pytest.mark.django_db
@pytest.mark.spec("API-ARQ-021")
@pytest.mark.parametrize("user", [None, SEM_PRIVILEGIO])
def test_grade_invalida_e_ignorada_para_quem_nao_e_superusuario(pdf, user):
    resposta = _pedir(pdf, user=user, page=1, grade="abc")

    assert resposta.status_code == 200
    assert resposta["Content-Type"] == "image/png"


@pytest.mark.django_db
@pytest.mark.spec("API-ARQ-029")
@pytest.mark.parametrize(
    "sufixo",
    [
        "abc.png",
        "c.png",
        "cx.png",
        "C96.png",
        "0.png",
        "c0.png",
        "100000.png",
        f"{MUITOS_ALGARISMOS}.png",
        ".png",
        "png.a.b",
        "png1.x",
        "pdf.1.2",
        "json.1.2",
    ],
)
def test_sufixo_de_miniatura_malformado_responde_400_sem_gerar_miniatura(
    imagem, gerador_de_miniaturas, sufixo
):
    resposta = _pedir(imagem, sufixo=sufixo, campos=RECORTE)

    assert resposta.status_code == 400
    assert "miniatura" in resposta.content.decode()
    gerador_de_miniaturas.assert_not_called()


@pytest.mark.django_db
@pytest.mark.spec("API-ARQ-029")
def test_miniatura_recortada_de_arquivo_sem_recorte_responde_400(
    imagem, gerador_de_miniaturas
):
    resposta = _pedir(imagem, sufixo="c96.png")

    assert resposta.status_code == 400
    assert "recorte" in resposta.content.decode()
    gerador_de_miniaturas.assert_not_called()

    assert _pedir(imagem, sufixo="96.png").status_code == 200


@pytest.mark.django_db
@pytest.mark.spec("API-ARQ-016")
@pytest.mark.parametrize(
    "sufixo, opcoes",
    [
        ("128.png", {"size": (128, 128), "box": None, "crop": False}),
        ("99999.jpg", {"size": (99999, 99999), "box": None, "crop": False}),
        ("c96.png", {"size": (96, 96), "box": "0,0,200,200", "crop": True}),
    ],
)
def test_sufixo_de_miniatura_valido_pede_a_miniatura(
    imagem, gerador_de_miniaturas, sufixo, opcoes
):
    resposta = _pedir(imagem, sufixo=sufixo, campos=RECORTE)

    assert resposta["X-Accel-Redirect"] == "/mediaredirect/pasta/miniatura.png"
    gerador_de_miniaturas.return_value.get_thumbnail.assert_called_once_with(
        {**opcoes, "detail": True}
    )


@pytest.mark.django_db
@pytest.mark.spec("API-ARQ-016")
def test_sufixo_so_com_a_extensao_entrega_o_arquivo_como_esta(
    imagem, gerador_de_miniaturas
):
    resposta = _pedir(imagem, sufixo="png")

    assert resposta["X-Accel-Redirect"] == "/mediaredirect/pasta/foto.png"
    gerador_de_miniaturas.assert_not_called()


@pytest.mark.django_db
@pytest.mark.spec("API-ARQ-029")
@pytest.mark.parametrize(
    "caminho", ["fotografia.abc.png", "fotografia.png?page=abc", "fotografia/?page=abc"]
)
def test_valor_invalido_chega_como_400_em_json_na_rota_com_sufixo(
    gerador_de_miniaturas, settings, tmp_path, caminho
):
    settings.MEDIA_ROOT = str(tmp_path)
    parlamentar = baker.make(Parlamentar)
    # sem save(): o campo de imagem abriria o arquivo para ler as dimensões
    Parlamentar.objects.filter(pk=parlamentar.pk).update(fotografia="pasta/foto.png")

    resposta = APIClient().get(
        f"/api/parlamentares/parlamentar/{parlamentar.pk}/{caminho}"
    )

    assert resposta.status_code == 400
    assert resposta["Content-Type"] == "application/json"
    assert "detail" in resposta.json()
    gerador_de_miniaturas.assert_not_called()


@pytest.fixture
def parlamentar_com_arquivo(gerador_de_miniaturas, settings, tmp_path):
    """Um parlamentar cujo campo de fotografia aponta para um arquivo que não
    é lido: os pedidos destes testes param antes."""
    settings.MEDIA_ROOT = str(tmp_path)

    def criar(nome_do_arquivo):
        parlamentar = baker.make(Parlamentar)
        # sem save(): o campo de imagem abriria o arquivo para ler as dimensões
        Parlamentar.objects.filter(pk=parlamentar.pk).update(fotografia=nome_do_arquivo)
        return f"/api/parlamentares/parlamentar/{parlamentar.pk}/fotografia"

    return criar


@pytest.mark.django_db
@pytest.mark.spec("API-ARQ-031")
@pytest.mark.parametrize(
    "arquivo, sufixo, status",
    [
        ("pasta/documento.pdf", ".pdf?page=2", 401),
        ("pasta/foto.png", ".png?original=1", 403),
        ("pasta/foto.png", ".abc.png", 400),
    ],
)
def test_erro_em_url_com_sufixo_de_arquivo_chega_com_o_status_dele(
    parlamentar_com_arquivo, arquivo, sufixo, status
):
    resposta = APIClient().get(parlamentar_com_arquivo(arquivo) + sufixo)

    assert resposta.status_code == status
    assert resposta["Content-Type"] == "application/json"
    assert "detail" in resposta.json()


@pytest.mark.django_db
@pytest.mark.spec("API-ARQ-031")
def test_registro_inexistente_em_url_com_sufixo_responde_404_em_json():
    resposta = APIClient().get("/api/parlamentares/parlamentar/0/fotografia.c96.png")

    assert resposta.status_code == 404
    assert resposta["Content-Type"] == "application/json"


@pytest.mark.django_db
@pytest.mark.spec("API-ARQ-032")
@pytest.mark.parametrize(
    "formato, status",
    [("json", 200), ("jsonx", 404), ("js", 404), ("yaml", 404), ("xml", 404)],
)
def test_formato_pedido_casa_por_inteiro_com_o_do_renderer(formato, status):
    rota = "/api/parlamentares/parlamentar/"

    assert APIClient().get(rota, {"format": formato}).status_code == status
    assert APIClient().get(f"{rota[:-1]}.{formato}").status_code == status
