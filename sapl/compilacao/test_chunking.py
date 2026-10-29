import pytest

from sapl.compilacao import chunking
from sapl.compilacao.chunking import No, construir_chunks, estimar_tokens

pytestmark = pytest.mark.django_db

TITULO = "Lei Ordinária nº 1 de 2020"
EMENTA = "Dispõe sobre diárias de viagem."


def no(pk, pai, tipo, ordem, rotulo="", texto=""):
    return No(pk, pai, tipo, 0, ordem, rotulo, texto)


def norma_simples():
    return [
        no(1, None, "Articulação", 1000),
        no(2, 1, "Ementa", 2000, texto=EMENTA),
        no(3, None, "Articulação", 3000),
        no(4, 3, "Capítulo", 4000, "Capítulo I", "DAS DIÁRIAS"),
        no(5, 4, "Artigo", 5000, "Art. 1º."),
        no(6, 5, "Caput", 6000, texto="Será concedida diária ao servidor em viagem."),
        no(7, 5, "Parágrafo", 7000, "§ 1º", "A diária cobre alimentação."),
        no(8, 4, "Artigo", 8000, "Art. 2º."),
        no(9, 8, "Caput", 9000, texto="O pagamento depende de solicitação:"),
        no(10, 9, "Inciso", 10000, "I", "prévia autorização;"),
        no(11, 9, "Inciso", 11000, "II", "relatório final."),
    ]


def por_raiz(chunks):
    return {c.raiz_pk: c for c in chunks}


def test_uma_unidade_por_artigo_sem_vazamento_entre_artigos():
    chunks = por_raiz(construir_chunks(norma_simples(), TITULO, EMENTA))

    art1, art2 = chunks[5].texto, chunks[8].texto
    assert "Art. 1º. Será concedida diária" in art1
    assert "§ 1º A diária cobre alimentação." in art1
    assert "Art. 2º" not in art1 and "prévia autorização" not in art1
    assert "Art. 2º. O pagamento depende de solicitação:" in art2
    assert "I prévia autorização;" in art2 and "Art. 1º" not in art2


def test_paragrafo_e_inciso_nao_geram_chunk_proprio_quando_ha_artigo():
    raizes = {c.raiz_pk for c in construir_chunks(norma_simples(), TITULO, EMENTA)}

    assert raizes == {2, 5, 8}  # ementa e dois artigos


def test_cabecalho_com_norma_ementa_e_estrutura():
    art1 = por_raiz(construir_chunks(norma_simples(), TITULO, EMENTA))[5]

    assert art1.texto.splitlines()[:3] == [TITULO, EMENTA, "Capítulo I DAS DIÁRIAS"]
    assert art1.metadata["caminho"] == [EMENTA, "Capítulo I DAS DIÁRIAS"]


def test_ementa_sem_duplicar_e_opcao_de_nao_incluir_ementa():
    chunks = por_raiz(construir_chunks(norma_simples(), TITULO, EMENTA))
    assert chunks[2].texto == f"{TITULO}\n{EMENTA}"

    sem = por_raiz(
        construir_chunks(norma_simples(), TITULO, EMENTA, incluir_ementa=False)
    )
    assert EMENTA not in sem[5].texto


def test_metadata_e_hash_estavel():
    a = por_raiz(construir_chunks(norma_simples(), TITULO, EMENTA))[5]
    b = por_raiz(construir_chunks(norma_simples(), TITULO, EMENTA))[5]

    assert a.metadata["hash"] == b.metadata["hash"]
    assert a.metadata["chunk_strategy"] == "v2"
    assert (a.metadata["tipo"], a.metadata["rotulo"]) == ("Artigo", "Art. 1º.")
    assert (a.metadata["ordem"], a.metadata["ordem_fim"]) == (5000, 7000)
    assert a.metadata["tokens_estimados"] == estimar_tokens(a.texto)

    nos = norma_simples()
    nos[5] = no(6, 5, "Caput", 6000, texto="Texto diferente.")
    alterado = por_raiz(construir_chunks(nos, TITULO, EMENTA))
    assert alterado[5].metadata["hash"] != a.metadata["hash"]
    # a edição do Art. 1º não muda o chunk do Art. 2º (sem cascata)
    assert (
        alterado[8].metadata["hash"]
        == por_raiz(construir_chunks(norma_simples(), TITULO, EMENTA))[8].metadata[
            "hash"
        ]
    )


