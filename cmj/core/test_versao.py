"""Versão de produção do backend (docs/specs/infra/versionamento.md).

Cada teste monta um repositório git em tmp_path, sem rede, com datas de commit
controladas. O banco não é usado, mas a fixture autouse do conftest.py exige
django_db.
"""

import re
import subprocess
from pathlib import Path

import pytest
import yaml

from cmj.core.services import s_versao
from cmj.core.services.s_versao import VersaoError, calcular_versao, criar_tag

pytestmark = pytest.mark.django_db

RAIZ = Path(__file__).resolve().parents[2]


def git(repo, *args, data=None):
    env = {
        "GIT_AUTHOR_NAME": "t",
        "GIT_AUTHOR_EMAIL": "t@t",
        "GIT_COMMITTER_NAME": "t",
        "GIT_COMMITTER_EMAIL": "t@t",
        "GIT_CONFIG_GLOBAL": "/dev/null",
        "GIT_CONFIG_SYSTEM": "/dev/null",
        "PATH": "/usr/bin:/bin:/usr/local/bin",
    }
    if data:
        env["GIT_COMMITTER_DATE"] = data
        env["GIT_AUTHOR_DATE"] = data
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        capture_output=True,
        text=True,
        env=env,
    ).stdout.strip()


def commit(repo, data, msg="c"):
    git(repo, "commit", "--allow-empty", "-q", "-m", msg, data=data)
    return git(repo, "rev-parse", "HEAD")


@pytest.fixture
def repo(tmp_path):
    r = tmp_path / "repo"
    r.mkdir()
    git(r, "init", "-q", "-b", "master")
    return r


@pytest.mark.spec("INFRA-VER-001")
def test_contador_conta_os_commits_do_mes_e_volta_a_1(repo):
    commit(repo, "2026-10-30T10:00:00-03:00")
    commit(repo, "2026-10-31T10:00:00-03:00")
    assert calcular_versao(repo=repo) == "v2026.10.2"
    primeiro = commit(repo, "2026-11-02T10:00:00-03:00")
    assert calcular_versao(repo=repo) == "v2026.11.1"
    commit(repo, "2026-11-03T10:00:00-03:00")
    commit(repo, "2026-11-04T10:00:00-03:00")
    assert calcular_versao(repo=repo) == "v2026.11.3"
    # O mesmo commit sempre tem a mesma versão.
    assert calcular_versao(rev=primeiro, repo=repo) == "v2026.11.1"


@pytest.mark.spec("INFRA-VER-001")
def test_mes_e_o_do_fuso_de_sao_paulo(repo):
    commit(repo, "2026-10-15T10:00:00-03:00")
    # 01/11 às 01h em UTC ainda é 31/10 em São Paulo.
    commit(repo, "2026-11-01T01:00:00+00:00")
    assert calcular_versao(repo=repo) == "v2026.10.2"
    commit(repo, "2026-11-01T00:30:00-03:00")
    assert calcular_versao(repo=repo) == "v2026.11.1"


@pytest.mark.spec("INFRA-VER-002")
def test_commits_de_merge_fora_da_linha_principal_nao_contam(repo):
    commit(repo, "2026-11-01T10:00:00-03:00")
    git(repo, "checkout", "-q", "-b", "ramo")
    commit(repo, "2026-11-02T10:00:00-03:00")
    commit(repo, "2026-11-03T10:00:00-03:00")
    git(repo, "checkout", "-q", "master")
    git(
        repo,
        "merge",
        "-q",
        "--no-ff",
        "-m",
        "merge",
        "ramo",
        data="2026-11-04T10:00:00-03:00",
    )
    assert calcular_versao(repo=repo) == "v2026.11.2"


@pytest.mark.spec("INFRA-VER-003")
def test_clone_raso_e_recusado(repo, tmp_path):
    for dia in (1, 2, 3):
        commit(repo, f"2026-11-0{dia}T10:00:00-03:00")
    raso = tmp_path / "raso"
    git(tmp_path, "clone", "-q", "--depth", "1", f"file://{repo}", str(raso))
    with pytest.raises(VersaoError, match="clone raso"):
        calcular_versao(repo=raso)


