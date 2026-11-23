"""Testes da spec docs/specs/loa/edicao-emenda.md.

Cada teste está ligado a uma regra pelo marker ``spec``. Testes de regras ``[desejado]`` mostram a
divergência atual e devem falhar até a correção.
"""

import datetime
from decimal import Decimal
from unittest import mock

import pytest
from django.urls import reverse
from model_mommy import mommy

from cmj.core.models import Bairro
from cmj.loa.models import (
    Agrupamento,
    AgrupamentoEmendaLoa,
    AgrupamentoRegistroContabil,
    Despesa,
    EmendaLoa,
    EmendaLoaParlamentar,
    EmendaLoaRegistroContabil,
    UnidadeOrcamentaria,
)
from cmj.loa.tests.conftest import _make_user, recarregar
from sapl.materia.models import (
    MateriaLegislativa,
    Proposicao,
    TipoMateriaLegislativa,
)
from sapl.parlamentares.models import Legislatura, Parlamentar

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


@pytest.mark.spec("LOA-EMD-070", "LOA-EMD-080")
@pytest.mark.parametrize(
    "fase,esperado",
    [(P, BASE | ESTRUTURAIS), (PL, BASE | ESTRUTURAIS), (LC, {"finalidade"})],
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


@pytest.mark.skip(
    reason="Chama a API do Telegram: signal de rede social ao salvar a matéria."
)
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


@pytest.mark.skip(
    reason="Chama a API do Telegram: signal de rede social ao salvar a matéria."
)
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


@pytest.mark.spec("LOA-EMD-083")
def test_patch_sem_campo_do_model_nao_grava_a_emenda(
    api, autor, parlamentar, make_emenda
):
    el = make_emenda(fase=P, owner=autor, parlamentar=parlamentar)

    with mock.patch.object(EmendaLoa, "save") as save:
        r = patch(
            api(autor),
            el,
            {"busca_despesa": "saude", "despesa_codigo": "1", "numero_materia": "3"},
        )

    assert r.status_code == 200
    assert r.data["id"] == el.pk
    save.assert_not_called()


@pytest.mark.spec("LOA-EMD-083")
def test_patch_com_campo_do_model_continua_gravando(
    api, autor, parlamentar, make_emenda
):
    el = make_emenda(fase=P, owner=autor, parlamentar=parlamentar)

    r = patch(api(autor), el, {"finalidade": "Nova", "busca_despesa": "saude"})

    assert r.status_code == 200
    assert recarregar(el).finalidade == "Nova"


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


@pytest.mark.skip(
    reason="Chama a API do Telegram: signal de rede social ao salvar a matéria."
)
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


@pytest.mark.skip(
    reason="Chama a API do Telegram: signal de rede social ao salvar a matéria."
)
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


# ------------------------------------------------- coautores e parlamentares


@pytest.fixture
def emenda_com_coautor(make_emenda, autor, parlamentar, parlamentar_b):
    """Emenda do autor A com o parlamentar B (do autor_b) como coautor."""

    def _make(fase=P, **kwargs):
        el = make_emenda(fase=fase, owner=autor, parlamentar=parlamentar, **kwargs)
        EmendaLoaParlamentar.objects.create(
            emendaloa=el, parlamentar=parlamentar_b, valor=Decimal("500.00")
        )
        return recarregar(el)

    return _make


@pytest.fixture
def parlamentar_fora_da_loa(db):
    return mommy.make(Parlamentar, nome_parlamentar="Fora", nome_completo="Fora")


def valor_parlamentar(client, emenda, parlamentar, valor):
    return patch(
        client,
        emenda,
        {"parlamentar_id": parlamentar.pk, "valor": valor},
        action="updatevalorparlamentar",
    )


def marcar_assinante(client, emenda, parlamentar, checked):
    return patch(
        client,
        emenda,
        {"parlamentar_id": parlamentar.pk, "checked": checked},
        action="update_parlassinantes",
    )


@pytest.mark.spec("LOA-EMD-079")
def test_service_parlamentar_protegido_e_o_do_dono(
    autor, editor_contabil, parlamentar, emenda_com_coautor, make_emenda
):
    el = emenda_com_coautor()
    sem_autor = make_emenda(owner=editor_contabil)

    assert EmendaLoa.service.parlamentar_protegido(el) == parlamentar
    assert EmendaLoa.service.parlamentar_protegido(sem_autor) is None


@pytest.mark.spec("LOA-EMD-076")
def test_coautor_nao_edita_pelo_patch(api, autor_b, emenda_com_coautor):
    el = emenda_com_coautor()

    r = patch(api(autor_b), el, {"finalidade": "Alterada pelo coautor"})

    assert r.status_code == 403
    assert recarregar(el).finalidade == "Finalidade de teste"


@pytest.mark.spec("LOA-EMD-076")
def test_coautor_nao_altera_valores_pelas_actions(
    api, autor_b, parlamentar_b, emenda_com_coautor
):
    el = emenda_com_coautor()
    client = api(autor_b)

    assert valor_parlamentar(client, el, parlamentar_b, "900,00").status_code == 403
    assert marcar_assinante(client, el, parlamentar_b, False).status_code == 403
    assert el.emendaloaparlamentar_set.get(parlamentar=parlamentar_b).valor == Decimal(
        "500.00"
    )


@pytest.mark.spec("LOA-EMD-076")
def test_coautor_ve_detalhe_mas_nao_abre_edicao(client, autor_b, emenda_com_coautor):
    el = emenda_com_coautor()
    client.force_login(autor_b)

    detalhe = client.get(reverse("cmj.loa:emendaloa_detail", kwargs={"pk": el.pk}))
    edicao = client.get(reverse("cmj.loa:emendaloa_update", kwargs={"pk": el.pk}))

    assert detalhe.status_code == 200
    assert edicao.status_code == 403


@pytest.mark.spec("LOA-EMD-076")
def test_usuario_sem_autor_nao_edita_emenda_de_dono_sem_autor(
    client, editor_contabil, make_emenda
):
    # dono sem operador de autor: antes, None == None liberava qualquer usuário logado
    el = make_emenda(fase=P, owner=editor_contabil)
    comum = _make_user("usuario_comum")
    client.force_login(comum)

    r = client.get(reverse("cmj.loa:emendaloa_update", kwargs={"pk": el.pk}))

    assert r.status_code == 403


@pytest.mark.spec("LOA-EMD-077")
def test_autor_do_dono_define_valor_do_coautor(
    api, autor, parlamentar_b, emenda_com_coautor
):
    el = emenda_com_coautor()

    r = valor_parlamentar(api(autor), el, parlamentar_b, "700,00")

    assert r.status_code == 200
    assert el.emendaloaparlamentar_set.get(parlamentar=parlamentar_b).valor == Decimal(
        "700.00"
    )


@pytest.mark.spec("LOA-EMD-077")
def test_operador_da_loa_altera_valor_de_parlamentar(
    api, operador_loa, parlamentar_b, emenda_com_coautor
):
    el = emenda_com_coautor()

    r = valor_parlamentar(api(operador_loa), el, parlamentar_b, "700,00")

    assert r.status_code == 200


@pytest.mark.spec("LOA-EMD-077")
def test_editor_contabil_nao_altera_parlamentares(
    api, editor_contabil, parlamentar_b, emenda_com_coautor
):
    el = emenda_com_coautor(fase=EC)
    client = api(editor_contabil)

    assert valor_parlamentar(client, el, parlamentar_b, "700,00").status_code == 400
    assert marcar_assinante(client, el, parlamentar_b, False).status_code == 400
    assert el.emendaloaparlamentar_set.get(parlamentar=parlamentar_b).valor == Decimal(
        "500.00"
    )


@pytest.mark.spec("LOA-EMD-078")
def test_valor_de_parlamentar_fora_da_loa_e_recusado(
    api, autor, parlamentar_fora_da_loa, emenda_com_coautor
):
    el = emenda_com_coautor()

    r = valor_parlamentar(api(autor), el, parlamentar_fora_da_loa, "100,00")

    assert r.status_code == 400
    assert not el.emendaloaparlamentar_set.filter(
        parlamentar=parlamentar_fora_da_loa
    ).exists()


@pytest.mark.spec("LOA-EMD-078")
def test_assinante_fora_da_loa_e_recusado(
    api, autor, parlamentar, parlamentar_fora_da_loa, make_emenda
):
    el = make_emenda(
        fase=P, owner=autor, parlamentar=parlamentar, tipo=EmendaLoa.MODIFICATIVA
    )

    r = marcar_assinante(api(autor), el, parlamentar_fora_da_loa, True)

    assert r.status_code == 400
    assert not el.parlamentares.filter(pk=parlamentar_fora_da_loa.pk).exists()


@pytest.mark.spec("LOA-EMD-079")
@pytest.mark.parametrize("perfil", ["autor", "operador_loa", "superuser"])
def test_ninguem_zera_o_parlamentar_do_dono(
    request, api, parlamentar, emenda_com_coautor, perfil
):
    el = emenda_com_coautor()
    user = request.getfixturevalue(perfil)

    r = valor_parlamentar(api(user), el, parlamentar, "0,00")

    assert r.status_code == 400
    assert el.emendaloaparlamentar_set.filter(parlamentar=parlamentar).exists()


@pytest.mark.spec("LOA-EMD-079")
@pytest.mark.parametrize("perfil", ["autor", "superuser"])
def test_ninguem_desmarca_o_parlamentar_do_dono(
    request, api, autor, parlamentar, make_emenda, perfil
):
    el = make_emenda(
        fase=P, owner=autor, parlamentar=parlamentar, tipo=EmendaLoa.MODIFICATIVA
    )
    user = request.getfixturevalue(perfil)

    r = marcar_assinante(api(user), el, parlamentar, False)

    assert r.status_code == 400
    assert el.parlamentares.filter(pk=parlamentar.pk).exists()


@pytest.mark.spec("LOA-EMD-079")
def test_formulario_do_superusuario_nao_zera_parlamentar_do_dono(
    client, superuser, parlamentar, parlamentar_b, emenda_com_coautor
):
    el = emenda_com_coautor()
    # parlamentares da LOA em ordem de nome: A (dono) e B (coautor)

    post_edicao(
        client,
        superuser,
        el,
        parlamentares__valor_0="",
        parlamentares__valor_1="500.00",
    )

    assert el.emendaloaparlamentar_set.filter(parlamentar=parlamentar).exists()


@pytest.mark.spec("LOA-EMD-078")
def test_formulario_recusa_assinante_fora_da_loa(
    client, autor, parlamentar, parlamentar_fora_da_loa, make_emenda
):
    el = make_emenda(
        fase=P, owner=autor, parlamentar=parlamentar, tipo=EmendaLoa.MODIFICATIVA
    )

    post_edicao(
        client,
        autor,
        el,
        parl_assinantes=[parlamentar.pk, parlamentar_fora_da_loa.pk],
    )

    assert not el.parlamentares.filter(pk=parlamentar_fora_da_loa.pk).exists()


# ------------------------------------------ autor na fase 17 e registros contábeis


@pytest.fixture
def loa_em_tramitacao(loa):
    """LOA com matéria e sem norma: o save() da emenda chama sync() (LOA-EMD-031).

    O texto de busca da emenda (``artigos``) usa uma view SQL que não existe nos testes.
    """
    Legislatura.objects.create(
        numero=99,
        data_inicio=datetime.date(2025, 1, 1),
        data_fim=datetime.date(2028, 12, 31),
        data_eleicao=datetime.date(2024, 10, 6),
    )
    tipo = mommy.make(TipoMateriaLegislativa, sigla="PLOA", descricao="PLOA")
    loa.materia = mommy.make(
        MateriaLegislativa,
        tipo=tipo,
        numero=9,
        ano=2026,
        data_apresentacao=datetime.date(2026, 9, 1),
    )
    loa.save()
    with mock.patch.object(
        EmendaLoa, "artigos", new_callable=mock.PropertyMock, return_value=[]
    ):
        yield loa


@pytest.fixture
def emenda_liberada(make_emenda, autor, parlamentar, loa):
    """Emenda na fase 17 com dedução de 1000 e inserções de 600 e 400.

    Montada antes de a LOA entrar em tramitação, para o sync() não alterar a montagem.
    """
    el = make_emenda(fase=LC, owner=autor, parlamentar=parlamentar)
    for valor in ("-1000.00", "600.00", "400.00"):
        EmendaLoaRegistroContabil.objects.create(
            emendaloa=el,
            despesa=mommy.make(Despesa, loa=loa, _fill_optional=False),
            valor=Decimal(valor),
        )
    return recarregar(el)


def registros(emenda):
    return sorted(
        recarregar(emenda).registrocontabil_set.values_list("valor", flat=True)
    )


@pytest.mark.spec("LOA-EMD-080")
@pytest.mark.parametrize(
    "campo,valor",
    [
        ("prefixo_finalidade", "Novo prefixo"),
        ("prefixo_indicacao", "Novo prefixo"),
        ("permite_juncao_coletiva", True),
    ],
)
def test_autor_na_fase_17_so_altera_finalidade_e_parlamentares(
    api, autor, parlamentar, make_emenda, campo, valor
):
    el = make_emenda(fase=LC, owner=autor, parlamentar=parlamentar)

    r = patch(api(autor), el, {campo: valor})

    assert r.status_code == 400


@pytest.mark.spec("LOA-EMD-080")
def test_autor_na_fase_17_nao_altera_bairro(api, autor, parlamentar, make_emenda):
    el = make_emenda(fase=LC, owner=autor, parlamentar=parlamentar)
    bairro = mommy.make(Bairro, nome="Centro", codigo=1)

    r = patch(api(autor), el, {"bairro": bairro.pk})

    assert r.status_code == 400
    assert recarregar(el).bairro_id is None


@pytest.mark.spec("LOA-EMD-080", "LOA-EMD-081")
def test_autosave_do_valor_na_fase_17_reajusta_registros(
    api, autor, parlamentar, emenda_liberada, loa_em_tramitacao
):
    el = emenda_liberada

    r = valor_parlamentar(api(autor), el, parlamentar, "1500,00")

    assert r.status_code == 200
    assert recarregar(el).valor == Decimal("1500.00")
    assert registros(el) == [Decimal("-1500.00"), Decimal("600.00"), Decimal("900.00")]


@pytest.mark.spec("LOA-EMD-080", "LOA-EMD-081")
def test_coautor_incluido_na_fase_17_reajusta_registros(
    api, autor, parlamentar_b, emenda_liberada, loa_em_tramitacao
):
    el = emenda_liberada

    r = valor_parlamentar(api(autor), el, parlamentar_b, "500,00")

    assert r.status_code == 200
    assert recarregar(el).valor == Decimal("1500.00")
    assert registros(el) == [Decimal("-1500.00"), Decimal("600.00"), Decimal("900.00")]


@pytest.mark.spec("LOA-EMD-081")
def test_formulario_na_fase_17_reajusta_registros(
    client, autor, parlamentar, emenda_liberada, loa_em_tramitacao
):
    el = emenda_liberada

    post_edicao(client, autor, el, parlamentares__valor_0="1500.00")

    assert recarregar(el).valor == Decimal("1500.00")
    assert registros(el) == [Decimal("-1500.00"), Decimal("600.00"), Decimal("900.00")]


@pytest.mark.spec("LOA-EMD-081")
def test_reajuste_com_proporcao_inexata_mantem_registros_fechados(
    api, autor, parlamentar, emenda_liberada, loa_em_tramitacao
):
    el = emenda_liberada

    valor_parlamentar(api(autor), el, parlamentar, "1333,33")

    valores = registros(el)
    insercoes = sum(v for v in valores if v > 0)
    deducoes = sum(v for v in valores if v < 0)
    assert recarregar(el).valor == Decimal("1333.33")
    assert insercoes == Decimal("1333.33")
    assert deducoes == Decimal("-1333.33")


@pytest.mark.spec("LOA-EMD-081")
def test_valor_na_fase_17_em_agrupamento_segue_percentuais(
    api, autor, parlamentar, make_emenda, loa, loa_em_tramitacao
):
    el = make_emenda(fase=LC, owner=autor, parlamentar=parlamentar)
    ag = mommy.make(Agrupamento, loa=loa, nome="Agrupamento")
    for percentual in ("-100.00", "100.00"):
        AgrupamentoRegistroContabil.objects.create(
            agrupamento=ag,
            despesa=mommy.make(Despesa, loa=loa, _fill_optional=False),
            percentual=Decimal(percentual),
        )
    AgrupamentoEmendaLoa.objects.create(agrupamento=ag, emendaloa=el)

    valor_parlamentar(api(autor), el, parlamentar, "1500,00")

    assert registros(el) == [Decimal("-1500.00"), Decimal("1500.00")]


# ------------------------------------------------------------------- criação


def criar_pela_api(client, loa, unidade):
    return client.post(
        "/api/loa/emendaloa/",
        {
            "loa": loa.pk,
            "unidade": unidade.pk,
            "tipo": EmendaLoa.DIVERSOS,
            "fase": P,
            "finalidade": "Criada pela API",
        },
        format="json",
    )


@pytest.mark.spec("LOA-EMD-082")
@pytest.mark.parametrize("publicado", [True, False], ids=["publicada", "nao_publicada"])
def test_autor_abre_criacao_com_loa_publicada_ou_nao(client, autor, loa, publicado):
    loa.publicado = publicado
    loa.save()
    client.force_login(autor)

    r = client.get(reverse("cmj.loa:emendaloa_create", kwargs={"pk": loa.pk}))

    assert r.status_code == 200


@pytest.mark.spec("LOA-EMD-082")
@pytest.mark.parametrize("publicado", [True, False], ids=["publicada", "nao_publicada"])
def test_autor_cria_pela_api_com_loa_publicada_ou_nao(
    api, autor, loa, unidade, publicado
):
    loa.publicado = publicado
    loa.save()

    r = criar_pela_api(api(autor), loa, unidade)

    assert r.status_code == 201, r.content


@pytest.mark.spec("LOA-EMD-082")
def test_usuario_sem_autor_nem_permissao_nao_cria(api, client, loa, unidade):
    comum = _make_user("usuario_comum")
    client.force_login(comum)

    tela = client.get(reverse("cmj.loa:emendaloa_create", kwargs={"pk": loa.pk}))
    r = criar_pela_api(api(comum), loa, unidade)

    assert tela.status_code == 403
    assert r.status_code == 403
    assert not EmendaLoa.all_objects.filter(finalidade="Criada pela API").exists()


# ------------------------------------------------- estilo gravado pelo /view/


def pdf_vazio(*args, **kwargs):
    import pymupdf

    doc = pymupdf.Document()
    doc.new_page()
    return doc.tobytes()


@pytest.fixture
def get_view():
    def _get(client, emenda, **params):
        with mock.patch("cmj.utils.utils_report.make_pdf", pdf_vazio):
            return client.get(f"/api/loa/emendaloa/{emenda.pk}/view/", params)

    return _get


ESTILO = {"style": {"lineHeight": 150, "espacoAssinatura": 0}}


@pytest.mark.spec("LOA-EMD-085")
def test_view_anonimo_nao_grava_estilo(
    client, get_view, autor, parlamentar, make_emenda
):
    el = make_emenda(fase=P, owner=autor, parlamentar=parlamentar, metadata=ESTILO)

    r = get_view(client, el, lineHeight=300, espacoAssinatura="true")

    assert r.status_code == 200
    assert recarregar(el).metadata == ESTILO


@pytest.mark.spec("LOA-EMD-085")
def test_view_sem_permissao_de_edicao_nao_grava_estilo(
    api, get_view, autor, autor_b, parlamentar, make_emenda
):
    el = make_emenda(fase=P, owner=autor, parlamentar=parlamentar, metadata=ESTILO)

    r = get_view(api(autor_b), el, lineHeight=300)

    assert r.status_code == 200
    assert recarregar(el).metadata == ESTILO


@pytest.mark.spec("LOA-EMD-085")
def test_view_sem_estilo_nao_grava_padrao_para_quem_nao_edita(
    client, get_view, autor, parlamentar, make_emenda
):
    el = make_emenda(fase=P, owner=autor, parlamentar=parlamentar, metadata={})

    assert get_view(client, el).status_code == 200
    assert recarregar(el).metadata == {}


@pytest.mark.spec("LOA-EMD-085")
def test_view_do_autor_grava_estilo(api, get_view, autor, parlamentar, make_emenda):
    el = make_emenda(fase=P, owner=autor, parlamentar=parlamentar, metadata=ESTILO)

    r = get_view(api(autor), el, lineHeight=200, espacoAssinatura="true")

    assert r.status_code == 200
    assert recarregar(el).metadata["style"] == {
        "lineHeight": 200,
        "espacoAssinatura": 1,
    }


@pytest.mark.spec("LOA-EMD-085")
def test_view_do_autor_nao_grava_estilo_na_fase_15(
    api, get_view, autor, parlamentar, make_emenda
):
    el = make_emenda(fase=EC, owner=autor, parlamentar=parlamentar, metadata=ESTILO)

    get_view(api(autor), el, lineHeight=200)

    assert recarregar(el).metadata == ESTILO


@pytest.mark.skip(
    reason="Chama a API do Telegram: signal de rede social ao salvar a matéria."
)
@pytest.mark.spec("LOA-EMD-085")
def test_view_do_operador_da_loa_grava_estilo_com_materia(
    api, get_view, operador_loa, make_emenda, materia
):
    el = make_emenda(fase=LC, materia=materia, metadata=ESTILO)

    get_view(api(operador_loa), el, lineHeight=200)

    assert recarregar(el).metadata["style"]["lineHeight"] == 200


# ------------------------------------- registro pelo detalhe removido (LOA-EMD-086)


@pytest.mark.spec("LOA-EMD-086")
def test_detalhe_com_registrar_nao_registra_proposicao(client, autor, make_emenda):
    el = make_emenda(fase=EmendaLoa.LIBERACAO_CONTABIL, owner=autor)
    client.force_login(autor)
    url = reverse("cmj.loa:emendaloa_detail", kwargs={"pk": el.pk})

    with mock.patch("cmj.utils.utils_report.make_pdf") as gerar:
        response = client.get(f"{url}?registrar")

    assert response.status_code == 200
    gerar.assert_not_called()
    assert Proposicao.objects.count() == 0
    assert recarregar(el).proposicao is None
