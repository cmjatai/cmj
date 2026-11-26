"""Telas da LOA (docs/specs/loa/crud-loa.md): quem consulta o detalhe
(`/loa/<pk>`) e quais emendas entram nos cálculos."""

import datetime
from decimal import Decimal
from unittest import mock

import pytest
from django.db.models import ProtectedError
from model_bakery import baker as mommy

from cmj.loa.forms.f_ajusteloa import RegistroAjusteLoaForm
from cmj.loa.forms.f_loa import LoaForm
from cmj.loa.models import (
    EmendaLoa,
    EmendaLoaHistoricoFase,
    EmendaLoaParlamentar,
    Entidade,
    Loa,
    OficioAjusteLoa,
    RegistroAjusteLoa,
    RegistroAjusteLoaParlamentar,
    UnidadeOrcamentaria,
)
from sapl.materia.models import MateriaLegislativa
from sapl.norma.models import NormaJuridica
from sapl.parlamentares.models import Legislatura, Mandato, Parlamentar

pytestmark = [pytest.mark.django_db]


@pytest.fixture(autouse=True)
def legislatura_atual(db):
    return Legislatura.objects.create(
        numero=99,
        data_inicio=datetime.date(2025, 1, 1),
        data_fim=datetime.date(2028, 12, 31),
        data_eleicao=datetime.date(2024, 10, 6),
    )


def _loa(ano, publicado, com_norma, **valores):
    materia = mommy.make(
        MateriaLegislativa,
        numero=ano,
        ano=ano - 1,
        data_apresentacao=datetime.date(ano - 1, 9, 1),
    )
    if com_norma:
        mommy.make(NormaJuridica, materia=materia)
    loa = mommy.make(Loa, ano=ano, publicado=publicado, materia=materia, **valores)
    loa.parlamentares.add(
        mommy.make(Parlamentar, nome_parlamentar=f"Parlamentar {ano}", ativo=True)
    )
    return loa


def _emenda(loa, parlamentar, fase, valor="1000.00"):
    """Emenda de áreas diversas com um parlamentar só."""
    emenda = EmendaLoa(
        loa=loa,
        fase=fase,
        tipo=EmendaLoa.DIVERSOS,
        valor=Decimal(valor),
        finalidade="Finalidade de teste",
    )
    emenda.save()
    EmendaLoaParlamentar.objects.create(
        emendaloa=emenda, parlamentar=parlamentar, valor=Decimal(valor)
    )
    return emenda


def _detalhe(client, loa):
    return client.get(f"/loa/{loa.pk}")


@pytest.mark.spec("LOA-CRUD-033")
def test_loa_publicada_abre_o_detalhe_com_os_resumos(client):
    loa = _loa(2081, publicado=True, com_norma=True)

    resposta = _detalhe(client, loa)

    assert resposta.status_code == 200
    pagina = resposta.content.decode()
    assert "Resumo Geral das Emendas Impositivas Parlamentares" in pagina
    assert f"Parlamentar {loa.ano}" in pagina


@pytest.mark.spec("LOA-CRUD-033")
@pytest.mark.parametrize("perfil", ["anonimo", "comum"])
def test_loa_nao_publicada_responde_404_no_detalhe(client, django_user_model, perfil):
    loa = _loa(2082, publicado=False, com_norma=False)
    if perfil == "comum":
        client.force_login(
            django_user_model.objects.create_user(
                email="comum@test.local", password="testpass123!"
            )
        )

    assert _detalhe(client, loa).status_code == 404


@pytest.mark.spec("LOA-CRUD-033")
def test_conta_comum_abre_o_detalhe_da_loa_publicada(client, django_user_model):
    loa = _loa(2083, publicado=True, com_norma=False)
    client.force_login(
        django_user_model.objects.create_user(
            email="comum@test.local", password="testpass123!"
        )
    )

    assert _detalhe(client, loa).status_code == 200


@pytest.mark.spec("LOA-CRUD-033")
def test_editor_da_contabilidade_abre_o_detalhe_da_loa_nao_publicada(
    client, editor_contabil
):
    loa = _loa(2084, publicado=False, com_norma=True)
    client.force_login(editor_contabil)

    assert _detalhe(client, loa).status_code == 200


@pytest.mark.spec("LOA-CRUD-033")
def test_operador_de_autor_segue_a_visibilidade_da_loa_no_detalhe(client, autor):
    # a LOA não publicada cuja matéria ainda não virou norma ele consulta; a
    # que já virou norma responde como inexistente
    sem_norma = _loa(2085, publicado=False, com_norma=False)
    virou_norma = _loa(2086, publicado=False, com_norma=True)
    client.force_login(autor)

    assert _detalhe(client, sem_norma).status_code == 200
    assert _detalhe(client, virou_norma).status_code == 404


@pytest.mark.spec("LOA-CRUD-033")
def test_loa_inexistente_responde_404_no_detalhe(client):
    assert client.get("/loa/999999").status_code == 404


