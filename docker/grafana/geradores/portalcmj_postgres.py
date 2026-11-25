"""Gera docker/grafana/dashboards/portalcmj-postgres.json.

O JSON é versionado e lido pelo provisioning do Grafana; este script é a fonte.
Para mudar o dashboard, altere aqui e rode:

    python docker/grafana/geradores/portalcmj_postgres.py

Um caminho como argumento grava em outro arquivo.
"""

import json
import sys
from pathlib import Path

SAIDA = Path(__file__).resolve().parents[1] / "dashboards" / "portalcmj-postgres.json"

DS = {"type": "prometheus", "uid": "prometheus"}
DB = 'datname="cmj"'

panels = []
_id = [0]
_y = [0]


def nid():
    _id[0] += 1
    return _id[0]


def row(title):
    panels.append(
        {
            "id": nid(),
            "type": "row",
            "title": title,
            "collapsed": False,
            "gridPos": {"x": 0, "y": _y[0], "w": 24, "h": 1},
            "panels": [],
        }
    )
    _y[0] += 1


def target(expr, legend="", ref="A", instant=False, fmt=None):
    t = {"datasource": DS, "expr": expr, "legendFormat": legend, "refId": ref}
    if instant:
        t["instant"] = True
        t["range"] = False
    if fmt:
        t["format"] = fmt
    return t


def panel(kind, title, x, w, h, targets, unit=None, desc=None, options=None, **extra):
    p = {
        "id": nid(),
        "type": kind,
        "title": title,
        "datasource": DS,
        "gridPos": {"x": x, "y": _y[0], "w": w, "h": h},
        "targets": targets,
        "fieldConfig": {"defaults": {}, "overrides": []},
        "options": options or {},
    }
    if unit:
        p["fieldConfig"]["defaults"]["unit"] = unit
    if desc:
        p["description"] = desc
    p.update(extra)
    panels.append(p)
    return p


def ts(title, x, w, targets, unit=None, desc=None, h=8):
    return panel(
        "timeseries",
        title,
        x,
        w,
        h,
        targets,
        unit,
        desc,
        options={
            "legend": {
                "displayMode": "list",
                "placement": "bottom",
                "showLegend": True,
            },
            "tooltip": {"mode": "multi", "sort": "desc"},
        },
    )


def stat(title, x, w, expr, unit=None, desc=None, thresholds=None, decimals=None):
    p = panel(
        "stat",
        title,
        x,
        w,
        4,
        [target(expr, instant=True)],
        unit,
        desc,
        options={
            "reduceOptions": {"calcs": ["lastNotNull"], "fields": "", "values": False},
            "colorMode": "value",
            "graphMode": "none",
            "textMode": "value",
        },
    )
    if thresholds:
        p["fieldConfig"]["defaults"]["thresholds"] = {
            "mode": "absolute",
            "steps": thresholds,
        }
    if decimals is not None:
        p["fieldConfig"]["defaults"]["decimals"] = decimals
    return p


def nextrow(h):
    _y[0] += h


def table(title, w, h, targets, renames, units, desc=None, sort=None, hide=()):
    """Tabela de consultas instantâneas juntadas pelos rótulos em comum."""
    overrides = [
        {
            "matcher": {"id": "byName", "options": col},
            "properties": [{"id": "unit", "value": unit}],
        }
        for col, unit in units.items()
    ]
    for col, width in (("Consulta", 900),):
        overrides.append(
            {
                "matcher": {"id": "byName", "options": col},
                "properties": [{"id": "custom.width", "value": width}],
            }
        )
    excl = {
        c: True
        for c in ("Time", "__name__", "instance", "job", "datname") + tuple(hide)
    }
    p = panel(
        "table",
        title,
        0,
        w,
        h,
        targets,
        desc=desc,
        options={
            "showHeader": True,
            "cellHeight": "sm",
            "sortBy": [{"displayName": sort, "desc": True}] if sort else [],
        },
        transformations=[
            {"id": "merge", "options": {}},
            {
                "id": "organize",
                "options": {"excludeByName": excl, "renameByName": renames},
            },
        ],
    )
    p["fieldConfig"]["defaults"]["custom"] = {"filterable": True}
    p["fieldConfig"]["overrides"] = overrides
    return p