def test_artigo_revogado_ou_vazio_e_ignorado():
    nos = norma_simples() + [
        no(20, 4, "Artigo", 12000, "Art. 3º."),
        no(21, 20, "Caput", 13000, texto="(Revogado)"),
        no(22, 4, "Artigo", 14000, "Art. 4º."),
        no(23, 22, "Caput", 15000, texto="Vetado."),
        no(24, 4, "Artigo", 16000, "Art. 5º."),
    ]

    assert {c.raiz_pk for c in construir_chunks(nos, TITULO, EMENTA)} == {2, 5, 8}


def test_artigo_grande_divide_em_partes_com_contexto():
    nos = [
        no(1, None, "Articulação", 1000),
        no(2, 1, "Artigo", 2000, "Art. 9º."),
        no(3, 2, "Caput", 3000, texto="Compete à Secretaria:"),
    ]
    for i in range(1, 31):
        nos.append(
            no(
                100 + i,
                3,
                "Inciso",
                4000 + i,
                f"I{i}",
                f"atribuição número {i} " + "x" * 120,
            )
        )
    nos.append(no(500, 3, "Inciso", 9000, "XL", "coordenar:"))
    for j in range(1, 12):
        nos.append(
            no(600 + j, 500, "Alinea", 9100 + j, f"{j})", f"ação {j} " + "y" * 120)
        )

    chunks = construir_chunks(nos, TITULO, EMENTA, max_tokens=250)

    assert len(chunks) > 3
    assert [c.parte for c in chunks] == list(range(len(chunks)))
    assert all(c.partes == len(chunks) for c in chunks)
    assert all(c.raiz_pk == 2 for c in chunks)
    for c in chunks:
        assert c.texto.splitlines()[0] == TITULO
        assert "Art. 9º. Compete à Secretaria:" in c.texto
        assert c.metadata["tokens_estimados"] <= 250 + 40
    # partes com alíneas repetem o inciso que as governa
    com_alineas = [c for c in chunks if "ação " in c.texto]
    assert all("XL coordenar:" in c.texto for c in com_alineas)
    # nenhuma linha se perde
    texto_total = "\n".join(c.texto for c in chunks)
    assert all(f"atribuição número {i} " in texto_total for i in range(1, 31))
    assert all(f"ação {j} " in texto_total for j in range(1, 12))


def test_linha_maior_que_o_orcamento_vira_janelas_com_sobreposicao():
    palavras = " ".join(f"palavra{i}" for i in range(900))
    nos = [
        no(1, None, "Articulação", 1000),
        no(2, 1, "Artigo", 2000, "Art. 1º."),
        no(3, 2, "Caput", 3000, texto=palavras),
    ]

    chunks = construir_chunks(nos, TITULO, "", max_tokens=200)

    assert len(chunks) > 1
    assert "palavra0" in chunks[0].texto and "palavra899" in chunks[-1].texto
    ultima_da_primeira = chunks[0].texto.split()[-1]
    assert ultima_da_primeira in chunks[1].texto  # sobreposição


def test_artigo_aninhado_em_bloco_de_alteracao_traz_o_artigo_pai_no_cabecalho():
    nos = [
        no(1, None, "Articulação", 1000),
        no(2, 1, "Artigo", 2000, "Art. 2º."),
        no(3, 2, "Caput", 3000, texto="O art. 48 da Lei 2.761 passa a vigorar assim:"),
        no(4, 3, "Bloco Alteração", 4000),
        no(5, 4, "Artigo", 5000, "Art. 48."),
        no(6, 5, "Caput", 6000, texto="A contribuição patronal será de 14%."),
    ]

    chunks = por_raiz(construir_chunks(nos, TITULO, ""))

    assert "A contribuição" not in chunks[2].texto
    aninhado = chunks[5].texto.splitlines()
    assert aninhado[1] == "Art. 2º. O art. 48 da Lei 2.761 passa a vigorar assim:"
    assert "Art. 48. A contribuição patronal será de 14%." in aninhado