@pytest.mark.spec("LOA-CRUD-036")
@pytest.mark.parametrize(
    "perfil, com_norma, ve_o_botao",
    [
        ("operador_loa", False, True),
        ("autor", False, True),
        ("comum", False, False),
        ("anonimo", False, False),
        ("operador_loa", True, False),
    ],
)
def test_botao_de_adicionar_emendas_segue_a_regra_de_criacao(
    client, request, django_user_model, perfil, com_norma, ve_o_botao
):
    loa = _loa(2087, publicado=True, com_norma=com_norma)
    if perfil == "comum":
        client.force_login(
            django_user_model.objects.create_user(
                email="comum@test.local", password="testpass123!"
            )
        )
    elif perfil != "anonimo":
        client.force_login(request.getfixturevalue(perfil))

    resposta = _detalhe(client, loa)

    assert resposta.status_code == 200
    assert ("Adicionar Emendas Impositivas" in resposta.content.decode()) is ve_o_botao


def _coluna_rcl_da_lista(loa):
    from django.test import RequestFactory
    from django.urls import resolve

    view = resolve("/loa").func.view_class()
    view.request = RequestFactory().get("/loa")
    return view.hook_receita_corrente_liquida(loa, "1.000,00", "")[0]


@pytest.mark.spec("LOA-CRUD-014")
def test_coluna_da_rcl_na_lista_fecha_as_tags_e_informa_o_andamento():
    from django.utils import timezone

    ano_atual = timezone.now().year
    futura = _loa(ano_atual + 60, publicado=True, com_norma=False)
    corrente = _loa(ano_atual, publicado=True, com_norma=True)
    passada = _loa(ano_atual - 1, publicado=True, com_norma=True)

    assert "Processo Legislativo em andamento" in _coluna_rcl_da_lista(futura)
    for loa in (futura, corrente, passada):
        coluna = _coluna_rcl_da_lista(loa)
        assert coluna.count("<small") == coluna.count("</small>")


@pytest.mark.spec("LOA-CRUD-057")
def test_emendas_sem_unidade_formam_um_grupo_nomeado_e_sem_link(client):
    loa = _loa(2088, publicado=True, com_norma=False)
    _emenda(loa, loa.parlamentares.get(), EmendaLoa.PROPOSTA)

    pagina = _detalhe(client, loa).content.decode()

    assert "Sem unidade orçamentária" in pagina
    assert "unidade=None" not in pagina


@pytest.mark.spec("LOA-CRUD-065")
def test_resumo_por_parlamentar_soma_so_as_emendas_de_fase_positiva(client):
    loa = _loa(
        2087,
        publicado=True,
        com_norma=False,
        disp_total=Decimal("20000.00"),
        disp_saude=Decimal("10000.00"),
        disp_diversos=Decimal("10000.00"),
    )
    parlamentar = loa.parlamentares.get()
    _emenda(loa, parlamentar, EmendaLoa.TRANSFORMADA_EM_COLETIVA)
    _emenda(loa, parlamentar, EmendaLoa.EDICAO_CONTABIL)

    pagina = _detalhe(client, loa).content.decode()

    # 10.000,00 disponíveis e 1.000,00 destinados: a emenda de origem não soma
    assert "9.000,00" in pagina
    assert "8.000,00" not in pagina
    assert "2.000,00" not in pagina


@pytest.mark.spec("LOA-CRUD-065")
def test_loa_atual_ignora_loa_que_so_tem_emenda_transformada_em_coletiva(client):
    so_de_origem = _loa(2090, publicado=True, com_norma=False)
    com_emenda = _loa(2089, publicado=True, com_norma=False)
    _emenda(
        so_de_origem,
        so_de_origem.parlamentares.get(),
        EmendaLoa.TRANSFORMADA_EM_COLETIVA,
    )
    _emenda(com_emenda, com_emenda.parlamentares.get(), EmendaLoa.PROPOSTA)

    resposta = client.get("/loa/atual")

    assert resposta.status_code == 302
    assert resposta["Location"] == f"/loa/{com_emenda.pk}/prestacaoconta"


def _loa_com_dez_mil_por_tipo(ano):
    loa = _loa(
        ano,
        publicado=True,
        com_norma=False,
        disp_total=Decimal("20000.00"),
        disp_saude=Decimal("10000.00"),
        disp_diversos=Decimal("10000.00"),
    )
    return loa, loa.parlamentares.get()


@pytest.mark.spec("LOA-CRUD-043")
def test_emenda_em_impedimento_tecnico_sai_do_ja_destinado(client):
    loa, parlamentar = _loa_com_dez_mil_por_tipo(2071)
    _emenda(loa, parlamentar, EmendaLoa.PROPOSTA, valor="3000.00")
    _emenda(loa, parlamentar, EmendaLoa.IMPEDIMENTO_TECNICO)

    pagina = _detalhe(client, loa).content.decode()

    # 3.000,00 destinados, 1.000,00 impedidos e 7.000,00 sem destinação
    assert "7.000,00" in pagina
    assert "6.000,00" not in pagina