# ---------------------------------------------------------------- Saúde
row("Saúde")
stat(
    "Postgres",
    0,
    3,
    "pg_up",
    desc="1: o exporter consegue consultar o banco.",
    thresholds=[{"color": "red", "value": None}, {"color": "green", "value": 1}],
)
panels[-1]["fieldConfig"]["defaults"]["mappings"] = [
    {"type": "value", "options": {"0": {"text": "fora"}, "1": {"text": "no ar"}}}
]
stat(
    "No ar há",
    3,
    3,
    "time() - pg_postmaster_start_time_seconds",
    unit="s",
    desc="Tempo desde o último início do Postgres.",
)
stat("Tamanho do banco", 6, 3, f"pg_database_size_bytes{{{DB}}}", unit="bytes")
stat(
    "Conexões em uso",
    9,
    3,
    "sum(pg_stat_activity_count) / max(pg_settings_max_connections)",
    unit="percentunit",
    desc="Mesma conta do alerta Conexões do Postgres (dispara acima de 80%).",
    thresholds=[
        {"color": "green", "value": None},
        {"color": "orange", "value": 0.6},
        {"color": "red", "value": 0.8},
    ],
)
stat(
    "Cache hit (janela)",
    12,
    3,
    f"sum(increase(pg_stat_database_blks_hit{{{DB}}}[$__range])) / "
    f"(sum(increase(pg_stat_database_blks_hit{{{DB}}}[$__range])) + "
    f"sum(increase(pg_stat_database_blks_read{{{DB}}}[$__range])))",
    unit="percentunit",
    desc="Blocos achados no shared_buffers sobre o total de blocos lidos, no intervalo do dashboard.",
    thresholds=[
        {"color": "red", "value": None},
        {"color": "orange", "value": 0.9},
        {"color": "green", "value": 0.98},
    ],
    decimals=2,
)
stat(
    "Deadlocks (janela)",
    15,
    3,
    f"sum(increase(pg_stat_database_deadlocks{{{DB}}}[$__range]))",
    thresholds=[{"color": "green", "value": None}, {"color": "red", "value": 1}],
    decimals=0,
)
stat(
    "Transação mais longa",
    18,
    3,
    f"max(pg_stat_activity_max_tx_duration{{{DB}}})",
    unit="s",
    desc="Duração da transação aberta há mais tempo, em qualquer estado.",
    thresholds=[
        {"color": "green", "value": None},
        {"color": "orange", "value": 300},
        {"color": "red", "value": 1800},
    ],
)
stat(
    "Idade do datfrozenxid",
    21,
    3,
    f"max(pg_database_wraparound_age_datfrozenxid{{{DB}}})",
    unit="short",
    desc=(
        "Transações desde o último congelamento completo do banco (wraparound). "
        "O autovacuum age a partir de autovacuum_freeze_max_age (200 milhões); "
        "o alerta dispara acima de 1 bilhão."
    ),
    thresholds=[
        {"color": "green", "value": None},
        {"color": "orange", "value": 500_000_000},
        {"color": "red", "value": 1_000_000_000},
    ],
)
nextrow(4)

# ---------------------------------------------------------------- Atividade
row("Atividade")
ts(
    "Conexões por estado",
    0,
    8,
    [target(f"sum by (state) (pg_stat_activity_count{{{DB}}}) > 0", "{{state}}")],
)
ts(
    "Transação mais longa por estado",
    8,
    8,
    [target(f"pg_stat_activity_max_tx_duration{{{DB}}} > 0", "{{state}}")],
    unit="s",
    desc="idle in transaction alto aponta conexão que abriu transação e não fechou.",
)
ts(
    "Locks por modo",
    16,
    8,
    [target(f"sum by (mode) (pg_locks_count{{{DB}}}) > 0", "{{mode}}")],
)
nextrow(8)
ts(
    "Transações por segundo",
    0,
    8,
    [
        target(f"sum(rate(pg_stat_database_xact_commit{{{DB}}}[5m]))", "commit"),
        target(
            f"sum(rate(pg_stat_database_xact_rollback{{{DB}}}[5m]))", "rollback", "B"
        ),
    ],
    unit="ops",
)
ts(
    "Tuplas por segundo",
    8,
    8,
    [
        target(
            f"sum(rate(pg_stat_database_tup_fetched{{{DB}}}[5m]))", "lidas (fetched)"
        ),
        target(
            f"sum(rate(pg_stat_database_tup_inserted{{{DB}}}[5m]))", "inseridas", "B"
        ),
        target(
            f"sum(rate(pg_stat_database_tup_updated{{{DB}}}[5m]))", "atualizadas", "C"
        ),
        target(f"sum(rate(pg_stat_database_tup_deleted{{{DB}}}[5m]))", "apagadas", "D"),
    ],
    unit="ops",
)
ts(
    "Arquivos temporários",
    16,
    8,
    [target(f"sum(rate(pg_stat_database_temp_bytes{{{DB}}}[5m]))", "bytes/s")],
    unit="Bps",
    desc="Ordenações e hashes que não couberam no work_mem e foram para o disco.",
)
nextrow(8)

