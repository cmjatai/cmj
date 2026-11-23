"""Design system do v8: as seções da vitrine, os temas e os dados de amostra.

Tudo aqui é fixo e fictício (docs/specs/v8/ds.md), escrito neste módulo: a
vitrine só mostra como o padrão visual está.
"""

from dataclasses import dataclass

from django.urls import reverse

from cmj.v8.services import s_global

PASTA_SECOES = "v8/partials/ds/"

# A vitrine e as prévias são públicas (ds.md, D1). Escolher o tema do navegador
# exige isto (temas.md, D9).
EXIGE_USAR_TEMA = s_global.SUPERUSUARIO


def pode_usar_tema(usuario):
    """Diz se o usuário vê e usa o botão "Usar este tema"."""
    return s_global.atende(usuario, EXIGE_USAR_TEMA)


@dataclass(frozen=True)
class Secao:
    """Seção da vitrine: âncora ``ds-<id>``, rótulo do índice e parcial."""

    id: str
    rotulo: str

    @property
    def ancora(self):
        return f"ds-{self.id}"

    @property
    def parcial(self):
        return f"{PASTA_SECOES}{self.id}.html"


# Ordem do índice e da página. A parcial de cada seção sai só deste registro.
SECOES = (
    Secao("cores", "Cores"),
    Secao("tokens", "Fontes, raios e sombras"),
    Secao("texto", "Títulos e texto"),
    Secao("listas", "Listas"),
    Secao("tabelas", "Tabelas"),
    Secao("formularios", "Formulários"),
    Secao("botoes", "Botões"),
    Secao("avisos", "Alertas e etiquetas"),
    Secao("blocos", "Cartão, dados e paginação"),
    Secao("icones", "Ícones"),
    Secao("drawers", "Drawers"),
    Secao("overlays", "Modals e toasts"),
    Secao("componentes", "Componentes base"),
    Secao("campos", "Campos"),
    Secao("estrutura", "Navegação e estrutura"),
    Secao("datas", "Datas e horas"),
    Secao("seletores-cor", "Seletores de cor"),
)

# Símbolos do sprite ``v8/shell/icones.html``, na ordem dele.
ICONES = (
    "menu",
    "sol",
    "lua",
    "casa",
    "grade",
    "usuario",
    "sair",
    "entrar",
    "seta",
    "filtro",
    "fechar",
    "historico",
    "paleta",
)

# Dados de amostra: nomes inventados e e-mails no domínio reservado ``.invalid``.
_PESSOAS = (
    ("Ana Lima", "ana.lima@exemplo.invalid", "Centro", "ativo", "12/03/2026"),
    ("Bruno Costa", "bruno.costa@exemplo.invalid", "Vila Nova", "ativo", "02/05/2026"),
    ("Carla Dias", "carla.dias@exemplo.invalid", "Jardim Sul", "inativo", "18/07/2026"),
    ("Davi Rocha", "davi.rocha@exemplo.invalid", "Centro", "ativo", "30/09/2026"),
)


def amostras():
    """Dados fixos que as seções da vitrine mostram."""
    return {
        "pessoas": [
            {
                "nome": nome,
                "email": email,
                "bairro": bairro,
                "situacao": situacao,
                "data": data,
            }
            for nome, email, bairro, situacao, data in _PESSOAS
        ],
        "opcoes": ["Centro", "Vila Nova", "Jardim Sul", "Setor Norte"],
        "paginas": [1, 2, 3, 4, 5],
        "pagina_atual": 2,
        "icones": list(ICONES),
    }


def temas(em_vigor):
    """Os temas do registro, na ordem dele, com as URLs e a marca do que vale."""
    return [
        {
            "nome": nome,
            "rotulo": rotulo,
            "em_vigor": nome == em_vigor,
            "url_previa": reverse(f"cmj.v8:ds_tema_{nome}"),
            "url_usar": reverse(f"cmj.v8:ds_tema_usar_{nome}"),
        }
        for nome, rotulo in s_global.TEMAS.items()
    ]


def tema(nome, em_vigor):
    """Um tema do registro, como em ``temas``. Nome fora do registro é erro."""
    return next(item for item in temas(em_vigor) if item["nome"] == nome)