@pytest.mark.spec("LOA-CRUD-043")
def test_emenda_que_ja_saiu_do_impedimento_sem_ajuste_conta_como_destinada(client):
    loa, parlamentar = _loa_com_dez_mil_por_tipo(2072)
    emenda = _emenda(loa, parlamentar, EmendaLoa.EMENDA_FINALIZADA)
    EmendaLoaHistoricoFase.objects.create(
        emendaloa=emenda, fase=EmendaLoa.IMPEDIMENTO_TECNICO
    )

    pagina = _detalhe(client, loa).content.decode()

    # 1.000,00 destinados e 9.000,00 sem destinação
    assert "9.000,00" in pagina


@pytest.mark.spec("LOA-CRUD-043")
def test_emenda_com_ajuste_da_lugar_ao_valor_do_ajuste(client):
    loa, parlamentar = _loa_com_dez_mil_por_tipo(2073)
    emenda = _emenda(loa, parlamentar, EmendaLoa.EMENDA_EM_EXECUCAO)
    # o hook de busca do ajuste lê o M2M antes de haver pk
    registro = mommy.prepare(
        RegistroAjusteLoa,
        oficio_ajuste_loa=mommy.make(OficioAjusteLoa, loa=loa),
        numero=1,
        ano=loa.ano,
        tipo=EmendaLoa.DIVERSOS,
        fase=RegistroAjusteLoa.AJUSTE_EM_EXECUCAO,
        unidade=None,
        entidade=None,
        descricao="Ajuste 1",
    )
    registro.save(auto_update_search=False)
    registro.emendaloa.add(emenda)
    RegistroAjusteLoaParlamentar.objects.create(
        registro=registro, parlamentar=parlamentar, valor=Decimal("1000.00")
    )

    pagina = _detalhe(client, loa).content.decode()

    # o ajuste de 1.000,00 entra no lugar da emenda: 9.000,00 sem destinação
    assert "9.000,00" in pagina
    assert "8.000,00" not in pagina


@pytest.mark.spec("LOA-CRUD-065")
def test_lista_de_empenhos_da_loa_ignora_a_emenda_transformada_em_coletiva():
    from django.contrib.auth.models import AnonymousUser
    from django.test import RequestFactory
    from django.urls import resolve

    from cmj.loa.models import Empenho, EmpenhoEmendaAjuste, Orgao

    loa = _loa(2089, publicado=True, com_norma=True)
    parlamentar = loa.parlamentares.get()
    orgao = mommy.make(Orgao, loa=loa, codigo="01")
    empenhos = {}
    for fase in (EmendaLoa.EMENDA_EM_EXECUCAO, EmendaLoa.TRANSFORMADA_EM_COLETIVA):
        empenhos[fase] = mommy.make(Empenho, orgao=orgao, _fill_optional=False)
        EmpenhoEmendaAjuste.objects.create(
            emendaloa=_emenda(loa, parlamentar, fase), empenho=empenhos[fase]
        )

    # a consulta da lista, sem renderizar as linhas, que leem a matéria da emenda
    view = resolve(f"/loa/{loa.pk}/empenho").func.view_class()
    view.request = RequestFactory().get(f"/loa/{loa.pk}/empenho")
    view.request.user = AnonymousUser()
    view.loa = loa

    assert list(view.get_queryset()) == [empenhos[EmendaLoa.EMENDA_EM_EXECUCAO]]


def _registro_de_ajuste(loa, emendas, parlamentar, valor):
    # o hook de busca do ajuste lê o M2M antes de haver pk
    registro = mommy.prepare(
        RegistroAjusteLoa,
        oficio_ajuste_loa=mommy.make(OficioAjusteLoa, loa=loa),
        numero=1,
        ano=loa.ano,
        tipo=EmendaLoa.DIVERSOS,
        fase=RegistroAjusteLoa.AJUSTE_EM_EXECUCAO,
        unidade=None,
        entidade=None,
        descricao="Ajuste",
    )
    registro.save(auto_update_search=False)
    registro.emendaloa.add(*emendas)
    RegistroAjusteLoaParlamentar.objects.create(
        registro=registro, parlamentar=parlamentar, valor=Decimal(valor)
    )
    return registro


@pytest.mark.spec("LOA-CRUD-044")
def test_ajuste_ligado_a_varias_emendas_entra_uma_vez_so():
    loa, parlamentar = _loa_com_dez_mil_por_tipo(2075)
    emendas = [
        _emenda(loa, parlamentar, EmendaLoa.EMENDA_EM_EXECUCAO) for _ in range(2)
    ]
    _registro_de_ajuste(loa, emendas, parlamentar, "1500.00")

    linha = Loa.service.resumo_parlamentares(loa)["linhas"][0][EmendaLoa.DIVERSOS]

    # D = I = 2.000,00 (as duas têm ajuste) e Ac = 1.500,00, não 3.000,00
    assert linha["ja_destinado"] == Decimal("1500.00")
    assert linha["impedimento_tecnico"] == Decimal("500.00")
    assert linha["sem_destinacao"] == Decimal("8500.00")


