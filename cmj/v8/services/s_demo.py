"""Dados e validações da demonstração do v8.

Os clientes são fictícios e existem só na memória do processo. Nada é gravado:
criar, editar e arquivar validam a entrada e respondem como se tivessem
gravado, e a lista continua a mesma.
"""

import copy
import math
import unicodedata
from datetime import date, timedelta
from decimal import Decimal

from django import forms

TOTAL_CLIENTES = 42
TAMANHO_PADRAO = 10
TAMANHO_MAXIMO = 50
TAMANHO_MAXIMO_BUSCA = 100
DOMINIO_EMAIL = "exemplo.invalid"

SITUACOES = (("ativo", "Ativo"), ("inativo", "Inativo"))

_NOMES = ("Ana", "Bento", "Clara", "Davi", "Elisa", "Fábio", "Glória")
_SOBRENOMES = ("Exemplo", "Modelo", "Amostra", "Teste", "Ensaio", "Protótipo")
_CIDADES = ("Caiapônia", "Jataí", "Mineiros", "Rio Verde", "Serranópolis")
_MOTIVOS = (
    "Cadastro duplicado",
    "Pedido do próprio cliente",
    "Sem movimento há mais de um ano",
)
_PRODUTOS = (
    "Caderno de anotações",
    "Caixa de canetas",
    "Pasta arquivo",
    "Resma de papel",
    "Etiquetas adesivas",
    "Grampeador",
)
_INICIO = date(2021, 1, 4)

# Páginas de demonstração dos layouts (docs/specs/v8/templates.md). Só texto
# fixo: o nome do layout, um resumo e o que cada block recebe.
LAYOUTS_DEMO = (
    {
        "nome": "landing",
        "resumo": "Capa: menu na horizontal, hero de largura total e rodapé.",
        "regioes": (
            ("header_nav", "Menu principal, na horizontal"),
            ("hero", "Vazio no layout. Esta página o preenche"),
            ("content", "Conteúdo centralizado, com largura máxima"),
            ("footer", "Marca e uma linha de texto"),
            ("footer_nav, footer_info", "Vazios no layout. Esta página os preenche"),
        ),
    },
    {
        "nome": "app_topbar",
        "resumo": "Navegação superior: menu na horizontal e conteúdo centralizado.",
        "regioes": (
            ("header_start", "Botão que abre o menu em tela estreita"),
            ("header_nav", "Menu principal, na horizontal"),
            ("breadcrumbs", "Trilha informada pela view"),
            ("content", "Conteúdo centralizado, com largura máxima"),
        ),
    },
    {
        "nome": "app_sidebar",
        "resumo": "Operacional: barra lateral à esquerda e área de trabalho fluida.",
        "regioes": (
            ("header_start", "Botão que recolhe a barra lateral"),
            ("aside", "Barra lateral com o menu principal"),
            ("breadcrumbs", "Trilha informada pela view"),
            ("content", "Área de trabalho, com toda a largura que sobra"),
        ),
    },
    {
        "nome": "minimal",
        "resumo": "Foco: sem cabeçalho, menu, barra lateral nem rodapé.",
        "regioes": (
            ("messages", "Mensagens do Django, para quem está sem JavaScript"),
            ("content", "Conteúdo centralizado na tela"),
        ),
    },
)


def _sem_acento(texto):
    normal = unicodedata.normalize("NFKD", str(texto))
    return "".join(c for c in normal if not unicodedata.combining(c)).casefold()


def _gerar_pedidos(indice, desde):
    pedidos = []
    for j in range(1 + indice % 4):
        centavos = 1990 + ((indice * 37 + j * 113) % 900) * 105
        pedidos.append(
            {
                "id": (indice + 1) * 100 + j + 1,
                "descricao": _PRODUTOS[(indice + j) % len(_PRODUTOS)],
                "valor": f"{Decimal(centavos) / 100:.2f}",
                "data": (desde + timedelta(days=30 * (j + 1))).isoformat(),
            }
        )
    return pedidos