@pytest.mark.spec("INFRA-VER-004")
def test_settings_le_a_variavel_de_ambiente_e_cai_para_o_git_e_para_master(
    tmp_path,
):
    codigo = (
        "import django, os; os.environ['DJANGO_SETTINGS_MODULE']='cmj.settings';"
        "from django.conf import settings; print(settings.PORTALCMJ_VERSION)"
    )

    def versao(env):
        base = {"PATH": "/usr/bin:/bin:/usr/local/bin", "HOME": str(tmp_path)}
        r = subprocess.run(
            ["python", "-c", codigo],
            cwd=RAIZ,
            env={**base, **env},
            capture_output=True,
            text=True,
            check=True,
        )
        return r.stdout.strip().splitlines()[-1]

    import os
    import sys

    env = {k: v for k, v in os.environ.items() if k != "PORTALCMJ_VERSION"}
    env["PATH"] = os.path.dirname(sys.executable) + ":" + env.get("PATH", "")
    assert versao({**env, "PORTALCMJ_VERSION": "v2030.01.7"}) == "v2030.01.7"
    assert versao(env) == calcular_versao(repo=RAIZ)
    # Sem git alcançável: "master".
    sem_git = {**env, "PATH": os.path.dirname(sys.executable)}
    assert versao(sem_git) == "master"


@pytest.mark.spec("INFRA-VER-005")
def test_imagem_recebe_a_versao_pelo_argumento_de_build():
    dockerfile = (RAIZ / "docker/Dockerfile").read_text()
    assert re.search(r"^ARG PORTALCMJ_VERSION=master$", dockerfile, re.M)
    assert re.search(r"^ENV PORTALCMJ_VERSION=\$PORTALCMJ_VERSION$", dockerfile, re.M)
    for compose in ("docker-compose.yaml", "docker-compose-dev-mode-prod.yaml"):
        servicos = yaml.safe_load((RAIZ / "docker" / compose).read_text())["services"]
        construidos = [s for s in servicos.values() if "build" in s]
        assert construidos
        for s in construidos:
            assert s["build"]["args"]["PORTALCMJ_VERSION"] == (
                "${PORTALCMJ_VERSION:-master}"
            )


@pytest.fixture
def com_remoto(repo, tmp_path):
    remoto = tmp_path / "remoto.git"
    git(tmp_path, "init", "-q", "--bare", str(remoto))
    git(repo, "remote", "add", "origin", str(remoto))
    return remoto


@pytest.mark.spec("INFRA-VER-006")
def test_tag_criada_e_enviada_para_o_ultimo_commit(repo, com_remoto):
    commit(repo, "2026-11-01T10:00:00-03:00")
    ultimo = commit(repo, "2026-11-02T10:00:00-03:00")
    assert criar_tag(repo=repo) == ("v2026.11.2", True)
    assert git(com_remoto, "rev-parse", "refs/tags/v2026.11.2") == ultimo
    # Rodar de novo (re-run do CI) não recria nem falha.
    assert criar_tag(repo=repo) == ("v2026.11.2", False)


@pytest.mark.spec("INFRA-VER-006")
def test_tag_existente_em_outro_commit_e_erro(repo, com_remoto):
    commit(repo, "2026-11-01T10:00:00-03:00")
    criar_tag(repo=repo)
    git(repo, "commit", "--amend", "--allow-empty", "-q", "-m", "outro")
    with pytest.raises(VersaoError, match="já existe"):
        criar_tag(repo=repo)


@pytest.mark.spec("INFRA-VER-020")
def test_git_e_chamado_sem_shell(repo, monkeypatch):
    commit(repo, "2026-11-01T10:00:00-03:00")
    chamadas = []
    original = subprocess.run

    def espiao(args, **kw):
        chamadas.append((args, kw))
        return original(args, **kw)

    monkeypatch.setattr(s_versao.subprocess, "run", espiao)
    calcular_versao(repo=repo)
    assert chamadas
    for args, kw in chamadas:
        assert isinstance(args, list) and args[0] == "git"
        assert not kw.get("shell")


@pytest.mark.spec("INFRA-VER-021")
def test_so_o_job_de_tag_escreve_e_nunca_em_pull_request():
    ci = yaml.safe_load((RAIZ / ".github/workflows/ci.yml").read_text())
    assert ci["permissions"] == {"contents": "read"}
    for nome, job in ci["jobs"].items():
        if nome == "tag":
            assert job["permissions"] == {"contents": "write"}
            assert job["if"] == "github.event_name == 'push'"
        else:
            assert "permissions" not in job
