"""Testes da spec docs/specs/loa/edicao-emenda.md.

Cada teste está ligado a uma regra pelo marker ``spec``. Testes de regras ``[desejado]`` mostram a
divergência atual e devem falhar até a correção.
"""

from decimal import Decimal

import pytest
from django.urls import reverse
from model_mommy import mommy

from cmj.core.models import Bairro
from cmj.loa.models import EmendaLoa, UnidadeOrcamentaria
from cmj.loa.tests.conftest import recarregar
from sapl.materia.models import MateriaLegislativa, TipoMateriaLegislativa

pytestmark = pytest.mark.django_db

P = EmendaLoa.PROPOSTA  # 10
PL = EmendaLoa.PROPOSTA_LIBERADA  # 12
EC = EmendaLoa.EDICAO_CONTABIL  # 15
LC = EmendaLoa.LIBERACAO_CONTABIL  # 17

BASE = {
    "permite_juncao_coletiva",
    "prefixo_indicacao",
    "prefixo_finalidade",
    "finalidade",
    "bairro",
}
ESTRUTURAIS = {"tipo", "fase", "unidade", "entidade"}


# ---------------------------------------------------------------- helpers


@pytest.fixture
def outra_unidade(loa):
    return mommy.make(
        UnidadeOrcamentaria,
        loa=loa,
        codigo="02",
        especificacao="Outra Unidade",
        recebe_emenda_impositiva=True,
    )


@pytest.fixture
def materia(db):
    tipo = mommy.make(TipoMateriaLegislativa, sigla="PLO", descricao="Projeto de Lei")
    return mommy.make(MateriaLegislativa, tipo=tipo, numero=1, ano=2026)


def patch(client, emenda, data, action=""):
    url = f"/api/loa/emendaloa/{emenda.pk}/"
    if action:
        url += f"{action}/"
    return client.patch(url, data, format="json")


def dados_formulario(emenda, **extra):
    """POST completo da tela de edição, com os valores gravados."""
    data = {
        "tipo": emenda.tipo,
        "fase": emenda.fase,
        "finalidade": emenda.finalidade,
        "permite_juncao_coletiva": str(emenda.permite_juncao_coletiva),
        "prefixo_indicacao": emenda.prefixo_indicacao,
        "prefixo_finalidade": emenda.prefixo_finalidade,
        "unidade": emenda.unidade_id,
        "ano_loa": emenda.loa.ano,
        "valor": str(emenda.valor),
    }
    for i, p in enumerate(emenda.loa.parlamentares.order_by("nome_parlamentar")):
        elp = emenda.emendaloaparlamentar_set.filter(parlamentar=p).first()
        data[f"parlamentares__valor_{i}"] = str(elp.valor) if elp else ""
    data.update(extra)
    return data


def post_edicao(client, user, emenda, **extra):
    client.force_login(user)
    return client.post(
        reverse("cmj.loa:emendaloa_update", kwargs={"pk": emenda.pk}),
        dados_formulario(emenda, **extra),
    )


# ------------------------------------------------- service: campos alteráveis


@pytest.mark.spec("LOA-EMD-070")
@pytest.mark.parametrize(
    "fase,esperado",
    [(P, BASE | ESTRUTURAIS), (PL, BASE | ESTRUTURAIS), (LC, BASE)],
)
def test_service_campos_do_autor_por_fase(
    autor, parlamentar, make_emenda, fase, esperado
):
    el = make_emenda(fase=fase, owner=autor, parlamentar=parlamentar)

    assert EmendaLoa.service.campos_alteraveis(autor, el) == esperado


@pytest.mark.spec("LOA-EMD-070")
@pytest.mark.parametrize("fase", [P, LC])
def test_service_autor_altera_valor_da_modificativa(
    autor, parlamentar, make_emenda, fase
):
    el = make_emenda(
        fase=fase, owner=autor, parlamentar=parlamentar, tipo=EmendaLoa.MODIFICATIVA
    )

    assert "valor" in EmendaLoa.service.campos_alteraveis(autor, el)


@pytest.mark.spec("LOA-EMD-070")
def test_service_campos_do_editor_contabil(editor_contabil, make_emenda):
    el = make_emenda(fase=EC)

    assert EmendaLoa.service.campos_alteraveis(editor_contabil, el) == (
        BASE | ESTRUTURAIS
    )