# ---------------------------------------------------------------- Consultas
row("Consultas (pg_stat_statements)")
SEC = f"pg_stat_statements_seconds_total{{{DB}}}"
CALLS = f"pg_stat_statements_calls_total{{{DB}}}"
ROWS = f"pg_stat_statements_rows_total{{{DB}}}"
TOP = f"topk(20, sum by (queryid) (increase({SEC}[$__range])))"
TXT = "max by (queryid, query) (pg_stat_statements_query_id)"


def com_texto(expr):
    return f"({expr}) * on (queryid) group_left (query) {TXT}"


def no_top(expr):
    return com_texto(
        f"sum by (queryid) (increase({expr}[$__range])) and on (queryid) {TOP}"
    )


table(
    "Consultas que mais consumiram tempo no intervalo",
    24,
    12,
    [
        target(com_texto(TOP), ref="A", instant=True, fmt="table"),
        target(no_top(CALLS), ref="B", instant=True, fmt="table"),
        target(
            com_texto(
                f"(sum by (queryid) (increase({SEC}[$__range])) / "
                f"sum by (queryid) (increase({CALLS}[$__range]))) and on (queryid) {TOP}"
            ),
            ref="C",
            instant=True,
            fmt="table",
        ),
        target(no_top(ROWS), ref="D", instant=True, fmt="table"),
    ],
    renames={
        "query": "Consulta",
        "Value #A": "Tempo total",
        "Value #B": "Chamadas",
        "Value #C": "Tempo médio",
        "Value #D": "Linhas",
    },
    units={
        "Tempo total": "s",
        "Tempo médio": "s",
        "Chamadas": "short",
        "Linhas": "short",
    },
    desc=(
        "Top 20 por tempo de execução somado no intervalo do dashboard. O texto vem "
        "normalizado pelo pg_stat_statements (constantes viram $1) e cortado em 300 "
        "caracteres. O exporter só envia as 100 consultas de maior tempo acumulado."
    ),
    sort="Tempo total",
)
nextrow(12)
ts(
    "Tempo de execução por consulta (top 10)",
    0,
    12,
    [
        target(
            f"topk(10, sum by (queryid) (rate({SEC}[5m])))",
            "{{queryid}}",
        )
    ],
    unit="percentunit",
    desc=(
        "Segundos de execução por segundo (1 = um backend ocupado o tempo todo). "
        "A legenda é o queryid: o texto está na tabela acima."
    ),
)
ts(
    "Tempo de I/O de bloco das consultas",
    12,
    12,
    [
        target(
            f"sum(rate(pg_stat_statements_block_read_seconds_total{{{DB}}}[5m]))",
            "leitura",
        ),
        target(
            f"sum(rate(pg_stat_statements_block_write_seconds_total{{{DB}}}[5m]))",
            "escrita",
            "B",
        ),
    ],
    unit="percentunit",
    desc="Depende de track_io_timing=on no Postgres; sem ele, fica em zero.",
)
nextrow(8)

# ---------------------------------------------------------------- Tabelas
row("Tabelas e índices")
REL = "(schemaname, relname)"
TOPT = (
    f"topk(25, pg_stat_user_tables_table_size_bytes{{{DB}}} "
    f"+ on {REL} pg_stat_user_tables_index_size_bytes{{{DB}}})"
)


def na_top(expr):
    return f"sum by {REL} (({expr}) and on {REL} {TOPT})"


