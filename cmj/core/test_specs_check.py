"""Checagem de consistência dos IDs das specs (docs/specs/README.md, seção Checagem).

Cada teste monta uma mini-árvore do repositório em tmp_path. O banco não é usado,
mas a fixture autouse do conftest.py exige django_db.
"""

import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

from cmj.core.services.s_specs_check import checar, filtrar_por_spec, ids_citados

pytestmark = pytest.mark.django_db

CABECALHO = """\
# Teste: capacidade

Status: implementado
Última verificação: 2026-11-21 (commit `abc`)
Código principal: `app/codigo.py`
Testes: `app/test_cap.py`, `_frontend/v8/tests/`

"""


def escrever(raiz, rel, texto):
    p = raiz / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(textwrap.dedent(texto), encoding="utf-8")
    return p


@pytest.fixture
def repo(tmp_path):
    escrever(tmp_path, "app/codigo.py", "a = 1\n" * 10)
    escrever(tmp_path, "app/test_cap.py", "")
    (tmp_path / "_frontend/v8/tests").mkdir(parents=True)
    escrever(tmp_path, "docs/specs/README.md", "- PREFIXO-001 [observado] exemplo\n")
    return tmp_path


def spec(repo, corpo, rel="docs/specs/tst/cap.md", cabecalho=CABECALHO):
    escrever(repo, rel, cabecalho + textwrap.dedent(corpo))


def teste_py(repo, corpo, rel="app/test_cap.py"):
    escrever(repo, rel, "import pytest\n\n" + textwrap.dedent(corpo))


def codigos(achados):
    return sorted(a.codigo for a in achados)


def test_repo_consistente_nao_tem_achados(repo):
    spec(
        repo,
        """\
        - TST-CAP-001 [implementado] Regra. Evidência: `app/codigo.py:3`.
        - TST-CAP-002 [observado] Outra, ver TST-CAP-001. Evidência:
          `app/codigo.py:1-10`.
        | TST-CAP-003 [observado] | coluna | `app/codigo.py:2` |
        - TST-CAP-004 [desejado] Nova. Evidência: a criar.
        - TST-CAP-005 [retirada] Substituída por TST-CAP-001.
        """,
    )
    teste_py(
        repo,
        """\
        @pytest.mark.spec("TST-CAP-001", "TST-CAP-002")
        def test_x():
            pass
        """,
    )
    assert checar(repo, branch="master") == []


def test_id_duplicado(repo):
    spec(
        repo,
        """\
        - TST-CAP-001 [observado] A. `app/codigo.py:1`
        - TST-CAP-001 [observado] B. `app/codigo.py:2`
        """,
    )
    assert codigos(checar(repo)) == ["SPEC-DUP"]


def test_marcador_ausente_ou_invalido(repo):
    spec(
        repo,
        """\
        - TST-CAP-001 Sem marcador. `app/codigo.py:1`
        - TST-CAP-002 [aprovado] Inválido. `app/codigo.py:1`
        """,
    )
    assert codigos(checar(repo)) == ["SPEC-FMT", "SPEC-FMT"]


def test_id_fora_do_formato(repo):
    spec(repo, "- TST-CAP-01 [observado] Dois dígitos. `app/codigo.py:1`\n")
    assert codigos(checar(repo)) == ["SPEC-FMT"]


def test_paragrafo_indentado_apos_linha_em_branco_continua_a_regra(repo):
    spec(
        repo,
        """\
        - TST-CAP-001 [observado] Regra.

          Evidência: `app/codigo.py:2`.

        Parágrafo comum, fora da regra: `app/codigo.py:3`.
        - TST-CAP-002 [observado] Sem evidência.

        Evidência fora do bloco: `app/codigo.py:4`.
        """,
    )
    achados = checar(repo)
    assert [(a.codigo, a.id) for a in achados] == [("SPEC-EVID", "TST-CAP-002")]


def test_definicao_em_bloco_de_codigo_e_ignorada(repo):
    spec(repo, "```\n- TST-CAP-001 sem marcador\n```\n")
    assert checar(repo) == []


def test_spec_mistura_prefixos(repo):
    spec(
        repo,
        """\
        - TST-CAP-001 [observado] A. `app/codigo.py:1`
        - TST-OUT-001 [observado] B. `app/codigo.py:1`
        """,
    )
    assert codigos(checar(repo)) == ["SPEC-PREFIXO"]