def _consultas_dos_resumos(loa):
    from django.db import connection
    from django.test.utils import CaptureQueriesContext

    loa = Loa.objects.get(pk=loa.pk)
    with CaptureQueriesContext(connection) as consultas:
        Loa.service.resumo_parlamentares(loa)
        Loa.service.resumo_unidades(loa)
        Loa.service.resumo_entidades(loa)
    return len(consultas)


@pytest.mark.spec("LOA-CRUD-071")
def test_consultas_dos_resumos_nao_crescem_com_os_parlamentares():
    pequena, parlamentar = _loa_com_dez_mil_por_tipo(2076)
    _registro_de_ajuste(
        pequena,
        [_emenda(pequena, parlamentar, EmendaLoa.EMENDA_EM_EXECUCAO)],
        parlamentar,
        "500.00",
    )

    grande, _primeiro = _loa_com_dez_mil_por_tipo(2077)
    for n in range(4):
        p = mommy.make(Parlamentar, nome_parlamentar=f"Outro {n}", ativo=True)
        grande.parlamentares.add(p)
        for fase in (EmendaLoa.PROPOSTA, EmendaLoa.EMENDA_EM_EXECUCAO):
            emenda = _emenda(grande, p, fase)
        _registro_de_ajuste(grande, [emenda], p, "500.00")

    assert _consultas_dos_resumos(grande) == _consultas_dos_resumos(pequena)


def _oficio_de_ajuste(ano):
    loa, parlamentar = _loa_com_dez_mil_por_tipo(ano)
    oficio = mommy.make(OficioAjusteLoa, loa=loa)
    oficio.parlamentares.add(parlamentar)
    return oficio, parlamentar


@pytest.mark.spec("LOA-CRUD-066")
def test_formulario_de_ajuste_so_aceita_valor_a_partir_de_zero():
    oficio, _parlamentar = _oficio_de_ajuste(2074)

    def erros(valor):
        form = RegistroAjusteLoaForm(
            data={"parlamentares__valor_0": valor},
            initial={"oficioajusteloa": oficio},
        )
        form.is_valid()
        return form.errors.get("parlamentares__valor")

    assert erros("-1,00")
    assert not erros("0,00")
    assert not erros("1.000,00")


@pytest.mark.spec("LOA-CRUD-066")
def test_api_do_ajuste_so_aceita_valor_a_partir_de_zero(api, superuser):
    oficio, parlamentar = _oficio_de_ajuste(2075)
    # o hook de busca do ajuste lê o M2M antes de haver pk
    registro = mommy.prepare(
        RegistroAjusteLoa,
        oficio_ajuste_loa=oficio,
        numero=1,
        ano=oficio.loa.ano,
        tipo=EmendaLoa.DIVERSOS,
        unidade=None,
        entidade=None,
        descricao="Ajuste 1",
    )
    registro.save(auto_update_search=False)
    cliente = api(superuser)

    def grava(valor):
        return cliente.post(
            "/api/loa/registroajusteloaparlamentar/",
            {"registro": registro.pk, "parlamentar": parlamentar.pk, "valor": valor},
            format="json",
        )

    negativo = grava("-1.00")
    assert negativo.status_code == 400
    assert "valor" in negativo.json()
    assert grava("1000.00").status_code == 201


def _parlamentar(nome, legislatura=None, **cadastro):
    """Parlamentar com mandato na legislatura, quando ela é informada."""
    parlamentar = mommy.make(Parlamentar, nome_parlamentar=nome, **cadastro)
    if legislatura:
        mommy.make(
            Mandato, parlamentar=parlamentar, legislatura=legislatura, titular=False
        )
    return parlamentar


@pytest.mark.spec("LOA-CRUD-067")
def test_ativo_no_detalhe_e_quem_tem_mandato_na_legislatura_do_ano_da_loa(
    client, legislatura_atual
):
    anterior = Legislatura.objects.create(
        numero=98,
        data_inicio=datetime.date(2021, 1, 1),
        data_fim=datetime.date(2024, 12, 31),
        data_eleicao=datetime.date(2020, 10, 4),
    )
    loa = mommy.make(Loa, ano=2026, publicado=True)
    # suplente com mandato na legislatura da LOA, inativo no cadastro
    com_mandato = _parlamentar("Zulmira", legislatura_atual, ativo=False)
    # ativo no cadastro, com mandato só na legislatura anterior
    sem_mandato = _parlamentar("Abel", anterior, ativo=True)
    loa.parlamentares.add(com_mandato, sem_mandato)

    assert Loa.service.parlamentares_com_mandato(loa) == {com_mandato.pk}

    pagina = _detalhe(client, loa).content.decode()

    # quem tem mandato vem primeiro e leva a etiqueta de ativo
    assert pagina.index("Zulmira") < pagina.index("Abel")
    etiqueta_de_zulmira = pagina[pagina.index("Zulmira") : pagina.index("Abel")]
    assert "Ativo" in etiqueta_de_zulmira
    assert "Inativo" in pagina[pagina.index("Abel") :]


