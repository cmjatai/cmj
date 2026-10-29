import re

from django.contrib.postgres.search import SearchQuery

FTS_CONFIG = "portuguese"
MAX_TERMS = 12

_EDGE_PUNCTUATION = ".,;:!?()[]{}\"'“”‘’«»"
_NUMERO_COM_MILHAR = re.compile(r"^\d{1,3}(\.\d{3})+$")
_NUMERO_PURO = re.compile(r"^[1-9]\d{3,}$")


def extract_terms(text, max_terms=MAX_TERMS):
    """
    Quebra o texto de busca em termos. Cada termo é uma lista de variantes
    equivalentes: o tsvector do PostgreSQL trata "4353" e "4.353" como lexemas
    distintos, então números de lei recebem as duas grafias.
    """
    terms = []
    seen = set()
    for raw in str(text or "").split():
        token = raw.strip(_EDGE_PUNCTUATION)
        key = token.lower()
        if not any(ch.isalnum() for ch in token) or key in seen:
            continue
        if len(key) < 2 and not key.isdigit():
            continue
        seen.add(key)

        variants = [token]
        if _NUMERO_COM_MILHAR.match(token):
            variants.append(token.replace(".", ""))
        elif _NUMERO_PURO.match(token):
            variants.append(f"{int(token):,}".replace(",", "."))

        terms.append(variants)
        if len(terms) >= max_terms:
            break
    return terms


def build_fts_queries(text):
    """
    Retorna (query_and, query_or) para a busca full-text.

    - query_and: todos os termos precisam existir no chunk (alta precisão).
    - query_or: qualquer termo basta (recuperação de reserva quando o AND
      traz poucos resultados). É None quando há um único termo.

    Cada termo é montado com SearchQuery "plain" (plainto_tsquery), que não
    interpreta operadores digitados pelo usuário ou pelo LLM.
    """
    terms = extract_terms(text)
    if not terms:
        return None, None

    term_queries = []
    for variants in terms:
        query = None
        for variant in variants:
            sq = SearchQuery(variant, config=FTS_CONFIG)
            query = sq if query is None else query | sq
        term_queries.append(query)

    query_and = term_queries[0]
    for query in term_queries[1:]:
        query_and = query_and & query

    if len(term_queries) == 1:
        return query_and, None

    query_or = term_queries[0]
    for query in term_queries[1:]:
        query_or = query_or | query

    return query_and, query_or