table(
    "Maiores tabelas",
    24,
    12,
    [
        target(TOPT, ref="A", instant=True, fmt="table"),
        target(
            na_top(f"pg_stat_user_tables_table_size_bytes{{{DB}}}"),
            ref="B",
            instant=True,
            fmt="table",
        ),
        target(
            na_top(f"pg_stat_user_tables_index_size_bytes{{{DB}}}"),
            ref="C",
            instant=True,
            fmt="table",
        ),
        target(
            na_top(f"pg_stat_user_tables_n_live_tup{{{DB}}}"),
            ref="D",
            instant=True,
            fmt="table",
        ),
        target(
            na_top(f"pg_stat_user_tables_n_dead_tup{{{DB}}}"),
            ref="E",
            instant=True,
            fmt="table",
        ),
        target(
            na_top(f"increase(pg_stat_user_tables_seq_scan{{{DB}}}[$__range])"),
            ref="F",
            instant=True,
            fmt="table",
        ),
        target(
            na_top(f"increase(pg_stat_user_tables_idx_scan{{{DB}}}[$__range])"),
            ref="G",
            instant=True,
            fmt="table",
        ),
        target(
            na_top(f"time() - (pg_stat_user_tables_last_autovacuum{{{DB}}} > 0)"),
            ref="H",
            instant=True,
            fmt="table",
        ),
        target(
            na_top(f"time() - (pg_stat_user_tables_last_autoanalyze{{{DB}}} > 0)"),
            ref="I",
            instant=True,
            fmt="table",
        ),
    ],
    renames={
        "schemaname": "Esquema",
        "relname": "Tabela",
        "Value #A": "Total",
        "Value #B": "Dados",
        "Value #C": "Índices",
        "Value #D": "Linhas vivas",
        "Value #E": "Linhas mortas",
        "Value #F": "Seq scans (janela)",
        "Value #G": "Index scans (janela)",
        "Value #H": "Último autovacuum há",
        "Value #I": "Último autoanalyze há",
    },
    units={
        "Total": "bytes",
        "Dados": "bytes",
        "Índices": "bytes",
        "Linhas vivas": "short",
        "Linhas mortas": "short",
        "Seq scans (janela)": "short",
        "Index scans (janela)": "short",
        "Último autovacuum há": "s",
        "Último autoanalyze há": "s",
    },
    desc=(
        "As 25 maiores tabelas (dados + índices). Seq scans altos numa tabela grande "
        "costumam indicar índice faltando. Linhas mortas altas e autovacuum antigo "
        "indicam vacuum atrasado. Vazio: a tabela nunca passou pelo autovacuum."
    ),
    sort="Total",
)
nextrow(12)
ts(
    "Linhas lidas por seq scan (top 10)",
    0,
    8,
    [
        target(
            f"topk(10, rate(pg_stat_user_tables_seq_tup_read{{{DB}}}[5m]))",
            "{{relname}}",
        )
    ],
    unit="ops",
)
ts(
    "Linhas mortas (top 10)",
    8,
    8,
    [target(f"topk(10, pg_stat_user_tables_n_dead_tup{{{DB}}})", "{{relname}}")],
    unit="short",
)
ts(
    "Blocos de índice lidos do disco (top 10)",
    16,
    8,
    [
        target(
            "topk(10, rate(pg_statio_user_indexes_idx_blks_read_total[5m]))",
            "{{indexrelname}}",
        )
    ],
    unit="ops",
    desc="Índices que não cabem no cache. Índices HNSW do pgvector costumam aparecer aqui.",
)
nextrow(8)
ts(
    "Autovacuum em andamento",
    0,
    12,
    [
        target(
            "time() - pg_stat_activity_autovacuum_timestamp_seconds",
            "{{relname}}",
        )
    ],
    unit="s",
    desc="Há quanto tempo cada worker de autovacuum está na tabela.",
)
ts(
    "Tempo de I/O do banco",
    12,
    12,
    [
        target(
            f"sum(rate(pg_stat_database_blk_read_time{{{DB}}}[5m])) / 1000", "leitura"
        ),
        target(
            f"sum(rate(pg_stat_database_blk_write_time{{{DB}}}[5m])) / 1000",
            "escrita",
            "B",
        ),
    ],
    unit="percentunit",
    desc="Segundos gastos em leitura e escrita de blocos por segundo. Depende de track_io_timing=on.",
)
nextrow(8)

# ---------------------------------------------------------------- Checkpoints
row("Checkpoints, buffers e WAL")
ts(
    "Checkpoints",
    0,
    8,
    [
        target(
            "increase(pg_stat_checkpointer_num_timed_total[$__rate_interval])",
            "por tempo",
        ),
        target(
            "increase(pg_stat_checkpointer_num_requested_total[$__rate_interval])",
            "solicitados",
            "B",
        ),
    ],
    unit="short",
    desc="Muitos checkpoints solicitados indicam max_wal_size pequeno para a carga de escrita.",
)
ts(
    "Buffers escritos e alocados",
    8,
    8,
    [
        target("rate(pg_stat_checkpointer_buffers_written_total[5m])", "checkpointer"),
        target("rate(pg_stat_bgwriter_buffers_clean_total[5m])", "bgwriter", "B"),
        target("rate(pg_stat_bgwriter_buffers_alloc_total[5m])", "alocados", "C"),
    ],
    unit="ops",
)
ts(
    "Tamanho do WAL",
    16,
    8,
    [target("pg_wal_size_bytes", "WAL")],
    unit="bytes",
)
nextrow(8)

dash = {
    "uid": "portalcmj-postgres",
    "title": "PortalCMJ – Postgres",
    "tags": ["portalcmj", "postgres"],
    "timezone": "browser",
    "schemaVersion": 39,
    "time": {"from": "now-6h", "to": "now"},
    "refresh": "1m",
    "editable": True,
    "templating": {"list": []},
    "annotations": {"list": []},
    "panels": panels,
}
saida = Path(sys.argv[1]) if len(sys.argv) > 1 else SAIDA
saida.write_text(
    json.dumps(dash, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
)
print(saida)