@pytest.mark.spec("LOA-CRUD-046")
@pytest.mark.parametrize("com_mandato", [True, False])
def test_remanescente_entra_no_impedimento_de_quem_tem_mandato(
    client, legislatura_atual, com_mandato
):
    materia = mommy.make(
        MateriaLegislativa,
        numero=2026,
        ano=2025,
        data_apresentacao=datetime.date(2025, 9, 1),
    )
    mommy.make(NormaJuridica, materia=materia)
    loa = mommy.make(
        Loa,
        ano=2026,
        publicado=True,
        materia=materia,
        disp_total=Decimal("20000.00"),
        disp_saude=Decimal("10000.00"),
        disp_diversos=Decimal("10000.00"),
    )
    # o campo "ativo" do cadastro vai ao contrário do mandato: não é ele que vale
    parlamentar = _parlamentar(
        "Parlamentar",
        legislatura_atual if com_mandato else None,
        ativo=not com_mandato,
    )
    loa.parlamentares.add(parlamentar)
    _emenda(loa, parlamentar, EmendaLoa.APROVACAO_LEGAL, valor="7000.00")
    _emenda(loa, parlamentar, EmendaLoa.IMPEDIMENTO_TECNICO, valor="2000.00")

    pagina = _detalhe(client, loa).content.decode()

    # 2.000,00 impedidos e 1.000,00 que sobraram sem emenda: quem tem mandato
    # vê 3.000,00 de impedimento a sanar; quem não tem, só os 2.000,00
    assert "3.000,00" in pagina
    assert ("2.000,00" in pagina) is not com_mandato


@pytest.mark.spec("LOA-CRUD-049")
def test_ajuste_impedido_fica_no_impedimento_e_nao_no_ja_destinado(client):
    # LOA sem registro de prestação de contas, com 10.000,00 por tipo
    oficio, parlamentar = _oficio_de_ajuste(2076)
    oficio.loa.update_disponibilidades()
    # o hook de busca do ajuste lê o M2M antes de haver pk
    registro = mommy.prepare(
        RegistroAjusteLoa,
        oficio_ajuste_loa=oficio,
        numero=1,
        ano=oficio.loa.ano,
        tipo=EmendaLoa.DIVERSOS,
        fase=RegistroAjusteLoa.AJUSTE_IMPEDIDO,
        unidade=None,
        entidade=None,
        descricao="Ajuste 1",
    )
    registro.save(auto_update_search=False)
    RegistroAjusteLoaParlamentar.objects.create(
        registro=registro, parlamentar=parlamentar, valor=Decimal("1000.00")
    )

    pagina = _detalhe(client, oficio.loa).content.decode()

    # os 1.000,00 do ajuste são impedimento: nada foi destinado dos 10.000,00
    assert "1.000,00" in pagina
    assert "9.000,00" not in pagina


@pytest.mark.spec("LOA-CRUD-050")
def test_superusuario_ve_as_colunas_de_valor_mesmo_zeradas(client, superuser):
    loa = _loa(2077, publicado=True, com_norma=False)

    anonimo = _detalhe(client, loa).content.decode()
    client.force_login(superuser)
    pagina = _detalhe(client, loa).content.decode()

    assert "Impedimentos<br>Técnicos" not in anonimo
    assert pagina.count("Impedimentos<br>Técnicos") == 2
    assert pagina.count("Sem<br>Destinação") == 2
    # a execução dos empenhos fica na prestação de contas
    assert "EMPENHADOS" not in pagina


@pytest.mark.spec("LOA-CRUD-061")
def test_resumo_por_entidade_soma_o_parlamentar_uma_vez(client):
    loa, parlamentar = _loa_com_dez_mil_por_tipo(2078)
    entidade = mommy.make(Entidade, nome_fantasia="Entidade de teste")
    # duas emendas do mesmo parlamentar para a entidade, em unidades diferentes
    for codigo, valor in (("01", "1000.00"), ("02", "2000.00")):
        emenda = _emenda(loa, parlamentar, EmendaLoa.PROPOSTA, valor=valor)
        EmendaLoa.objects.filter(pk=emenda.pk).update(
            entidade=entidade,
            unidade=mommy.make(
                UnidadeOrcamentaria,
                loa=loa,
                codigo=codigo,
                especificacao=f"Unidade {codigo}",
            ),
        )

    pagina = _detalhe(client, loa).content.decode()
    tabela = pagina[
        pagina.index(
            'class="table table-form table-bordered table-entidade-totalize"'
        ) :
    ]
    tabela = tabela[: tabela.index("</table>")]

    assert "ENTIDADE DE TESTE" in tabela
    assert tabela.count(parlamentar.nome_parlamentar) == 1
    assert tabela.count("3.000,00") == 3  # entidade, parlamentar e total geral


