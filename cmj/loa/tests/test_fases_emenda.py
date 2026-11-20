"""Testes da spec docs/specs/loa/fases-emenda.md.

Cada teste está ligado a uma regra pelo marker ``spec``. Testes de regras ``[acordado]`` devem
passar. Testes de regras ``[desejado]`` mostram a divergência atual e devem falhar até a correção.
"""

from decimal import Decimal

import pytest
from django.urls import reverse
from model_mommy import mommy

from cmj.loa.forms.f_emendaloa import EmendaLoaForm
from cmj.loa.models import (
    AgrupamentoEmendaLoa,
    Despesa,
    EmendaLoa,
    EmendaLoaRegistroContabil,
    Loa,
    OficioAjusteLoa,
    RegistroAjusteLoa,
)
from cmj.loa.tests.conftest import ANO, recarregar

pytestmark = pytest.mark.django_db

P = EmendaLoa.PROPOSTA  # 10
PL = EmendaLoa.PROPOSTA_LIBERADA  # 12
EC = EmendaLoa.EDICAO_CONTABIL  # 15
LC = EmendaLoa.LIBERACAO_CONTABIL  # 17
TR = EmendaLoa.EM_TRAMITACAO  # 20
AL = EmendaLoa.APROVACAO_LEGISLATIVA  # 25
AP = EmendaLoa.APROVACAO_LEGAL  # 30


# ---------------------------------------------------------------- helpers


def patch_fase(client, emenda, fase):
    return client.patch(
        f"/api/loa/emendaloa/{emenda.pk}/", {"fase": fase}, format="json"
    )


def fases_do_select(user, emenda=None, loa=None, creating=False):
    loa = loa or emenda.loa
    form = EmendaLoaForm(
        instance=emenda,
        initial={"loa": loa, "user": user, "creating": creating},
    )
    return [valor for valor, _ in form.fields["fase"].choices]


def dados_formulario(emenda, **extra):
    data = {
        "tipo": emenda.tipo,
        "fase": emenda.fase,
        "finalidade": emenda.finalidade,
        "permite_juncao_coletiva": "False",
        "prefixo_indicacao": emenda.prefixo_indicacao,
        "prefixo_finalidade": emenda.prefixo_finalidade,
        "unidade": emenda.unidade_id,
        "ano_loa": emenda.loa.ano,
        "valor": str(emenda.valor),
    }
    data.update(extra)
    return data


def post_edicao(client, user, emenda, **extra):
    client.force_login(user)
    return client.post(
        reverse("cmj.loa:emendaloa_update", kwargs={"pk": emenda.pk}),
        dados_formulario(emenda, **extra),
    )


def get_edicao(client, user, emenda):
    client.force_login(user)
    return client.get(reverse("cmj.loa:emendaloa_update", kwargs={"pk": emenda.pk}))


def incluir_no_agrupamento(client, agrupamento, emenda, **extra):
    data = {"agrupamento": agrupamento.pk, "emendaloa": emenda.pk}
    data.update(extra)
    return client.post("/api/loa/agrupamentoemendaloa/", data, format="json")


# ---------------------------------------------------- inclusão em agrupamento


@pytest.mark.spec("LOA-FASE-058")
def test_inclusao_em_agrupamento_nega_emenda_na_fase_10(
    api, editor_contabil, make_emenda, agrupamento
):
    el = make_emenda(fase=P)

    incluir_no_agrupamento(api(editor_contabil), agrupamento, el, emendaloa__fase=EC)

    assert not AgrupamentoEmendaLoa.objects.filter(emendaloa=el).exists()
    assert recarregar(el).fase == P


@pytest.mark.spec("LOA-FASE-059")
@pytest.mark.parametrize("fase", [PL, EC])
def test_inclusao_em_agrupamento_aceita_fases_12_e_15(
    api, editor_contabil, make_emenda, agrupamento, fase
):
    el = make_emenda(fase=fase)

    incluir_no_agrupamento(api(editor_contabil), agrupamento, el, emendaloa__fase=EC)

    assert AgrupamentoEmendaLoa.objects.filter(
        emendaloa=el, agrupamento=agrupamento
    ).exists()


