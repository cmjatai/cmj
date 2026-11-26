"""Checagem de consistência dos IDs das specs (docs/specs/README.md, seção Checagem).

Lê as specs de ``docs/specs/<dominio>/<capacidade>.md``, as marcas
``pytest.mark.spec`` dos testes Python, os títulos ``'ID: ...'`` dos testes
Vitest do v8 e do v2018 e as referências a IDs em todo arquivo versionado, e
devolve a lista de inconsistências. Não usa banco nem Django.
"""

import ast
import re
import subprocess
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from pathlib import Path

DIR_SPECS = "docs/specs"

# Prefixo reservado para exemplos (README, skills): nunca é checado.
PREFIXO_EXEMPLO = "PREFIXO"

MARCADORES_REGRA = {"observado", "desejado", "acordado", "implementado", "retirada"}
SEVERIDADES = {"Crítica", "Alta", "Média", "Baixa"}
MARCADORES_SEG = {"observado", "confirmado"}

CABECALHO = ("Status", "Última verificação", "Código principal", "Testes")

ID_RE = r"[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)*-\d{3}"
RE_ID = re.compile(r"(?<![\w-])(" + ID_RE + r")(?![\w-])")
# Definição: "- ID [marcador] ..." ou "| ID [marcador] | ...".
RE_DEF = re.compile(
    r"^(?P<tipo>-|\|)\s*\**(?P<id>[A-Z][\w-]*?-\d+)\**(?=[\s|]|$)(?P<resto>.*)$"
)
RE_MARCADORES = re.compile(r"\s*\[([^\]]+)\]")
RE_EVIDENCIA = re.compile(r"`([\w./@~-]+\.[A-Za-z0-9]+):(\d+)(?:-(\d+))?`")
RE_CAMPO_CAB = re.compile(r"^(" + "|".join(CABECALHO) + r"):\s*(.*)$")
RE_CAMINHO = re.compile(r"`([^`\s]+)`")
RE_DUVIDA = re.compile(r"^\s*(?:[-*]|#+)\s*\**D(\d+)\b", re.M)
RE_DUVIDA_REF = re.compile(r"\bD(\d+)\b")
# Abreviações depois de um ID completo: "LOA-FASE-056, 057, 071 e 017 a 019".
RE_ABREV = re.compile(r"\s*(?:,|\be|\ba)\s+(\d{3})(?![\w-])")
# Título de teste Vitest que liga regras: 'V8-ARQ-004: ...' ou 'V8-ARQ-004, V8-ARQ-005: ...'.
RE_TITULO_VITEST = re.compile(
    r"""['"`]\s*(""" + ID_RE + r"(?:\s*,\s*" + ID_RE + r""")*)\s*:"""
)

# Frontends cujos testes Vitest (``*.spec.js``) ligam regras pelo título.
FRONTENDS_VITEST = ("_frontend/v8/", "_frontend/v2018/")

EXCLUIR_REFS = (
    "node_modules/",
    "/dist/",
    "collected_static/",
    "_frontend/v6/src/assets/bootstrap-icons/",
)
TAMANHO_MAX_REF = 2 * 1024 * 1024


@dataclass
class Achado:
    codigo: str
    arquivo: str
    linha: int
    mensagem: str
    id: str = ""

    def __str__(self):
        return f"{self.arquivo}:{self.linha}: {self.codigo} {self.mensagem}"

    def as_dict(self):
        return asdict(self)


@dataclass
class Regra:
    id: str
    arquivo: str
    linha: int
    marcadores: list
    texto: str

    @property
    def seg(self):
        return "-SEG-" in self.id

    @property
    def status(self):
        validos = MARCADORES_SEG if self.seg else MARCADORES_REGRA
        for m in self.marcadores:
            if m in validos:
                return m
        return None

    @property
    def severidade(self):
        for m in self.marcadores:
            if m in SEVERIDADES:
                return m
        return None


@dataclass
class Spec:
    arquivo: str
    cabecalho: dict = field(default_factory=dict)
    linha_cabecalho: dict = field(default_factory=dict)
    regras: list = field(default_factory=list)
    duvidas: set = field(default_factory=set)