@pytest.mark.spec("LOA-CRUD-054")
def test_loa_sem_parlamentares_abre_o_detalhe(client):
    loa = _loa(2079, publicado=True, com_norma=False)
    loa.loaparlamentar_set.all().delete()

    resposta = _detalhe(client, loa)

    assert resposta.status_code == 200
    assert "Resumo Geral das Emendas Impositivas Parlamentares" in (
        resposta.content.decode()
    )


@pytest.mark.spec("LOA-CRUD-058")
def test_emenda_sem_parlamentar_entra_com_valor_zero_nos_resumos(client):
    loa, parlamentar = _loa_com_dez_mil_por_tipo(2069)
    _emenda(loa, parlamentar, EmendaLoa.PROPOSTA)
    sem_parlamentar = EmendaLoa(
        loa=loa,
        fase=EmendaLoa.PROPOSTA,
        tipo=EmendaLoa.DIVERSOS,
        valor=Decimal("500.00"),
        finalidade="Sem parlamentar",
        entidade=mommy.make(Entidade, nome_fantasia="Entidade de teste"),
    )
    sem_parlamentar.save()

    resposta = _detalhe(client, loa)

    assert resposta.status_code == 200
    pagina = resposta.content.decode()
    assert "ENTIDADE DE TESTE" in pagina
    tabela = pagina[pagina.index("table-entidade-totalize") :]
    assert "None" not in tabela[: tabela.index("</table>")]


# A exclusão real consulta a view SQL das despesas, que não existe no banco
# de teste: os dois testes trocam o delete() do model.


@pytest.mark.spec("LOA-CRUD-064")
def test_excluir_loa_com_emenda_avisa_e_nao_exclui(client, superuser):
    loa, parlamentar = _loa_com_dez_mil_por_tipo(2068)
    emenda = _emenda(loa, parlamentar, EmendaLoa.PROPOSTA)
    client.force_login(superuser)

    with mock.patch.object(
        Loa, "delete", side_effect=ProtectedError("protegido", {emenda})
    ):
        resposta = client.post(f"/loa/{loa.pk}/delete")

    assert resposta.status_code == 200
    assert "Registro não pode ser removido" in resposta.content.decode()


@pytest.mark.spec("LOA-CRUD-064")
def test_excluir_loa_sem_emenda_volta_para_a_lista(client, superuser):
    loa = _loa(2067, publicado=True, com_norma=False)
    client.force_login(superuser)

    with mock.patch.object(Loa, "delete") as excluir:
        resposta = client.post(f"/loa/{loa.pk}/delete")

    assert resposta.status_code == 302
    excluir.assert_called_once()


def _loa_de_virada(legislatura_atual, rcl_definitiva, **valores):
    """LOA de 2025, primeiro ano da legislatura atual, com um parlamentar só
    da legislatura anterior, um só da atual e um reeleito."""
    anterior = Legislatura.objects.create(
        numero=98,
        data_inicio=datetime.date(2021, 1, 1),
        data_fim=datetime.date(2024, 12, 31),
        data_eleicao=datetime.date(2020, 10, 4),
    )
    loa = mommy.make(
        Loa,
        ano=2025,
        publicado=True,
        rcl_previa=Decimal("100000.00"),
        receita_corrente_liquida=Decimal(
            "120000.00" if rcl_definitiva else "100000.00"
        ),
        **{"disp_total": Decimal("30000.00"), **valores},
    )
    so_na_anterior = _parlamentar("Só na anterior", anterior)
    so_na_atual = _parlamentar("Só na atual", legislatura_atual)
    reeleito = _parlamentar("Reeleito", anterior)
    mommy.make(Mandato, parlamentar=reeleito, legislatura=legislatura_atual)
    loa.parlamentares.add(so_na_anterior, so_na_atual, reeleito)
    return loa, so_na_anterior, so_na_atual, reeleito


@pytest.mark.spec("LOA-CRUD-067")
@pytest.mark.parametrize("rcl_definitiva", [False, True])
def test_loa_de_virada_troca_de_parlamentares_com_a_rcl_definitiva(
    legislatura_atual, rcl_definitiva
):
    loa, so_na_anterior, so_na_atual, reeleito = _loa_de_virada(
        legislatura_atual, rcl_definitiva
    )

    esperado = (
        {so_na_atual.pk, reeleito.pk}
        if rcl_definitiva
        else {so_na_anterior.pk, reeleito.pk}
    )
    assert Loa.service.parlamentares_com_mandato(loa) == esperado