@pytest.mark.spec("LOA-FASE-059")
@pytest.mark.parametrize("fase", [LC, TR, AP])
def test_inclusao_em_agrupamento_nega_fases_fora_de_12_e_15(
    api, editor_contabil, make_emenda, agrupamento, fase
):
    el = make_emenda(fase=fase)

    incluir_no_agrupamento(api(editor_contabil), agrupamento, el, emendaloa__fase=EC)

    assert not AgrupamentoEmendaLoa.objects.filter(emendaloa=el).exists()
    assert recarregar(el).fase == fase


@pytest.mark.spec("LOA-FASE-059")
def test_inclusao_em_agrupamento_nega_emenda_de_outro_ano(
    api, editor_contabil, make_emenda, agrupamento, unidade
):
    outra_loa = mommy.make(Loa, ano=ANO + 1, publicado=True)
    el = make_emenda(fase=PL, loa=outra_loa)

    incluir_no_agrupamento(api(editor_contabil), agrupamento, el, emendaloa__fase=EC)

    assert not AgrupamentoEmendaLoa.objects.filter(emendaloa=el).exists()


@pytest.mark.spec("LOA-FASE-060")
@pytest.mark.parametrize(
    "extra",
    [{}, {"emendaloa__fase": LC}, {"emendaloa__fase": P}],
    ids=["sem_fase", "cliente_envia_17", "cliente_envia_10"],
)
def test_inclusao_em_agrupamento_define_fase_15_no_servidor(
    api, editor_contabil, make_emenda, agrupamento, extra
):
    el = make_emenda(fase=PL)

    incluir_no_agrupamento(api(editor_contabil), agrupamento, el, **extra)

    assert AgrupamentoEmendaLoa.objects.filter(emendaloa=el).exists()
    assert recarregar(el).fase == EC


# ------------------------------------------------------------ emenda coletiva


@pytest.fixture
def agrupamento_com_coletiva(
    make_emenda, agrupamento, autor, autor_b, parlamentar, parlamentar_b
):
    """Duas emendas que viram coletiva e uma que fica de fora (sem junção, fase 17)."""
    a = make_emenda(
        fase=EC, owner=autor, parlamentar=parlamentar, permite_juncao_coletiva=True
    )
    b = make_emenda(
        fase=EC, owner=autor_b, parlamentar=parlamentar_b, permite_juncao_coletiva=True
    )
    fora = make_emenda(fase=LC, owner=autor, parlamentar=parlamentar)
    for el in (a, b, fora):
        AgrupamentoEmendaLoa.objects.create(agrupamento=agrupamento, emendaloa=el)

    coletivas = agrupamento.gerar_emendas_coletivas()
    return agrupamento, a, b, fora, coletivas


def cancelar_coletivas(client, agrupamento):
    return client.post(
        f"/api/loa/agrupamento/{agrupamento.pk}/cancelar_emendas_coletivas/"
    )


@pytest.mark.spec("LOA-FASE-056")
def test_gerar_coletiva_leva_origem_para_menos_10(agrupamento_com_coletiva):
    _, a, b, _, coletivas = agrupamento_com_coletiva

    assert len(coletivas) == 1
    assert recarregar(a).fase == EmendaLoa.TRANSFORMADA_EM_COLETIVA
    assert recarregar(b).fase == EmendaLoa.TRANSFORMADA_EM_COLETIVA
    assert recarregar(coletivas[0]).fase == EC


@pytest.mark.spec("LOA-FASE-056")
def test_cancelar_coletiva_devolve_origem_para_15(
    api, editor_contabil, agrupamento_com_coletiva
):
    agrupamento, a, b, _, coletivas = agrupamento_com_coletiva

    r = cancelar_coletivas(api(editor_contabil), agrupamento)

    assert r.status_code == 200
    assert recarregar(a).fase == EC
    assert recarregar(b).fase == EC
    assert not EmendaLoa.all_objects.filter(pk=coletivas[0].pk).exists()


