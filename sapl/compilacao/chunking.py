"""
Chunking v2 de Textos Articulados para o chat RAG.

Módulo puro (sem acesso a banco): recebe os dispositivos vigentes de uma
norma já convertidos em `No` e devolve os chunks a indexar.

Princípios:
- A unidade de busca é o que um jurista cita: o Artigo completo (caput,
  parágrafos, incisos, alíneas e itens), o Anexo, a Ementa ou um texto não
  estruturado solto e substantivo. Não há janela de vizinhos.
- Todo chunk leva um cabeçalho de contexto: nome da norma, ementa (truncada)
  e os títulos/artigos ancestrais (Capítulo, Seção, artigo que contém um
  bloco de alteração...).
- Só se divide uma unidade que passa do orçamento de tokens, nas fronteiras
  de dispositivo; cada parte repete o artigo (caput) e o caminho dos
  dispositivos que a governam.
"""

import hashlib
import math
import re
from collections import defaultdict
from dataclasses import dataclass, field

ESTRATEGIA = "v2"

CHARS_POR_TOKEN = 3.2  # medido no índice de produção: ~3,16 caracteres/token
MAX_TOKENS = 350  # escolhido por avaliação: ver docs/rag/07-diagnostico-e-evolucao.md
EMENTA_MAX_CHARS = 300
ANCESTRAL_MAX_CHARS = 300
CABECALHO_CONTINUACAO_MAX_CHARS = 400
TNU_MIN_PALAVRAS = 40
ANEXO_MIN_PALAVRAS = 8
SOBREPOSICAO_JANELA = 0.1

TIPO_ARTICULACAO = "Articulação"
TIPO_ARTIGO = "Artigo"
TIPO_CAPUT = "Caput"
TIPO_EMENTA = "Ementa"
TIPO_ANEXO = "Anexo"
TIPO_TNU = "Texto Não Estruturado"
TIPOS_ORFAOS = {
    "Parágrafo",
    "Inciso",
    "Alinea",
    "Item",
    "Inciso de Item",
    "Alinea de Item",
}

_SEM_CONTEUDO = re.compile(
    r"^\(?\s*(revogad[oa]s?|vetad[oa]s?)\b[^)]*\)?\.?$", re.IGNORECASE
)
_OMISSIS = {"[...]", "[…]", "(...)", "(…)"}


@dataclass
class No:
    pk: int
    pai_id: int | None
    tipo: str
    nivel: int
    ordem: int
    rotulo: str
    texto: str  # texto puro (sem HTML)


@dataclass
class ChunkV2:
    raiz_pk: int
    ordem: int
    parte: int
    partes: int
    texto: str
    metadata: dict = field(default_factory=dict)


@dataclass
class _Linha:
    texto: str
    pai_idx: int | None


def estimar_tokens(texto):
    return math.ceil(len(texto) / CHARS_POR_TOKEN)


def _normalizar(texto):
    return re.sub(r"\s+", " ", texto or "").strip()


def _truncar(texto, limite):
    texto = _normalizar(texto)
    if len(texto) <= limite:
        return texto
    return texto[: limite - 1].rstrip() + "…"


def _sem_conteudo(texto):
    texto = _normalizar(texto)
    return not texto or bool(_SEM_CONTEUDO.match(texto))


class _Arvore:
    def __init__(self, nos):
        self.nos = sorted(nos, key=lambda n: n.ordem)
        self.por_pk = {n.pk: n for n in self.nos}
        self.filhos = defaultdict(list)
        for n in self.nos:
            pai = n.pai_id if n.pai_id in self.por_pk else None
            self.filhos[pai].append(n)

    def pai(self, no):
        return self.por_pk.get(no.pai_id)

    def ancestrais(self, no):
        """Do mais externo para o mais interno."""
        cadeia = []
        pai = self.pai(no)
        while pai is not None:
            cadeia.insert(0, pai)
            pai = self.pai(pai)
        return cadeia

    def caput_texto(self, artigo):
        for f in self.filhos[artigo.pk]:
            if f.tipo == TIPO_CAPUT and _normalizar(f.texto):
                return _normalizar(f.texto)
        return ""

    def linha(self, no):
        """Texto de uma linha do dispositivo, já com o rótulo."""
        if no.tipo == TIPO_ARTIGO:
            corpo = self.caput_texto(no) or _normalizar(no.texto)
        else:
            corpo = _normalizar(no.texto)
        if corpo in _OMISSIS:
            return ""
        return _normalizar(f"{_normalizar(no.rotulo)} {corpo}")


def _unidades(arvore):
    """Dispositivos que originam chunks próprios, na ordem do texto."""
    unidades = []

    def visitar(no, dentro):
        pai = arvore.pai(no)
        nova = False
        if no.tipo == TIPO_EMENTA:
            nova = True
        elif no.tipo == TIPO_ARTIGO:
            nova = True
        elif no.tipo == TIPO_ANEXO:
            nova = not dentro
        elif no.tipo == TIPO_TNU:
            nova = (
                not dentro
                and pai is not None
                and pai.tipo == TIPO_ARTICULACAO
                and len(_normalizar(no.texto).split()) >= TNU_MIN_PALAVRAS
            )
        elif no.tipo in TIPOS_ORFAOS:
            nova = not dentro

        if nova:
            unidades.append(no)
        for f in arvore.filhos[no.pk]:
            visitar(f, dentro or nova)

    for raiz in arvore.filhos[None]:
        visitar(raiz, False)
    return unidades


