"""Template tags do v8.

As tags calculam o que faltar no contexto, de modo que um template que estende
um layout do v8 renderiza só com o que os context processors fornecem. Os
dados e as decisões vêm de ``cmj/v8/services``.
"""

import itertools
from datetime import date

from django import template
from django.contrib.auth.models import AnonymousUser
from django.utils.html import format_html, json_script

from cmj.v8.services import s_global, s_menu, s_portal

register = template.Library()

ID_DADOS_GLOBAIS = "v8-global"
ID_MENSAGENS = "v8-messages"
PREFIXO_ID_ILHA = "v8-island"

_CHAVE_CONTADOR_ILHAS = "v8_contador_ilhas"

# Nível da mensagem do Django para o modificador de ``v8-alerta``.
_ALERTAS = {
    "success": "sucesso",
    "warning": "aviso",
    "error": "erro",
}


def _usuario(context):
    usuario = context.get("user")
    if usuario is None:
        usuario = getattr(context.get("request"), "user", None)
    return usuario if usuario is not None else AnonymousUser()


def _dados_v8(context):
    """Dados de layout que a view informa em ``v8``. Ausente, um dict vazio."""
    dados = context.get("v8")
    return dados if isinstance(dados, dict) else {}


def _preferencias(context):
    return s_global.preferencias(
        getattr(context.get("request"), "COOKIES", None),
        tema=_dados_v8(context).get("tema"),
    )


@register.simple_tag(takes_context=True)
def v8_preferencias(context):
    """Tema, modo e sidebar, só com valores da lista válida.

    O tema é o que a view fixa em ``v8.tema`` (prévia), senão o do cookie.
    """
    return _preferencias(context)


@register.simple_tag(takes_context=True)
def v8_usuario(context):
    """Dados de exibição do usuário (``None`` para anônimo)."""
    return s_global.dados_usuario(_usuario(context))


@register.simple_tag(takes_context=True)
def v8_dados_globais(context):
    """Emite ``<script id="v8-global" type="application/json">``."""
    dados = s_global.dados_globais(
        _usuario(context),
        zona=_dados_v8(context).get("zona"),
        preferencias=_preferencias(context),
    )
    return json_script(dados, ID_DADOS_GLOBAIS)


@register.simple_tag(takes_context=True)
def v8_mensagens(context):
    """Emite ``<script id="v8-messages" type="application/json">``."""
    mensagens = [
        {"nivel": mensagem.level_tag, "texto": str(mensagem)}
        for mensagem in context.get("messages") or ()
    ]
    return json_script(mensagens, ID_MENSAGENS)


@register.simple_tag
def v8_menu_versao():
    """Versão do menu, para a chave de cache."""
    return s_menu.VERSAO_MENU


@register.simple_tag(takes_context=True)
def v8_menu_chave(context):
    """Resumo das permissões do usuário, para a chave de cache do menu."""
    return s_global.hash_permissoes(_usuario(context))


@register.simple_tag(takes_context=True)
def v8_menu(context):
    """Árvore do menu visível ao usuário, com o item ativo de ``v8.menu_ativo``."""
    return s_menu.menu_para(_usuario(context), _dados_v8(context).get("menu_ativo"))


@register.filter
def v8_alerta(nivel):
    """Modificador de ``v8-alerta`` para o nível de uma mensagem do Django."""
    return _ALERTAS.get(nivel, "info")


@register.filter
def v8_data(valor):
    """Data ISO (``AAAA-MM-DD``) no formato ``DD/MM/AAAA``."""
    try:
        return date.fromisoformat(str(valor)).strftime("%d/%m/%Y")
    except ValueError:
        return valor


def _proximo_id_ilha(context):
    """Id único na renderização da página para o JSON de props de uma ilha.

    O contador fica no escopo do template mais externo do ``render_context``.
    Cada ``{% include %}` abre um escopo próprio, que não serviria: ilhas em
    includes diferentes repetiriam o id.

    ``v8_ilha_prefixo``, informado pelas views de fragmento, diferencia os ids
    de um fragmento dos da página em que ele é inserido.
    """
    escopos = context.render_context.dicts
    contador = next(
        (e[_CHAVE_CONTADOR_ILHAS] for e in escopos if _CHAVE_CONTADOR_ILHAS in e),
        None,
    )
    if contador is None:
        contador = itertools.count(1)
        escopo = escopos[1] if len(escopos) > 1 else escopos[-1]
        escopo[_CHAVE_CONTADOR_ILHAS] = contador
    prefixo = context.get("v8_ilha_prefixo")
    partes = [PREFIXO_ID_ILHA] + ([str(prefixo)] if prefixo else [])
    return "-".join(partes + [str(next(contador))])


class IlhaNode(template.Node):
    def __init__(self, nome, props, nodelist):
        self.nome = nome
        self.props = props
        self.nodelist = nodelist

    def render(self, context):
        nome = self.nome.resolve(context)
        props = (
            self.props.resolve(context, ignore_failures=True)
            if self.props is not None
            else None
        )
        if props is None:
            return format_html(
                '<div data-vue-island="{}">{}</div>',
                nome,
                self.nodelist.render(context),
            )
        id_props = _proximo_id_ilha(context)
        return format_html(
            '{}<div data-vue-island="{}" data-props-id="{}">{}</div>',
            json_script(props, id_props),
            nome,
            id_props,
            self.nodelist.render(context),
        )


@register.tag("v8_island")
def v8_island(parser, token):
    """``{% v8_island "nome" props %}...{% endv8_island %}``

    Emite o elemento da ilha com o conteúdo do bloco como HTML de espera. Com
    ``props``, emite antes o ``json_script`` delas e o aponta em
    ``data-props-id``.
    """
    partes = token.split_contents()
    if len(partes) not in (2, 3):
        raise template.TemplateSyntaxError(
            "Uso: {% v8_island nome [props] %}...{% endv8_island %}"
        )
    nome = parser.compile_filter(partes[1])
    props = parser.compile_filter(partes[2]) if len(partes) == 3 else None
    nodelist = parser.parse(("endv8_island",))
    parser.delete_first_token()
    return IlhaNode(nome, props, nodelist)


@register.simple_tag(takes_context=True)
def v8_portal_pode_ativar(context):
    """Diz se o usuário pode ligar o v8 na raiz do portal (docs/specs/v8/portal.md)."""
    return s_portal.pode_ativar(_usuario(context))


@register.simple_tag(takes_context=True)
def v8_portal_ativo(context):
    """Diz se a requisição está com o v8 ligado na raiz do portal."""
    return bool(getattr(context.get("request"), "v8_portal", False))