@pytest.mark.spec("LOA-FASE-057")
def test_cancelar_coletiva_devolve_para_15_quem_estava_em_17(
    api, editor_contabil, agrupamento_com_coletiva
):
    agrupamento, _, _, fora, _ = agrupamento_com_coletiva
    assert recarregar(fora).fase == LC

    cancelar_coletivas(api(editor_contabil), agrupamento)

    assert recarregar(fora).fase == EC


@pytest.mark.spec("LOA-FASE-064")
def test_coletiva_recebe_owner_da_primeira_emenda(agrupamento_com_coletiva, autor):
    _, a, _, _, coletivas = agrupamento_com_coletiva

    assert recarregar(coletivas[0]).owner_id == a.owner_id == autor.pk


# -------------------------------------------------------- criação pelo autor


@pytest.mark.spec("LOA-FASE-051")
def test_select_de_criacao_do_autor_so_oferece_fase_10(autor, loa):
    assert fases_do_select(autor, loa=loa, creating=True) == [P]


@pytest.mark.spec("LOA-FASE-051")
@pytest.mark.parametrize("fase", [PL, EC, LC, TR])
def test_post_da_api_do_autor_nao_cria_fora_da_fase_10(api, autor, loa, unidade, fase):
    api(autor).post(
        "/api/loa/emendaloa/",
        {
            "loa": loa.pk,
            "unidade": unidade.pk,
            "tipo": EmendaLoa.DIVERSOS,
            "fase": fase,
            "finalidade": "Criada pela API",
        },
        format="json",
    )

    assert (
        not EmendaLoa.all_objects.filter(finalidade="Criada pela API")
        .exclude(fase=P)
        .exists()
    )


# ------------------------------------------------------ transições pelo autor


@pytest.mark.spec("LOA-FASE-052")
@pytest.mark.parametrize("origem,destino", [(P, PL), (PL, P)])
def test_autor_alterna_entre_10_e_12(
    api, autor, parlamentar, make_emenda, origem, destino
):
    el = make_emenda(fase=origem, owner=autor, parlamentar=parlamentar)

    r = patch_fase(api(autor), el, destino)

    assert r.status_code == 200
    assert recarregar(el).fase == destino


@pytest.mark.spec("LOA-FASE-052")
@pytest.mark.parametrize(
    "origem,destino", [(P, EC), (P, LC), (PL, EC), (PL, LC), (LC, P), (LC, PL)]
)
def test_autor_nao_faz_outras_transicoes(
    api, autor, parlamentar, make_emenda, origem, destino
):
    el = make_emenda(fase=origem, owner=autor, parlamentar=parlamentar)

    patch_fase(api(autor), el, destino)

    assert recarregar(el).fase == origem


# ------------------------------------------------- transições do editor contábil


@pytest.mark.spec("LOA-FASE-053")
@pytest.mark.parametrize("origem,destino", [(PL, EC), (PL, LC), (EC, LC), (LC, EC)])
def test_editor_contabil_faz_transicoes_permitidas(
    api, editor_contabil, make_emenda, origem, destino
):
    el = make_emenda(fase=origem)

    r = patch_fase(api(editor_contabil), el, destino)

    assert r.status_code == 200
    assert recarregar(el).fase == destino


@pytest.mark.spec("LOA-FASE-053")
@pytest.mark.parametrize("origem,destino", [(P, EC), (P, LC), (EC, PL), (LC, P)])
def test_editor_contabil_nao_faz_outras_transicoes_pela_api(
    api, editor_contabil, make_emenda, origem, destino
):
    el = make_emenda(fase=origem)

    patch_fase(api(editor_contabil), el, destino)

    assert recarregar(el).fase == origem


@pytest.mark.spec("LOA-FASE-053")
def test_editor_contabil_nao_leva_emenda_da_fase_10_para_17_pelo_formulario(
    client, editor_contabil, make_emenda
):
    el = make_emenda(fase=P)

    post_edicao(client, editor_contabil, el, fase=LC)

    assert recarregar(el).fase == P