def test_prefixo_em_duas_specs(repo):
    spec(repo, "- TST-CAP-001 [observado] A. `app/codigo.py:1`\n")
    spec(
        repo,
        "- TST-CAP-002 [observado] B. `app/codigo.py:1`\n",
        rel="docs/specs/tst/outra.md",
    )
    assert codigos(checar(repo)) == ["SPEC-PREFIXO"]


def test_cabecalho_incompleto_e_caminho_inexistente(repo):
    cab = CABECALHO.replace("Código principal: `app/codigo.py`\n", "").replace(
        "`app/test_cap.py`", "`app/nao_existe.py`"
    )
    spec(repo, "- TST-CAP-001 [observado] A. `app/codigo.py:1`\n", cabecalho=cab)
    achados = checar(repo)
    assert codigos(achados) == ["SPEC-CAB", "SPEC-CAB"]
    assert any("Código principal" in a.mensagem for a in achados)
    assert any("app/nao_existe.py" in a.mensagem for a in achados)


def test_evidencia_ausente_inexistente_ou_fora_do_arquivo(repo):
    spec(
        repo,
        """\
        - TST-CAP-001 [observado] Sem evidência.
        - TST-CAP-002 [observado] `app/sumiu.py:1`
        - TST-CAP-003 [observado] `app/codigo.py:5-11`
        - TST-CAP-004 [desejado] Ainda sem evidência.
        """,
    )
    achados = checar(repo)
    assert codigos(achados) == ["SPEC-EVID"] * 4
    assert any("fora do arquivo (10 linhas)" in a.mensagem for a in achados)


def test_risco_seg_no_master_e_sem_duvida(repo):
    spec(
        repo,
        """\
        - TST-CAP-SEG-001 [Alta] [observado] Vetor. Evidência: `app/codigo.py:1`. Decisão: D9.
        - TST-CAP-SEG-002 [Baixa] [confirmado] Vetor. `app/codigo.py:1`

        ## Dúvidas

        - D1. Corrigir?
        """,
    )
    no_master = checar(repo, branch="master")
    assert codigos(no_master) == ["SPEC-SEG", "SPEC-SEG", "SPEC-SEG"]
    no_branch = checar(repo, branch="tst-cap")
    assert codigos(no_branch) == ["SPEC-SEG"]
    assert "sem dúvida" in no_branch[0].mensagem


def test_risco_seg_com_formato_invalido(repo):
    spec(repo, "- TST-CAP-SEG-001 [observado] Sem severidade. `app/codigo.py:1`\n")
    assert codigos(checar(repo, branch="x")) == ["SPEC-FMT"]


def test_marca_de_teste_com_id_inexistente(repo):
    spec(repo, "- TST-CAP-001 [observado] A. `app/codigo.py:1`\n")
    teste_py(
        repo,
        """\
        @pytest.mark.spec("TST-CAP-099")
        def test_x():
            pass
        """,
    )
    assert codigos(checar(repo)) == ["TEST-ORFAO"]


def test_marca_com_argumento_nao_literal(repo):
    spec(repo, "- TST-CAP-001 [observado] A. `app/codigo.py:1`\n")
    teste_py(
        repo,
        """\
        REGRA = "TST-CAP-001"
        pytestmark = [pytest.mark.spec(REGRA)]
        """,
    )
    assert codigos(checar(repo)) == ["TEST-ARG"]


def test_implementado_sem_teste(repo):
    spec(repo, "- TST-CAP-001 [implementado] A. `app/codigo.py:1`\n")
    assert codigos(checar(repo)) == ["TEST-FALTA"]


@pytest.mark.parametrize("marcador", ["acordado", "desejado", "retirada"])
def test_teste_ligado_a_regra_sem_codigo_aprovado(repo, marcador):
    spec(repo, f"- TST-CAP-001 [{marcador}] A. `app/codigo.py:1`\n")
    teste_py(repo, 'pytestmark = pytest.mark.spec("TST-CAP-001")\n')
    assert codigos(checar(repo)) == ["TEST-STATUS"]


def test_teste_ligado_a_risco_seg(repo):
    spec(repo, "- TST-CAP-SEG-001 [Baixa] [observado] V. `app/codigo.py:1`\n")
    teste_py(repo, 'pytestmark = pytest.mark.spec("TST-CAP-SEG-001")\n')
    assert codigos(checar(repo, branch="x")) == ["TEST-STATUS"]