def prefixo(id_):
    return id_.rsplit("-", 1)[0]


def prefixo_base(id_):
    return prefixo(id_).replace("-SEG", "")


def raiz_id(id_):
    return id_.split("-", 1)[0]


# --- Leitura ---------------------------------------------------------------


def arquivos_spec(raiz):
    base = Path(raiz) / DIR_SPECS
    return sorted(p for p in base.glob("*/*.md") if p.name != "README.md")


def ler_spec(raiz, caminho):
    rel = str(Path(caminho).relative_to(raiz))
    linhas = Path(caminho).read_text(encoding="utf-8").splitlines()
    spec = Spec(arquivo=rel)
    spec.duvidas = {int(n) for n in RE_DUVIDA.findall("\n".join(linhas))}

    # Cabeçalho: parágrafo que começa no primeiro campo e vai até a linha em branco.
    campo = None
    for n, linha in enumerate(linhas, 1):
        m = RE_CAMPO_CAB.match(linha)
        if m:
            campo = m.group(1)
            spec.cabecalho[campo] = m.group(2)
            spec.linha_cabecalho[campo] = n
        elif campo and linha.strip():
            spec.cabecalho[campo] += " " + linha.strip()
        elif campo:
            break

    em_bloco = False
    atual = None
    for n, linha in enumerate(linhas, 1):
        if linha.lstrip().startswith("```"):
            em_bloco = not em_bloco
            atual = None
            continue
        if em_bloco:
            continue
        m = RE_DEF.match(linha)
        if m:
            resto = m.group("resto")
            marcadores = []
            while True:
                mm = RE_MARCADORES.match(resto)
                if not mm:
                    break
                marcadores.append(mm.group(1).strip())
                resto = resto[mm.end() :]
            atual = Regra(m.group("id"), rel, n, marcadores, linha)
            spec.regras.append(atual)
            if m.group("tipo") == "|":
                atual = None
        elif atual and linha.startswith((" ", "\t")) and linha.strip():
            # parágrafo indentado continua a regra, mesmo depois de linha em branco
            atual.texto += "\n" + linha
        elif atual and not linha.strip():
            atual.texto += "\n"
        else:
            atual = None
    return spec


def ids_citados(texto):
    """IDs completos do texto, com as abreviações expandidas para o mesmo prefixo.

    Devolve pares (id, posição). Em "X-070 a 073" valem só as pontas.
    """
    achados = []
    for m in RE_ID.finditer(texto):
        id_ = m.group(1)
        achados.append((id_, m.start()))
        pre = prefixo(id_)
        pos = m.end()
        while True:
            a = RE_ABREV.match(texto, pos)
            if not a:
                break
            achados.append((f"{pre}-{a.group(1)}", a.start(1)))
            pos = a.end()
    return achados


def marcas_python(raiz, caminho):
    """Marcas ``pytest.mark.spec`` de um arquivo: (ids por linha, achados TEST-ARG)."""
    rel = str(Path(caminho).relative_to(raiz))
    try:
        arvore = ast.parse(Path(caminho).read_text(encoding="utf-8"))
    except SyntaxError as e:
        return [], [
            Achado("TEST-ARG", rel, e.lineno or 1, f"arquivo não compila: {e.msg}")
        ]
    marcas, erros = [], []
    for no in ast.walk(arvore):
        if not isinstance(no, ast.Call):
            continue
        f = no.func
        if not (
            isinstance(f, ast.Attribute)
            and f.attr == "spec"
            and isinstance(f.value, ast.Attribute)
            and f.value.attr == "mark"
        ):
            continue
        if no.keywords or not no.args:
            erros.append(
                Achado("TEST-ARG", rel, no.lineno, "pytest.mark.spec sem IDs literais")
            )
        for arg in no.args:
            if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                marcas.append((arg.value, rel, no.lineno))
            else:
                erros.append(
                    Achado(
                        "TEST-ARG",
                        rel,
                        no.lineno,
                        "pytest.mark.spec com argumento que não é string literal",
                    )
                )
    return marcas, erros