@pytest.mark.spec("LOA-FASE-011")
def test_editor_contabil_captura_emenda_12_ao_abrir_edicao(
    client, editor_contabil, make_emenda
):
    el = make_emenda(fase=PL)

    r = get_edicao(client, editor_contabil, el)

    assert r.status_code == 200
    assert recarregar(el).fase == EC


@pytest.mark.spec("LOA-FASE-066")
def test_superusuario_nao_captura_emenda_12_ao_abrir_edicao(
    client, superuser, make_emenda
):
    el = make_emenda(fase=PL)

    r = get_edicao(client, superuser, el)

    assert r.status_code == 200
    assert recarregar(el).fase == PL


# ----------------------------------------------------------------- fase 20+


@pytest.mark.spec("LOA-FASE-054")
def test_select_de_fase_20_so_para_superusuario_e_operador(
    autor, editor_contabil, operador_loa, superuser, parlamentar, make_emenda
):
    el = make_emenda(fase=LC, owner=autor, parlamentar=parlamentar)

    assert TR in fases_do_select(superuser, el)
    assert TR in fases_do_select(operador_loa, el)
    assert TR not in fases_do_select(editor_contabil, el)
    assert TR not in fases_do_select(autor, el)


@pytest.mark.spec("LOA-FASE-054")
def test_editor_contabil_nao_escolhe_fase_20_pela_api(
    api, editor_contabil, make_emenda
):
    el = make_emenda(fase=LC)

    patch_fase(api(editor_contabil), el, TR)

    assert recarregar(el).fase == LC


@pytest.mark.spec("LOA-FASE-054")
def test_autor_nao_escolhe_fase_20_pela_api(api, autor, parlamentar, make_emenda):
    el = make_emenda(fase=LC, owner=autor, parlamentar=parlamentar)

    patch_fase(api(autor), el, TR)

    assert recarregar(el).fase == LC


@pytest.mark.spec("LOA-FASE-055")
@pytest.mark.parametrize("perfil", ["operador_loa", "superuser"])
def test_superusuario_e_operador_movimentam_fase_20_ou_superior(
    request, api, make_emenda, perfil
):
    user = request.getfixturevalue(perfil)
    el = make_emenda(fase=AL)

    r = patch_fase(api(user), el, AP)

    assert r.status_code == 200
    assert recarregar(el).fase == AP


@pytest.mark.spec("LOA-FASE-055")
def test_editor_contabil_nao_movimenta_fase_20_ou_superior(
    api, editor_contabil, make_emenda
):
    el = make_emenda(fase=AL)

    patch_fase(api(editor_contabil), el, AP)

    assert recarregar(el).fase == AL


@pytest.mark.spec("LOA-FASE-055")
def test_autor_nao_movimenta_fase_20_ou_superior(api, autor, parlamentar, make_emenda):
    el = make_emenda(fase=AL, owner=autor, parlamentar=parlamentar)

    patch_fase(api(autor), el, AP)

    assert recarregar(el).fase == AL


# ------------------------------------------------- superusuário e operador


@pytest.mark.spec("LOA-FASE-062")
def test_superusuario_ve_todas_as_fases_no_select(superuser, make_emenda):
    el = make_emenda(fase=AL)

    assert fases_do_select(superuser, el) == [v for v, _ in EmendaLoa.FASE_CHOICE]


@pytest.mark.spec("LOA-FASE-065")
@pytest.mark.parametrize("fase", [P, EC, TR, AP, EmendaLoa.EMENDA_FINALIZADA])
def test_operador_da_loa_abre_edicao_em_qualquer_fase(
    client, operador_loa, autor, make_emenda, fase
):
    el = make_emenda(fase=fase, owner=autor)

    r = get_edicao(client, operador_loa, el)

    assert r.status_code == 200
    assert fases_do_select(operador_loa, el) == [v for v, _ in EmendaLoa.FASE_CHOICE]


@pytest.mark.spec("LOA-FASE-065")
def test_operador_da_loa_nao_ve_emenda_transformada_em_coletiva(
    client, operador_loa, make_emenda
):
    el = make_emenda(fase=EmendaLoa.TRANSFORMADA_EM_COLETIVA)

    r = get_edicao(client, operador_loa, el)

    assert r.status_code == 404