def _coletar_linhas(arvore, raiz):
    """Linhas do subtree da unidade, sem as unidades de Artigo aninhadas."""
    linhas = []
    textos_crus = []
    ordens = [raiz.ordem]

    def rec(no, pai_idx):
        if no is not raiz and no.tipo == TIPO_ARTIGO:
            return
        if no.tipo == TIPO_CAPUT:
            # o caput já foi mesclado à linha do artigo
            for f in arvore.filhos[no.pk]:
                rec(f, pai_idx)
            return
        ordens.append(no.ordem)
        texto = arvore.linha(no)
        idx = pai_idx
        if texto:
            linhas.append(_Linha(texto, pai_idx))
            idx = len(linhas) - 1
        if no.tipo == TIPO_ARTIGO:
            textos_crus.append(arvore.caput_texto(no) or no.texto)
        else:
            textos_crus.append(no.texto)
        for f in arvore.filhos[no.pk]:
            rec(f, idx)

    rec(raiz, None)
    return linhas, textos_crus, max(ordens)


def _cabecalho(arvore, raiz, titulo_norma, ementa, incluir_ementa):
    cab = [_normalizar(titulo_norma)]
    if incluir_ementa and ementa and raiz.tipo != TIPO_EMENTA:
        cab.append(_truncar(ementa, EMENTA_MAX_CHARS))
    for anc in arvore.ancestrais(raiz):
        if anc.tipo in (TIPO_ARTICULACAO, TIPO_CAPUT):
            continue
        texto = arvore.linha(anc)
        if texto:
            cab.append(_truncar(texto, ANCESTRAL_MAX_CHARS))
    return cab


def _quebrar_texto(texto, max_chars):
    """Janelas de até max_chars (em fronteira de palavra), com sobreposição."""
    palavras = texto.split()
    janelas = []
    i = 0
    while i < len(palavras):
        j = i
        tamanho = 0
        while j < len(palavras) and tamanho + len(palavras[j]) + 1 <= max_chars:
            tamanho += len(palavras[j]) + 1
            j += 1
        j = max(j, i + 1)  # palavra maior que a janela
        janelas.append(" ".join(palavras[i:j]))
        if j >= len(palavras):
            break
        i = max(i + 1, j - max(1, int((j - i) * SOBREPOSICAO_JANELA)))
    return janelas


def _migalhas(linhas, i):
    """Linhas ancestrais (dentro da unidade, exceto a primeira) que governam a linha i."""
    cadeia = []
    p = linhas[i].pai_idx
    while p is not None and p != 0:
        cadeia.insert(0, _truncar(linhas[p].texto, ANCESTRAL_MAX_CHARS))
        p = linhas[p].pai_idx
    return cadeia


def _empacotar(cab, linhas, max_tokens):
    """Divide as linhas em partes que cabem no orçamento. Cada parte é uma lista de textos."""
    cab_tokens = estimar_tokens("\n".join(cab))
    total = cab_tokens + sum(estimar_tokens(l.texto) + 1 for l in linhas)
    if total <= max_tokens:
        return [[l.texto for l in linhas]]

    cabeca = _truncar(linhas[0].texto, CABECALHO_CONTINUACAO_MAX_CHARS)
    partes = []
    i = 0
    while i < len(linhas):
        prefixo = [] if i == 0 else [cabeca] + _migalhas(linhas, i)
        gasto = cab_tokens + sum(estimar_tokens(p) + 1 for p in prefixo)
        grupo = []
        while i < len(linhas):
            custo = estimar_tokens(linhas[i].texto) + 1
            if grupo and gasto + custo > max_tokens:
                break
            if not grupo and gasto + custo > max_tokens:
                # linha maior que o orçamento: janelas com sobreposição
                limite = max(200, int((max_tokens - gasto) * CHARS_POR_TOKEN))
                for janela in _quebrar_texto(linhas[i].texto, limite):
                    partes.append(prefixo + [janela])
                i += 1
                break
            grupo.append(linhas[i].texto)
            gasto += custo
            i += 1
        if grupo:
            partes.append(prefixo + grupo)
    return partes


def construir_chunks(
    nos,
    titulo_norma,
    ementa="",
    max_tokens=MAX_TOKENS,
    incluir_ementa=True,
):
    """Chunks v2 da norma, ordenados por (ordem da unidade, parte)."""
    arvore = _Arvore(nos)
    chunks = []

    for raiz in _unidades(arvore):
        linhas, textos_crus, ordem_fim = _coletar_linhas(arvore, raiz)
        if not linhas:
            continue

        conteudo = _normalizar(" ".join(textos_crus))
        if _sem_conteudo(conteudo):
            continue
        if raiz.tipo == TIPO_ANEXO and len(conteudo.split()) < ANEXO_MIN_PALAVRAS:
            continue

        cab = _cabecalho(arvore, raiz, titulo_norma, ementa, incluir_ementa)
        partes = _empacotar(cab, linhas, max_tokens)

        for numero, corpo in enumerate(partes):
            texto = "\n".join(cab + corpo)
            chunks.append(
                ChunkV2(
                    raiz_pk=raiz.pk,
                    ordem=raiz.ordem,
                    parte=numero,
                    partes=len(partes),
                    texto=texto,
                    metadata={
                        "chunk_strategy": ESTRATEGIA,
                        "tipo": raiz.tipo,
                        "rotulo": _normalizar(raiz.rotulo),
                        "ordem": raiz.ordem,
                        "ordem_fim": ordem_fim,
                        "parte": numero,
                        "partes": len(partes),
                        "caminho": cab[1:],
                        "hash": hashlib.sha1(texto.encode("utf-8")).hexdigest()[:16],
                        "tokens_estimados": estimar_tokens(texto),
                    },
                )
            )
    return chunks