@pytest.mark.spec("LOA-CRUD-069")
@pytest.mark.parametrize("rcl_definitiva", [False, True])
def test_valor_por_parlamentar_da_loa_de_virada_divide_pelos_originais(
    client, legislatura_atual, rcl_definitiva
):
    loa, so_na_anterior, so_na_atual, reeleito = _loa_de_virada(
        legislatura_atual, rcl_definitiva
    )
    # a legislatura nova tem mais parlamentares que a do projeto
    loa.parlamentares.add(_parlamentar("Outro só na atual", legislatura_atual))

    assert Loa.service.parlamentares_originais(loa) == {so_na_anterior.pk, reeleito.pk}

    # 30.000,00 pelos dois parlamentares da legislatura do projeto
    assert "R$ 15.000,00" in _detalhe(client, loa).content.decode()


@pytest.mark.spec("LOA-CRUD-039")
def test_valor_por_parlamentar_divide_pelos_vinculados_com_mandato(
    client, legislatura_atual
):
    loa = mommy.make(
        Loa,
        ano=2026,
        publicado=True,
        disp_total=Decimal("30000.00"),
        disp_saude=Decimal("14000.00"),
        disp_diversos=Decimal("16000.00"),
    )
    loa.parlamentares.add(
        _parlamentar("Com mandato A", legislatura_atual),
        _parlamentar("Com mandato B", legislatura_atual),
        _parlamentar("Sem mandato", ativo=True),
    )

    pagina = _detalhe(client, loa).content.decode()

    # três vinculados, dois com mandato
    for valor in ("15.000,00", "7.000,00", "8.000,00"):
        assert f"R$ {valor}" in pagina


def _disponibilidades(loa):
    return {
        lp.parlamentar.nome_parlamentar: (lp.disp_saude, lp.disp_diversos)
        for lp in loa.loaparlamentar_set.select_related("parlamentar")
    }


@pytest.mark.spec("LOA-CRUD-027")
def test_disponibilidade_e_dividida_igualmente_entre_os_vinculados(legislatura_atual):
    loa = mommy.make(
        Loa,
        ano=2026,
        disp_saude=Decimal("1000.00"),
        disp_diversos=Decimal("2000.00"),
    )
    loa.parlamentares.add(
        _parlamentar("A", legislatura_atual),
        _parlamentar("B", legislatura_atual),
        _parlamentar("C"),
    )

    loa.update_disponibilidades()

    parte = (Decimal("333.33"), Decimal("666.66"))
    assert _disponibilidades(loa) == {"A": parte, "B": parte, "C": parte}


@pytest.mark.spec("LOA-CRUD-070")
def test_loa_de_virada_divide_a_previa_pelos_originais_e_o_resto_pelos_novos(
    legislatura_atual,
):
    # prévia de 1.000,00 por tipo e definitiva de 1.200,00; dois originais e
    # três com mandato na legislatura nova (o reeleito está nos dois grupos)
    loa, so_na_anterior, _so_na_atual, _reeleito = _loa_de_virada(
        legislatura_atual,
        rcl_definitiva=True,
        perc_disp_saude=Decimal("1.00"),
        perc_disp_diversos=Decimal("1.00"),
        disp_saude=Decimal("1200.00"),
        disp_diversos=Decimal("1200.00"),
    )
    loa.parlamentares.add(_parlamentar("Outro só na atual", legislatura_atual))
    # quem saiu tem 100,00 impedidos em áreas diversas
    _emenda(loa, so_na_anterior, EmendaLoa.IMPEDIMENTO_TECNICO, valor="100.00")

    loa.update_disponibilidades()

    assert _disponibilidades(loa) == {
        # a parte da prévia, menos o próprio impedimento
        "Só na anterior": (Decimal("500.00"), Decimal("400.00")),
        # a parte da prévia e a parte do que é dividido entre os novos
        "Reeleito": (Decimal("566.66"), Decimal("600.00")),
        # (200,00) / 3 na saúde; (200,00 + 100,00) / 3 em áreas diversas
        "Só na atual": (Decimal("66.66"), Decimal("100.00")),
        "Outro só na atual": (Decimal("66.66"), Decimal("100.00")),
    }


@pytest.mark.spec("LOA-CRUD-070")
def test_loa_de_virada_antes_da_rcl_definitiva_divide_entre_os_originais(
    legislatura_atual,
):
    loa, _so_na_anterior, _so_na_atual, _reeleito = _loa_de_virada(
        legislatura_atual,
        rcl_definitiva=False,
        disp_saude=Decimal("1000.00"),
        disp_diversos=Decimal("1000.00"),
    )

    loa.update_disponibilidades()

    valores = _disponibilidades(loa)
    assert valores["Só na anterior"] == (Decimal("500.00"), Decimal("500.00"))
    assert valores["Reeleito"] == (Decimal("500.00"), Decimal("500.00"))
    assert valores["Só na atual"] == (Decimal("0.00"), Decimal("0.00"))