def test_texto_nao_estruturado_so_solto_e_substantivo():
    longo = " ".join(["preâmbulo"] * 45)
    nos = [
        no(1, None, "Articulação", 1000),
        no(
            2, 1, "Texto Não Estruturado", 2000, texto="Prefeito Municipal assina aqui."
        ),
        no(3, 1, "Texto Não Estruturado", 3000, texto=longo),
        no(4, 1, "Artigo", 4000, "Art. 1º."),
        no(5, 4, "Caput", 5000, texto="Texto do caput:"),
        no(6, 5, "Texto Não Estruturado", 6000, texto=longo),
    ]

    chunks = construir_chunks(nos, TITULO, "")
    por = por_raiz(chunks)

    assert set(por) == {3, 4}  # curto descartado; filho do caput fica no artigo
    assert longo in por[4].texto


def test_anexo_com_conteudo_gera_chunk_e_sem_conteudo_nao():
    nos = [
        no(1, None, "Articulação", 1000),
        no(2, 1, "Anexo", 2000, "Anexo I", "TABELA DE VALORES"),
        no(
            3,
            2,
            "Item",
            3000,
            "1",
            "diária nacional para viagens dentro do país: R$ 300,00",
        ),
        no(4, 1, "Anexo", 4000, "Anexo II"),
    ]

    por = por_raiz(construir_chunks(nos, TITULO, ""))

    assert set(por) == {2}
    assert "Anexo I TABELA DE VALORES" in por[2].texto
    assert "1 diária nacional para viagens dentro do país: R$ 300,00" in por[2].texto


def test_omissis_so_com_reticencias_nao_gera_linha():
    nos = [
        no(1, None, "Articulação", 1000),
        no(2, 1, "Artigo", 2000, "Art. 2º."),
        no(3, 2, "Caput", 3000, texto="Altera a lei:"),
        no(4, 3, "Omissis", 4000, texto="[...]"),
        no(5, 3, "Omissis", 5000, texto="Art. 48. […]"),
    ]

    texto = construir_chunks(nos, TITULO, "")[0].texto

    assert "[...]" not in texto and "Art. 48. […]" in texto


def test_dispositivo_orfao_individualizavel_gera_unidade():
    nos = [
        no(1, None, "Articulação", 1000),
        no(2, 1, "Parágrafo", 2000, "§ 1º", "Texto solto sem artigo."),
    ]

    assert [c.raiz_pk for c in construir_chunks(nos, TITULO, "")] == [2]


def test_artigo_sob_estrutura_revogada_nao_e_indexado():
    nos = norma_simples() + [
        no(30, 3, "Capítulo", 20000, "Capítulo II", "(Revogado)"),
        no(31, 30, "Artigo", 21000, "Art. 9º."),
        no(
            32,
            31,
            "Caput",
            22000,
            texto="Texto que ainda existe no banco mas está sob capítulo revogado.",
        ),
        no(33, 3, "Seção", 23000, "Seção I", "DAS REGRAS"),
        no(34, 33, "Artigo", 24000, "Art. 10."),
        no(35, 34, "Caput", 25000, texto="Texto vigente sob seção vigente."),
    ]

    raizes = {c.raiz_pk for c in construir_chunks(nos, TITULO, EMENTA)}

    assert 31 not in raizes
    assert 34 in raizes


def test_estrutura_com_texto_vazio_nao_e_revogada():
    # "Livro I" costuma ter só rótulo; isso não significa revogação
    nos = [
        no(1, None, "Articulação", 1000),
        no(2, 1, "Livro", 2000, "Livro I", ""),
        no(3, 2, "Título", 3000, "Título I", "DAS NORMAS"),
        no(4, 3, "Artigo", 4000, "Art. 1º."),
        no(5, 4, "Caput", 5000, texto="Texto do artigo sob livro sem título."),
    ]

    assert [c.raiz_pk for c in construir_chunks(nos, TITULO, "")] == [4]


def test_constantes_coerentes():
    assert chunking.MAX_TOKENS > 0 and chunking.TNU_MIN_PALAVRAS > 0