def marcas_vitest(raiz, caminho):
    rel = str(Path(caminho).relative_to(raiz))
    texto = Path(caminho).read_text(encoding="utf-8")
    marcas = []
    for m in RE_TITULO_VITEST.finditer(texto):
        linha = texto.count("\n", 0, m.start()) + 1
        for id_ in re.findall(ID_RE, m.group(1)):
            marcas.append((id_, rel, linha))
    return marcas


def arquivos_versionados(raiz):
    raiz = Path(raiz)
    if (raiz / ".git").exists():
        saida = subprocess.run(
            ["git", "ls-files", "-z"],
            cwd=raiz,
            capture_output=True,
            text=True,
            check=True,
        ).stdout
        return [raiz / p for p in saida.split("\0") if p]
    return [p for p in raiz.rglob("*") if p.is_file() and ".git" not in p.parts]


def branch_atual(raiz):
    try:
        return subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=raiz,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return ""


def _ler_texto(caminho):
    try:
        if caminho.stat().st_size > TAMANHO_MAX_REF:
            return None
        return caminho.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None


def _excluido(rel):
    rel = "/" + rel
    return any("/" + e.strip("/") + "/" in rel for e in EXCLUIR_REFS)


def _linhas_arquivo(raiz, rel, cache):
    if rel not in cache:
        p = Path(raiz) / rel
        if p.is_file():
            texto = _ler_texto(p)
            cache[rel] = None if texto is None else len(texto.splitlines())
        else:
            cache[rel] = -1
    return cache[rel]


def _caminhos_cabecalho(valor):
    caminhos = []
    for c in RE_CAMINHO.findall(valor):
        c = c.split(":", 1)[0]
        if "/" in c and "*" not in c and "<" not in c:
            caminhos.append(c.rstrip(","))
    return caminhos


def _coberto(arquivo_teste, caminhos):
    for c in caminhos:
        c = c.rstrip("/")
        if arquivo_teste == c or arquivo_teste.startswith(c + "/"):
            return True
    return False


# --- Checagem --------------------------------------------------------------