@pytest.mark.spec("LOA-EMD-070")
def test_service_campos_do_operador_e_superusuario(
    operador_loa, superuser, make_emenda
):
    el = make_emenda(fase=LC)
    esperado = BASE | ESTRUTURAIS | {"valor", "materia"}

    assert EmendaLoa.service.campos_alteraveis(operador_loa, el) == esperado
    assert EmendaLoa.service.campos_alteraveis(superuser, el) == esperado


# --------------------------------------------------------------- PATCH da API


@pytest.mark.spec("LOA-EMD-070")
def test_autor_altera_campo_base_pelo_patch(api, autor, parlamentar, make_emenda):
    el = make_emenda(fase=LC, owner=autor, parlamentar=parlamentar)

    r = patch(api(autor), el, {"finalidade": "Nova finalidade"})

    assert r.status_code == 200
    assert recarregar(el).finalidade == "Nova finalidade"


@pytest.mark.spec("LOA-EMD-070")
def test_autor_altera_unidade_ate_a_fase_12(
    api, autor, parlamentar, make_emenda, outra_unidade
):
    el = make_emenda(fase=PL, owner=autor, parlamentar=parlamentar)

    r = patch(api(autor), el, {"unidade": outra_unidade.pk})

    assert r.status_code == 200
    assert recarregar(el).unidade_id == outra_unidade.pk


@pytest.mark.spec("LOA-EMD-070", "LOA-EMD-073")
def test_autor_nao_altera_unidade_na_fase_17(
    api, autor, parlamentar, make_emenda, outra_unidade
):
    el = make_emenda(fase=LC, owner=autor, parlamentar=parlamentar)

    r = patch(api(autor), el, {"unidade": outra_unidade.pk})

    assert r.status_code == 400
    assert "Unidade" in r.content.decode()
    assert recarregar(el).unidade_id != outra_unidade.pk


@pytest.mark.spec("LOA-EMD-070")
def test_editor_contabil_altera_unidade_mas_nao_materia(
    api, editor_contabil, make_emenda, outra_unidade, materia
):
    el = make_emenda(fase=EC)
    client = api(editor_contabil)

    assert patch(client, el, {"unidade": outra_unidade.pk}).status_code == 200
    assert patch(client, el, {"materia": materia.pk}).status_code == 400
    el = recarregar(el)
    assert el.unidade_id == outra_unidade.pk
    assert el.materia_id is None


@pytest.mark.spec("LOA-EMD-070")
def test_operador_da_loa_vincula_materia_pelo_patch(
    api, operador_loa, make_emenda, materia
):
    el = make_emenda(fase=LC)

    r = patch(api(operador_loa), el, {"materia": materia.pk})

    assert r.status_code == 200
    assert recarregar(el).materia_id == materia.pk


@pytest.mark.spec("LOA-EMD-071")
@pytest.mark.parametrize("perfil", ["autor", "editor_contabil", "superuser"])
def test_ninguem_altera_owner_pelo_patch(
    request, api, autor, parlamentar, make_emenda, perfil
):
    user = request.getfixturevalue(perfil)
    el = make_emenda(fase=P, owner=autor, parlamentar=parlamentar)
    outro = mommy.make("core.User", email="outro@test.local")

    r = patch(api(user), el, {"owner": outro.pk})

    assert r.status_code == 400
    assert recarregar(el).owner_id == autor.pk


@pytest.mark.spec("LOA-EMD-071")
def test_superusuario_nao_altera_metadata_pelo_patch(api, superuser, make_emenda):
    el = make_emenda(fase=P)

    r = patch(api(superuser), el, {"metadata": {"style": {"lineHeight": 300}}})

    assert r.status_code == 400
    assert recarregar(el).metadata.get("style", {}).get("lineHeight") != 300


@pytest.mark.spec("LOA-EMD-072")
def test_campo_bloqueado_com_mesmo_valor_nao_e_recusado(
    api, autor, parlamentar, make_emenda
):
    el = make_emenda(fase=LC, owner=autor, parlamentar=parlamentar)

    r = patch(api(autor), el, {"unidade": el.unidade_id})

    assert r.status_code == 200


@pytest.mark.spec("LOA-EMD-073")
def test_chave_que_nao_e_campo_do_model_e_ignorada(
    api, autor, parlamentar, make_emenda
):
    el = make_emenda(fase=LC, owner=autor, parlamentar=parlamentar)

    r = patch(api(autor), el, {"busca_despesa": "saude"})

    assert r.status_code == 200