def test_observado_com_teste_e_aceito(repo):
    spec(repo, "- TST-CAP-001 [observado] A. `app/codigo.py:1`\n")
    teste_py(repo, 'pytestmark = pytest.mark.spec("TST-CAP-001")\n')
    assert checar(repo) == []


def test_arquivo_de_teste_fora_do_cabecalho(repo):
    spec(repo, "- TST-CAP-001 [implementado] A. `app/codigo.py:1`\n")
    teste_py(
        repo, 'pytestmark = pytest.mark.spec("TST-CAP-001")\n', rel="outro/test_y.py"
    )
    achados = checar(repo)
    assert codigos(achados) == ["TEST-CAB"]
    assert "outro/test_y.py" in achados[0].mensagem


def test_titulos_vitest_ligam_regras(repo):
    spec(
        repo,
        """\
        - TST-CAP-001 [implementado] A. `app/codigo.py:1`
        - TST-CAP-002 [implementado] B. `app/codigo.py:1`
        """,
    )
    escrever(
        repo,
        "_frontend/v8/tests/cap.spec.js",
        """\
        it('TST-CAP-001: faz A', () => {})
        it.each([1, 2])('TST-CAP-002, TST-CAP-003: faz B (%s)', () => {})
        """,
    )
    achados = checar(repo)
    assert codigos(achados) == ["TEST-ORFAO"]
    assert "TST-CAP-003" in achados[0].mensagem


def test_referencias_orfas_e_retiradas(repo):
    spec(
        repo,
        """\
        - TST-CAP-001 [observado] A. `app/codigo.py:1`
        - TST-CAP-002 [retirada] Substituída por TST-CAP-001. Ver TST-CAP-002.
        """,
    )
    escrever(
        repo,
        "app/views.py",
        "# TST-CAP-002 e TST-CAP-007\n# OUTRO-X-001 não é das specs\n",
    )
    achados = checar(repo)
    assert codigos(achados) == ["REF-ORFA", "REF-RETIRADO"]
    assert all(a.arquivo == "app/views.py" for a in achados)


def test_readme_e_prefixo_de_exemplo_nao_sao_checados(repo):
    spec(repo, "- TST-CAP-001 [observado] A. `app/codigo.py:1`\n")
    escrever(repo, "docs/specs/README.md", "Como `TST-CAP-SEG-001`.\n")
    escrever(repo, ".claude/skills/x/SKILL.md", "- PREFIXO-001 [desejado] ...\n")
    assert checar(repo) == []


def test_abreviacoes_sao_expandidas():
    texto = "(TST-CAP-056, 057, 064 e 017 a 019; 2026)"
    assert [i for i, _ in ids_citados(texto)] == [
        "TST-CAP-056",
        "TST-CAP-057",
        "TST-CAP-064",
        "TST-CAP-017",
        "TST-CAP-019",
    ]


def test_abreviacao_orfa_e_apontada(repo):
    spec(
        repo, "- TST-CAP-001 [observado] A, ver TST-CAP-001 e 002. `app/codigo.py:1`\n"
    )
    assert codigos(checar(repo)) == ["REF-ORFA"]


def test_filtro_por_spec(repo):
    spec(repo, "- TST-CAP-001 [implementado] A. `app/codigo.py:1`\n")
    spec(
        repo,
        "- TST-OUT-001 [implementado] B. `app/codigo.py:1`\n",
        rel="docs/specs/tst/outra.md",
    )
    achados = checar(repo)
    assert len(achados) == 2
    filtrados = filtrar_por_spec(repo, achados, "docs/specs/tst/outra.md")
    assert [a.id for a in filtrados] == ["TST-OUT-001"]


SCRIPT = Path(__file__).parent / "services" / "s_specs_check.py"


def rodar_script(raiz):
    return subprocess.run(
        [sys.executable, str(SCRIPT), str(raiz)], capture_output=True, text=True
    )


def test_script_direto_sai_com_0_sem_achados(repo):
    spec(repo, "- TST-CAP-001 [observado] A. `app/codigo.py:1`\n")
    r = rodar_script(repo)
    assert r.returncode == 0
    assert "nenhum achado" in r.stdout


def test_script_direto_sai_com_1_com_achados(repo):
    spec(repo, "- TST-CAP-001 [implementado] A. `app/codigo.py:1`\n")
    r = rodar_script(repo)
    assert r.returncode == 1
    assert "TEST-FALTA" in r.stdout