def checar(raiz, branch=None):
    raiz = Path(raiz)
    if branch is None:
        branch = branch_atual(raiz)
    achados = []
    specs = [ler_spec(raiz, p) for p in arquivos_spec(raiz)]

    regras = {}
    spec_do_id = {}
    for spec in specs:
        for r in spec.regras:
            if r.id in regras:
                anterior = regras[r.id]
                achados.append(
                    Achado(
                        "SPEC-DUP",
                        r.arquivo,
                        r.linha,
                        f"{r.id} já definido em {anterior.arquivo}:{anterior.linha}",
                        r.id,
                    )
                )
                continue
            regras[r.id] = r
            spec_do_id[r.id] = spec

    achados += _checar_specs(raiz, specs, branch)
    raizes = {raiz_id(i) for i in regras}

    # Testes
    ligacoes = defaultdict(list)  # id -> [(arquivo, linha)]
    locais_ligacao = set()  # já avaliados como ligação de teste, não como referência
    for p in arquivos_versionados(raiz):
        rel = str(p.relative_to(raiz))
        if _excluido(rel):
            continue
        if p.suffix == ".py":
            texto = _ler_texto(p)
            if texto is None or "mark.spec" not in texto:
                continue
            marcas, erros = marcas_python(raiz, p)
            achados += erros
        elif p.name.endswith(".spec.js") and rel.startswith(FRONTENDS_VITEST):
            marcas = marcas_vitest(raiz, p)
        else:
            continue
        for id_, arq, linha in marcas:
            ligacoes[id_].append((arq, linha))
            locais_ligacao.add((arq, linha, id_))

    for id_, locais in sorted(ligacoes.items()):
        regra = regras.get(id_)
        for arq, linha in locais:
            if regra is None:
                achados.append(
                    Achado(
                        "TEST-ORFAO",
                        arq,
                        linha,
                        f"teste ligado a {id_}, que não existe",
                        id_,
                    )
                )
                continue
            if regra.seg:
                achados.append(
                    Achado(
                        "TEST-STATUS",
                        arq,
                        linha,
                        f"teste ligado ao risco {id_}: ligue a uma regra comum",
                        id_,
                    )
                )
            elif regra.status in ("acordado", "desejado", "retirada"):
                dica = {
                    "acordado": "mude a regra para [implementado]",
                    "desejado": "a regra ainda não foi acordada",
                    "retirada": "a regra foi retirada",
                }[regra.status]
                achados.append(
                    Achado(
                        "TEST-STATUS",
                        arq,
                        linha,
                        f"teste ligado a {id_} [{regra.status}]: {dica}",
                        id_,
                    )
                )
            spec = spec_do_id[id_]
            caminhos = _caminhos_cabecalho(spec.cabecalho.get("Testes", ""))
            if not _coberto(arq, caminhos):
                achados.append(
                    Achado(
                        "TEST-CAB",
                        spec.arquivo,
                        spec.linha_cabecalho.get("Testes", 1),
                        f"{arq} testa {id_}, mas não está em Testes:",
                        id_,
                    )
                )

    for id_, regra in regras.items():
        if not regra.seg and regra.status == "implementado" and id_ not in ligacoes:
            achados.append(
                Achado(
                    "TEST-FALTA",
                    regra.arquivo,
                    regra.linha,
                    f"{id_} está [implementado] sem teste ligado",
                    id_,
                )
            )

    # Referências
    for p in arquivos_versionados(raiz):
        rel = str(p.relative_to(raiz))
        if _excluido(rel) or rel == f"{DIR_SPECS}/README.md":
            continue
        texto = _ler_texto(p)
        if not texto:
            continue
        em_spec = rel.startswith(DIR_SPECS + "/")
        for id_, pos in ids_citados(texto):
            if raiz_id(id_) not in raizes or raiz_id(id_) == PREFIXO_EXEMPLO:
                continue
            linha = texto.count("\n", 0, pos) + 1
            if (rel, linha, id_) in locais_ligacao:
                continue
            regra = regras.get(id_)
            if regra is None:
                achados.append(
                    Achado(
                        "REF-ORFA",
                        rel,
                        linha,
                        f"referência a {id_}, que não existe",
                        id_,
                    )
                )
            elif regra.status == "retirada" and not em_spec:
                achados.append(
                    Achado(
                        "REF-RETIRADO",
                        rel,
                        linha,
                        f"referência a {id_}, que foi retirada",
                        id_,
                    )
                )

    return _unicos(achados)


def _checar_specs(raiz, specs, branch):
    achados = []
    cache_linhas = {}
    dono_prefixo = {}
    for spec in specs:
        for campo in CABECALHO:
            if campo not in spec.cabecalho:
                achados.append(
                    Achado(
                        "SPEC-CAB",
                        spec.arquivo,
                        1,
                        f"falta a linha '{campo}:' no cabeçalho",
                    )
                )
        for campo in ("Código principal", "Testes"):
            for c in _caminhos_cabecalho(spec.cabecalho.get(campo, "")):
                if not (Path(raiz) / c).exists():
                    achados.append(
                        Achado(
                            "SPEC-CAB",
                            spec.arquivo,
                            spec.linha_cabecalho[campo],
                            f"caminho de '{campo}:' não existe: {c}",
                        )
                    )

        bases = set()
        for r in spec.regras:
            if not re.fullmatch(ID_RE, r.id):
                achados.append(
                    Achado(
                        "SPEC-FMT",
                        r.arquivo,
                        r.linha,
                        f"{r.id}: ID fora do formato",
                        r.id,
                    )
                )
                continue
            bases.add(prefixo_base(r.id))
            achados += _checar_marcadores(r, spec, branch)
            achados += _checar_evidencia(raiz, r, cache_linhas)

        if len(bases) > 1:
            achados.append(
                Achado(
                    "SPEC-PREFIXO",
                    spec.arquivo,
                    1,
                    "a spec mistura prefixos: " + ", ".join(sorted(bases)),
                )
            )
        for b in bases:
            if b in dono_prefixo and dono_prefixo[b] != spec.arquivo:
                achados.append(
                    Achado(
                        "SPEC-PREFIXO",
                        spec.arquivo,
                        1,
                        f"prefixo {b} também é usado em {dono_prefixo[b]}",
                    )
                )
            dono_prefixo.setdefault(b, spec.arquivo)
    return achados