# -------------------------------------------- botões concluir e devolver


@pytest.mark.spec("LOA-FASE-063")
@pytest.mark.parametrize("origem", [EC, LC])
def test_editor_contabil_devolve_para_correcao_nas_fases_15_e_17(
    client, editor_contabil, make_emenda, origem
):
    el = make_emenda(fase=origem)

    post_edicao(client, editor_contabil, el, submit_devolver="1")

    assert recarregar(el).fase == P


@pytest.mark.spec("LOA-FASE-069")
def test_editor_contabil_conclui_edicao_na_fase_15(
    client, editor_contabil, make_emenda
):
    el = make_emenda(fase=EC)

    post_edicao(client, editor_contabil, el, submit_concluir="1")

    assert recarregar(el).fase == LC


@pytest.mark.spec("LOA-FASE-069")
@pytest.mark.parametrize("perfil", ["operador_loa", "superuser"])
@pytest.mark.parametrize("botao", ["submit_concluir", "submit_devolver"])
@pytest.mark.parametrize("origem", [P, PL, TR, AP])
def test_botoes_nao_agem_fora_das_fases_15_e_17(
    request, client, make_emenda, perfil, botao, origem
):
    user = request.getfixturevalue(perfil)
    el = make_emenda(fase=origem)

    post_edicao(client, user, el, **{botao: "1"})

    assert recarregar(el).fase == origem


# ------------------------------------------------------ registros contábeis


@pytest.fixture
def registro_contabil(make_emenda, loa):
    def _make(fase):
        el = make_emenda(fase=fase)
        despesa = mommy.make(Despesa, loa=loa, _fill_optional=False)
        return EmendaLoaRegistroContabil.objects.create(
            emendaloa=el, despesa=despesa, valor=Decimal("100.00")
        )

    return _make


@pytest.mark.spec("LOA-FASE-068")
@pytest.mark.parametrize("fase", [P, PL, EC, LC, TR, AP])
def test_editor_contabil_exclui_registro_contabil_em_qualquer_fase(
    api, editor_contabil, registro_contabil, fase
):
    registro = registro_contabil(fase)

    r = api(editor_contabil).delete(
        f"/api/loa/emendaloaregistrocontabil/{registro.pk}/"
    )

    assert r.status_code == 204
    assert not EmendaLoaRegistroContabil.objects.filter(pk=registro.pk).exists()


@pytest.mark.spec("LOA-FASE-068")
def test_usuario_sem_permissao_nao_exclui_registro_contabil(
    api, autor, registro_contabil
):
    registro = registro_contabil(EC)

    api(autor).delete(f"/api/loa/emendaloaregistrocontabil/{registro.pk}/")

    assert EmendaLoaRegistroContabil.objects.filter(pk=registro.pk).exists()


# --------------------------------------------------------------------- valor


@pytest.mark.spec("LOA-FASE-061")
def test_emenda_com_ajuste_tem_valor_computado_zero(make_emenda):
    el = make_emenda(fase=AP, valor=Decimal("5000.00"))
    assert el.valor_computado == Decimal("5000.00")

    # O hook de busca de RegistroAjusteLoa lê o M2M antes de haver pk; por isso o
    # primeiro save é sem atualizar a busca.
    ajuste = mommy.prepare(
        RegistroAjusteLoa,
        numero=1,
        ano=ANO,
        oficio_ajuste_loa=mommy.make(OficioAjusteLoa, loa=el.loa),
    )
    ajuste.save(auto_update_search=False)
    ajuste.emendaloa.add(el)

    assert recarregar(el).valor_computado == Decimal("0.00")


# ---------------------------------------------------- histórico com usuário

SEM_CAMPO = "EmendaLoaHistoricoFase sem o campo usuario"


def usuario_do_historico(emenda, fase=None):
    """Usuário do registro de histórico mais recente (da fase, se informada)."""
    qs = recarregar(emenda).emendaloahistoricofase_set.order_by("-id")
    if fase is not None:
        qs = qs.filter(fase=fase)
    h = qs.first()
    assert h is not None, "a mudança de fase não gerou histórico"
    return getattr(h, "usuario_id", SEM_CAMPO)