def _gerar_clientes():
    """Monta a lista fixa. O resultado é o mesmo a cada execução."""
    clientes = []
    for i in range(TOTAL_CLIENTES):
        nome = f"{_NOMES[i % len(_NOMES)]} {_SOBRENOMES[i // len(_NOMES)]}"
        inativo = i % 5 == 3
        desde = _INICIO + timedelta(days=i * 41)
        clientes.append(
            {
                "id": i + 1,
                "nome": nome,
                "email": f"{_sem_acento(nome).replace(' ', '.')}@{DOMINIO_EMAIL}",
                "cidade": _CIDADES[(i * 2 + i // 5) % len(_CIDADES)],
                "situacao": "inativo" if inativo else "ativo",
                "motivo": _MOTIVOS[i % len(_MOTIVOS)] if inativo else "",
                "desde": desde.isoformat(),
                "pedidos": _gerar_pedidos(i, desde),
            }
        )
    return tuple(clientes)


_CLIENTES = _gerar_clientes()
_POR_ID = {cliente["id"]: cliente for cliente in _CLIENTES}


class ClienteForm(forms.Form):
    """Validação de cliente. ``cliente_id`` é o cliente em edição, se houver."""

    nome = forms.CharField(
        max_length=80,
        error_messages={"required": "Informe o nome."},
    )
    email = forms.EmailField(
        max_length=120,
        error_messages={
            "required": "Informe o e-mail.",
            "invalid": "Informe um e-mail válido.",
        },
    )
    cidade = forms.CharField(
        max_length=60,
        error_messages={"required": "Informe a cidade."},
    )
    situacao = forms.ChoiceField(
        choices=SITUACOES,
        error_messages={
            "required": "Informe a situação.",
            "invalid_choice": "Situação inválida.",
        },
    )
    motivo = forms.CharField(max_length=200, required=False)

    def __init__(self, *args, cliente_id=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.cliente_id = cliente_id

    def clean_nome(self):
        nome = self.cleaned_data["nome"].strip()
        if sum(1 for c in nome if c.isalpha()) < 3:
            raise forms.ValidationError("O nome precisa ter ao menos três letras.")
        return nome

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        for cliente in _CLIENTES:
            if cliente["email"] == email and cliente["id"] != self.cliente_id:
                raise forms.ValidationError("Este e-mail já é usado por outro cliente.")
        return email

    def clean(self):
        dados = super().clean()
        if dados.get("situacao") == "inativo" and not dados.get("motivo", "").strip():
            raise forms.ValidationError(
                "Cliente inativo precisa de um motivo preenchido."
            )
        return dados


def cidades():
    """Cidades presentes na lista, em ordem alfabética."""
    return list(_CIDADES)


def normalizar_filtros(q="", situacao="", cidade=""):
    """Reduz os filtros aos valores aceitos. O que não for reconhecido é ignorado."""
    q = str(q or "").strip()[:TAMANHO_MAXIMO_BUSCA]
    situacao = situacao if situacao in dict(SITUACOES) else ""
    cidade_pedida = _sem_acento(str(cidade or "").strip())
    cidade = next((c for c in _CIDADES if _sem_acento(c) == cidade_pedida), "")
    return {"q": q, "situacao": situacao, "cidade": cidade}


def _resumo(cliente):
    resumo = {chave: valor for chave, valor in cliente.items() if chave != "pedidos"}
    resumo["total_pedidos"] = len(cliente["pedidos"])
    return resumo


def listar(q="", situacao="", cidade="", pagina=1, tamanho=TAMANHO_PADRAO):
    """Página da lista de clientes, filtrada por busca, situação e cidade.

    A busca vale para nome e e-mail, sem diferenciar maiúsculas nem acentos. O
    tamanho da página fica entre 1 e ``TAMANHO_MAXIMO``, e a página pedida é
    trazida para o intervalo existente.
    """
    filtros = normalizar_filtros(q, situacao, cidade)
    busca = _sem_acento(filtros["q"])
    encontrados = [
        cliente
        for cliente in _CLIENTES
        if (not filtros["situacao"] or cliente["situacao"] == filtros["situacao"])
        and (not filtros["cidade"] or cliente["cidade"] == filtros["cidade"])
        and (
            not busca
            or busca in _sem_acento(cliente["nome"])
            or busca in cliente["email"]
        )
    ]
    tamanho = min(max(int(tamanho), 1), TAMANHO_MAXIMO)
    total = len(encontrados)
    paginas = max(1, math.ceil(total / tamanho))
    pagina = min(max(int(pagina), 1), paginas)
    inicio = (pagina - 1) * tamanho
    return {
        "total": total,
        "pagina": pagina,
        "paginas": paginas,
        "tamanho": tamanho,
        "itens": [_resumo(c) for c in encontrados[inicio : inicio + tamanho]],
    }


def obter(pk):
    """Cópia do cliente com seus pedidos, ou ``None`` se o id não existe."""
    cliente = _POR_ID.get(pk)
    return copy.deepcopy(cliente) if cliente else None


def validar(dados, pk=None):
    """Valida os dados de um cliente novo ou, com ``pk``, de um existente.

    Devolve ``(cliente, form)``. Com erro, ``cliente`` é ``None`` e ``form``
    traz os erros. Sem erro, ``cliente`` é o registro como ficaria gravado.
    """
    atual = None
    if pk is not None:
        atual = obter(pk)
        if atual is None:
            raise LookupError(f"Cliente {pk} não existe.")
    form = ClienteForm(dados if isinstance(dados, dict) else {}, cliente_id=pk)
    if not form.is_valid():
        return None, form
    cliente = atual or {
        "id": max(_POR_ID) + 1,
        "desde": date.today().isoformat(),
        "pedidos": [],
    }
    cliente.update(form.cleaned_data)
    ordem = ("id", "nome", "email", "cidade", "situacao", "motivo", "desde", "pedidos")
    return {chave: cliente[chave] for chave in ordem}, form


def arquivar(ids):
    """Conta os ids recebidos que são de clientes existentes. Nada é alterado."""
    validos = set()
    for bruto in ids or ():
        try:
            pk = int(bruto)
        except (TypeError, ValueError):
            continue
        if pk in _POR_ID:
            validos.add(pk)
    return len(validos)


def historico(pk):
    """Eventos do cliente, do mais antigo ao mais recente. ``None`` se não existe."""
    cliente = _POR_ID.get(pk)
    if cliente is None:
        return None
    eventos = [{"data": cliente["desde"], "texto": "Cadastro criado."}]
    for pedido in cliente["pedidos"]:
        eventos.append(
            {
                "data": pedido["data"],
                "texto": f"Pedido {pedido['id']} registrado: {pedido['descricao']}.",
            }
        )
    if cliente["situacao"] == "inativo":
        ultima = date.fromisoformat(eventos[-1]["data"]) + timedelta(days=15)
        eventos.append(
            {
                "data": ultima.isoformat(),
                "texto": f"Cliente inativado. Motivo: {cliente['motivo']}.",
            }
        )
    return eventos


def layouts_demo():
    """As páginas de demonstração dos layouts, cada uma com a própria URL."""
    return [
        {**copy.deepcopy(layout), "url": f"/v8/demo/layouts/{layout['nome']}/"}
        for layout in LAYOUTS_DEMO
    ]


def layout_demo(nome):
    """Dados da página de demonstração de um layout, ou ``None``."""
    for layout in layouts_demo():
        if layout["nome"] == nome:
            return layout
    return None