@pytest.mark.spec("LOA-CRUD-020")
def test_formulario_da_loa_oferece_quem_tem_mandato_e_os_ja_vinculados(
    legislatura_atual,
):
    anterior = Legislatura.objects.create(
        numero=98,
        data_inicio=datetime.date(2021, 1, 1),
        data_fim=datetime.date(2024, 12, 31),
        data_eleicao=datetime.date(2020, 10, 4),
    )
    loa = mommy.make(Loa, ano=2025)
    do_projeto = _parlamentar("Do projeto", anterior, ativo=False)
    do_ano = _parlamentar("Do ano", legislatura_atual, ativo=False)
    vinculado = _parlamentar("Vinculado sem mandato", ativo=False)
    _parlamentar("Ativo sem mandato", ativo=True)
    loa.parlamentares.add(vinculado)

    oferecidos = {
        pk for pk, _nome in LoaForm(instance=loa).fields["parlamentares"].choices
    }

    assert oferecidos == {do_projeto.pk, do_ano.pk, vinculado.pk}


@pytest.mark.spec("LOA-CRUD-020")
def test_formulario_de_loa_nova_sem_mandato_registrado_oferece_os_ativos():
    ativo = _parlamentar("Ativo", ativo=True)
    _parlamentar("Inativo", ativo=False)

    oferecidos = {pk for pk, _nome in LoaForm().fields["parlamentares"].choices}

    assert oferecidos == {ativo.pk}


# ------------------------------------- responsável pelas Emendas Coletivas


def _grupo_operador_da_loa():
    from django.contrib.auth.models import Group, Permission

    grupo, criado = Group.objects.get_or_create(name="Operador da LOA (teste)")
    if not criado:
        return grupo
    for codename in ("add_emendaloa", "change_emendaloa", "emendaloa_full_editor"):
        grupo.permissions.add(
            Permission.objects.get(content_type__app_label="loa", codename=codename)
        )
    return grupo


@pytest.mark.spec("LOA-CRUD-072")
def test_responsavel_pelas_coletivas_oferece_so_operador_da_loa_sem_autor(
    django_user_model, operador_loa, editor_contabil, autor, superuser
):
    from sapl.base.models import OperadorAutor

    pelo_grupo = django_user_model.objects.create_user(
        email="grupo@test.local", password="testpass123!"
    )
    pelo_grupo.groups.add(_grupo_operador_da_loa())
    inativo = django_user_model.objects.create_user(
        email="inativo@test.local", password="testpass123!"
    )
    inativo.is_active = False
    inativo.save()
    inativo.groups.add(_grupo_operador_da_loa())
    operador_e_autor = django_user_model.objects.create_user(
        email="operador_e_autor@test.local", password="testpass123!"
    )
    operador_e_autor.groups.add(_grupo_operador_da_loa())
    mommy.make(
        OperadorAutor,
        user=operador_e_autor,
        autor=autor.operadorautor_set.first().autor,
    )

    oferecidos = set(
        LoaForm().fields["responsavel_coletivas"].queryset.values_list("pk", flat=True)
    )

    assert oferecidos == {operador_loa.pk, pelo_grupo.pk, superuser.pk}
    for user in (operador_loa, pelo_grupo, superuser):
        assert Loa.service.pode_ser_responsavel_coletivas(user)
    for user in (editor_contabil, autor, inativo, operador_e_autor):
        assert not Loa.service.pode_ser_responsavel_coletivas(
            django_user_model.objects.get(pk=user.pk)
        )


@pytest.mark.spec("LOA-CRUD-072")
def test_formulario_grava_o_responsavel_e_recusa_quem_nao_e_elegivel(
    operador_loa, editor_contabil
):
    loa = mommy.make(Loa, ano=2076, receita_corrente_liquida=Decimal("1000.00"))
    dados = {
        "ano": 2076,
        "receita_corrente_liquida": "1000.00",
        "perc_disp_total": "2.00",
        "perc_disp_saude": "1.00",
        "perc_disp_diversos": "1.00",
        "yaml_obs": "",
    }

    form = LoaForm(
        instance=loa, data={**dados, "responsavel_coletivas": editor_contabil.pk}
    )
    assert not form.is_valid()
    assert "responsavel_coletivas" in form.errors

    form = LoaForm(
        instance=loa, data={**dados, "responsavel_coletivas": operador_loa.pk}
    )
    assert form.is_valid(), form.errors
    form.save()
    loa.refresh_from_db()
    assert loa.responsavel_coletivas_id == operador_loa.pk


@pytest.mark.spec("LOA-CRUD-072")
def test_api_publica_da_loa_nao_mostra_o_responsavel(client, operador_loa):
    loa = _loa(
        2077, publicado=True, com_norma=False, responsavel_coletivas=operador_loa
    )

    response = client.get(f"/api/loa/loa/{loa.pk}/")

    assert response.status_code == 200
    assert "responsavel_coletivas" not in response.json()
