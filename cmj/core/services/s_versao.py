"""Versão de produção do backend: ``vAAAA.MM.N`` (docs/specs/infra/versionamento.md).

Só biblioteca padrão: roda no CI e no servidor sem as dependências do projeto.

    python3 cmj/core/services/s_versao.py          # imprime a versão do HEAD
    python3 cmj/core/services/s_versao.py --tag    # cria e envia a tag da versão do HEAD
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path

FUSO = "America/Sao_Paulo"
RAIZ = Path(__file__).resolve().parents[3]


class VersaoError(Exception):
    pass


def _git(repo, *args):
    # Lista de argumentos, sem shell; o fuso vale para o format-local das datas.
    r = subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True,
        text=True,
        env={**os.environ, "TZ": FUSO},
    )
    if r.returncode != 0:
        raise VersaoError(r.stderr.strip() or f"git {' '.join(args)} falhou")
    return r.stdout.strip()


def calcular_versao(rev="HEAD", repo=RAIZ):
    if _git(repo, "rev-parse", "--is-shallow-repository") == "true":
        raise VersaoError(
            "clone raso: o número da versão sairia errado; rode git fetch --unshallow"
        )
    # Meses dos commits da linha principal, do mais novo para o mais antigo.
    meses = _git(
        repo,
        "log",
        "--first-parent",
        "--format=%cd",
        "--date=format-local:%Y.%m",
        rev,
        "--",
    ).split()
    mes = meses[0]
    n = 0
    for m in meses:
        if m != mes:
            break
        n += 1
    return f"v{mes}.{n}"


def criar_tag(rev="HEAD", repo=RAIZ, remoto="origin"):
    """Cria a tag da versão de ``rev`` e a envia ao remoto.

    Devolve ``(versao, criada)``. Tag existente no mesmo commit não é recriada;
    em outro commit, é erro.
    """
    versao = calcular_versao(rev, repo)
    commit = _git(repo, "rev-parse", f"{rev}^{{commit}}")
    try:
        existente = _git(repo, "rev-parse", f"refs/tags/{versao}^{{commit}}")
    except VersaoError:
        existente = None
    if existente == commit:
        return versao, False
    if existente:
        raise VersaoError(
            f"a tag {versao} já existe no commit {existente[:9]}, "
            f"e não em {commit[:9]}: o histórico do master foi reescrito?"
        )
    _git(repo, "tag", versao, commit)
    _git(repo, "push", remoto, f"refs/tags/{versao}")
    return versao, True


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--tag", action="store_true", help="cria e envia a tag")
    parser.add_argument("--remoto", default="origin")
    args = parser.parse_args(argv)
    try:
        if args.tag:
            versao, criada = criar_tag(remoto=args.remoto)
            print(f"{versao} {'criada' if criada else 'já existia'}")
        else:
            print(calcular_versao())
    except VersaoError as e:
        print(f"erro: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