@pytest.mark.spec("LOA-FASE-067")
def test_historico_registra_autor_no_patch_da_api(api, autor, parlamentar, make_emenda):
    el = make_emenda(fase=P, owner=autor, parlamentar=parlamentar)

    r = patch_fase(api(autor), el, PL)

    assert r.status_code == 200
    assert usuario_do_historico(el, PL) == autor.pk


@pytest.mark.spec("LOA-FASE-067")
def test_historico_registra_autor_na_criacao_pela_api(api, autor, loa, unidade):
    loa.publicado = False
    loa.save()

    r = api(autor).post(
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

    assert r.status_code == 201, r.content
    el = EmendaLoa.all_objects.get(finalidade="Criada pela API")
    assert usuario_do_historico(el, P) == autor.pk


@pytest.mark.spec("LOA-FASE-067")
def test_historico_registra_editor_na_captura_ao_abrir_edicao(
    client, editor_contabil, make_emenda
):
    el = make_emenda(fase=PL)

    get_edicao(client, editor_contabil, el)

    assert usuario_do_historico(el, EC) == editor_contabil.pk


@pytest.mark.spec("LOA-FASE-067")
def test_historico_registra_editor_no_botao_concluir(
    client, editor_contabil, make_emenda
):
    el = make_emenda(fase=EC)

    post_edicao(client, editor_contabil, el, submit_concluir="1")

    assert usuario_do_historico(el, LC) == editor_contabil.pk


@pytest.mark.spec("LOA-FASE-067")
def test_historico_registra_editor_na_inclusao_em_agrupamento(
    api, editor_contabil, make_emenda, agrupamento
):
    el = make_emenda(fase=PL)

    incluir_no_agrupamento(api(editor_contabil), agrupamento, el)

    assert usuario_do_historico(el, EC) == editor_contabil.pk


@pytest.mark.spec("LOA-FASE-067")
def test_historico_registra_usuario_ao_gerar_e_cancelar_coletiva(
    api,
    editor_contabil,
    make_emenda,
    agrupamento,
    autor,
    autor_b,
    parlamentar,
    parlamentar_b,
):
    a = make_emenda(
        fase=EC, owner=autor, parlamentar=parlamentar, permite_juncao_coletiva=True
    )
    b = make_emenda(
        fase=EC, owner=autor_b, parlamentar=parlamentar_b, permite_juncao_coletiva=True
    )
    for el in (a, b):
        AgrupamentoEmendaLoa.objects.create(agrupamento=agrupamento, emendaloa=el)
    client = api(editor_contabil)

    r = client.post(f"/api/loa/agrupamento/{agrupamento.pk}/gerar_emenda_coletiva/")
    assert r.status_code == 200, r.content
    coletiva = EmendaLoa.all_objects.get(pk=r.json()["emendas_criadas"][0])

    assert usuario_do_historico(coletiva, EC) == editor_contabil.pk
    for el in (a, b):
        assert (
            usuario_do_historico(el, EmendaLoa.TRANSFORMADA_EM_COLETIVA)
            == editor_contabil.pk
        )

    r = client.post(
        f"/api/loa/agrupamento/{agrupamento.pk}/cancelar_emendas_coletivas/"
    )
    assert r.status_code == 200, r.content

    for el in (a, b):
        assert usuario_do_historico(el) == editor_contabil.pk
        assert recarregar(el).fase == EC


@pytest.mark.spec("LOA-FASE-067")
def test_historico_sem_usuario_quando_save_nao_informa(make_emenda, editor_contabil):
    el = make_emenda(fase=P)

    assert usuario_do_historico(el, P) is None

    # o usuário informado num save() não vaza para o save() seguinte
    el._usuario_fase = editor_contabil
    el.fase = PL
    el.save()
    el.fase = EC
    el.save()

    assert usuario_do_historico(el, PL) == editor_contabil.pk
    assert usuario_do_historico(el, EC) is None