@pytest.mark.spec("LOA-EMD-073")
def test_patch_recusado_nao_grava_nenhum_campo(
    api, autor, parlamentar, make_emenda, outra_unidade
):
    el = make_emenda(fase=LC, owner=autor, parlamentar=parlamentar)

    r = patch(
        api(autor), el, {"finalidade": "Nova finalidade", "unidade": outra_unidade.pk}
    )

    assert r.status_code == 400
    assert recarregar(el).finalidade == "Finalidade de teste"


# ---------------------------------------------------------- updatevaloremenda


@pytest.mark.spec("LOA-EMD-074")
def test_updatevaloremenda_recusa_autor_na_impositiva(
    api, autor, parlamentar, make_emenda
):
    el = make_emenda(fase=P, owner=autor, parlamentar=parlamentar)

    r = patch(api(autor), el, {"valor": "5000,00"}, action="updatevaloremenda")

    assert r.status_code == 400
    assert recarregar(el).valor == Decimal("1000.00")


@pytest.mark.spec("LOA-EMD-074")
def test_updatevaloremenda_aceita_autor_na_modificativa(
    api, autor, parlamentar, make_emenda
):
    el = make_emenda(
        fase=P, owner=autor, parlamentar=parlamentar, tipo=EmendaLoa.MODIFICATIVA
    )

    r = patch(api(autor), el, {"valor": "5000,00"}, action="updatevaloremenda")

    assert r.status_code == 200
    assert recarregar(el).valor == Decimal("5000.00")


@pytest.mark.spec("LOA-EMD-074")
def test_updatevaloremenda_recusa_editor_contabil(api, editor_contabil, make_emenda):
    el = make_emenda(fase=EC)

    r = patch(
        api(editor_contabil), el, {"valor": "5000,00"}, action="updatevaloremenda"
    )

    assert r.status_code == 400
    assert recarregar(el).valor == Decimal("1000.00")


@pytest.mark.spec("LOA-EMD-074")
def test_updatevaloremenda_aceita_operador_da_loa(api, operador_loa, make_emenda):
    el = make_emenda(fase=EC)

    r = patch(api(operador_loa), el, {"valor": "5000,00"}, action="updatevaloremenda")

    assert r.status_code == 200
    assert recarregar(el).valor == Decimal("5000.00")


# ------------------------------------------------------- POST do formulário


@pytest.mark.spec("LOA-EMD-075")
def test_formulario_do_autor_grava_campo_base(client, autor, parlamentar, make_emenda):
    el = make_emenda(fase=P, owner=autor, parlamentar=parlamentar)

    post_edicao(client, autor, el, finalidade="Nova finalidade")

    assert recarregar(el).finalidade == "Nova finalidade"


@pytest.mark.spec("LOA-EMD-075")
def test_formulario_do_autor_recusa_materia_forjada(
    client, autor, parlamentar, make_emenda, materia
):
    el = make_emenda(fase=P, owner=autor, parlamentar=parlamentar)

    r = post_edicao(
        client,
        autor,
        el,
        tipo_materia=materia.tipo_id,
        numero_materia=materia.numero,
        ano_materia=materia.ano,
    )

    assert r.status_code == 200  # formulário inválido é renderizado de novo
    assert recarregar(el).materia_id is None


@pytest.mark.spec("LOA-EMD-075")
def test_formulario_do_editor_contabil_recusa_valor_forjado(
    client, editor_contabil, make_emenda
):
    el = make_emenda(fase=EC)

    post_edicao(client, editor_contabil, el, valor="5000.00")

    assert recarregar(el).valor == Decimal("1000.00")


@pytest.mark.spec("LOA-EMD-075")
def test_formulario_do_editor_contabil_grava_bairro(
    client, editor_contabil, make_emenda
):
    el = make_emenda(fase=EC)
    bairro = mommy.make(Bairro, nome="Centro", codigo=1)

    post_edicao(client, editor_contabil, el, bairro=bairro.pk)

    assert recarregar(el).bairro_id == bairro.pk


@pytest.mark.spec("LOA-EMD-075")
def test_formulario_do_operador_vincula_materia(
    client, operador_loa, make_emenda, materia
):
    el = make_emenda(fase=EC)

    post_edicao(
        client,
        operador_loa,
        el,
        tipo_materia=materia.tipo_id,
        numero_materia=materia.numero,
        ano_materia=materia.ano,
    )

    assert recarregar(el).materia_id == materia.pk