def _checar_marcadores(r, spec, branch):
    achados = []
    if r.seg:
        if r.severidade is None or r.status is None:
            achados.append(
                Achado(
                    "SPEC-FMT",
                    r.arquivo,
                    r.linha,
                    f"{r.id}: risco exige [severidade] [observado|confirmado]",
                    r.id,
                )
            )
        if branch == "master":
            achados.append(
                Achado(
                    "SPEC-SEG",
                    r.arquivo,
                    r.linha,
                    f"{r.id}: risco -SEG- não pode estar no master (seção Publicação)",
                    r.id,
                )
            )
        if r.severidade in ("Crítica", "Alta"):
            refs = {int(n) for n in RE_DUVIDA_REF.findall(r.texto)}
            if not refs & spec.duvidas:
                achados.append(
                    Achado(
                        "SPEC-SEG",
                        r.arquivo,
                        r.linha,
                        f"{r.id}: risco {r.severidade} sem dúvida D<n> existente",
                        r.id,
                    )
                )
    elif len(r.marcadores) == 0 or r.marcadores[0] not in MARCADORES_REGRA:
        achados.append(
            Achado(
                "SPEC-FMT",
                r.arquivo,
                r.linha,
                f"{r.id}: marcador ausente ou inválido; use "
                + ", ".join(f"[{m}]" for m in sorted(MARCADORES_REGRA)),
                r.id,
            )
        )
    return achados


def _checar_evidencia(raiz, r, cache_linhas):
    achados = []
    evidencias = RE_EVIDENCIA.findall(r.texto)
    if not evidencias:
        if r.status == "retirada":
            return achados
        if r.status == "desejado" and "a criar" in r.texto:
            return achados
        achados.append(
            Achado(
                "SPEC-EVID",
                r.arquivo,
                r.linha,
                f"{r.id}: sem evidência `arquivo:linha`",
                r.id,
            )
        )
        return achados
    for arq, ini, fim in evidencias:
        total = _linhas_arquivo(raiz, arq, cache_linhas)
        if total == -1:
            achados.append(
                Achado(
                    "SPEC-EVID",
                    r.arquivo,
                    r.linha,
                    f"{r.id}: evidência em arquivo inexistente: {arq}",
                    r.id,
                )
            )
        elif total is not None:
            ultima = int(fim or ini)
            if int(ini) < 1 or ultima > total or int(ini) > ultima:
                achados.append(
                    Achado(
                        "SPEC-EVID",
                        r.arquivo,
                        r.linha,
                        f"{r.id}: evidência {arq}:{ini}{'-' + fim if fim else ''} "
                        f"fora do arquivo ({total} linhas)",
                        r.id,
                    )
                )
    return achados


def _unicos(achados):
    vistos, saida = set(), []
    for a in sorted(achados, key=lambda a: (a.arquivo, a.linha, a.codigo, a.mensagem)):
        chave = (a.codigo, a.arquivo, a.linha, a.mensagem)
        if chave not in vistos:
            vistos.add(chave)
            saida.append(a)
    return saida


def filtrar_por_spec(raiz, achados, spec_rel):
    """Achados no arquivo da spec ou ligados a IDs dela."""
    spec = ler_spec(Path(raiz), Path(raiz) / spec_rel)
    ids = {r.id for r in spec.regras}
    prefixos = {prefixo_base(i) for i in ids}
    return [
        a
        for a in achados
        if a.arquivo == spec.arquivo
        or (a.id and (a.id in ids or prefixo_base(a.id) in prefixos))
    ]


if __name__ == "__main__":
    # Execução direta, sem Django: `python cmj/core/services/s_specs_check.py [raiz]`.
    # É assim que o CI (.github/workflows/ci.yml) roda a checagem.
    import sys

    raiz = (
        Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[3]
    )
    achados = checar(raiz)
    for a in achados:
        print(a)
    if achados:
        print(f"{len(achados)} achado(s).", file=sys.stderr)
        sys.exit(1)
    print("Specs consistentes: nenhum achado.")
