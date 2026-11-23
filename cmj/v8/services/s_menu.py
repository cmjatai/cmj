"""Menu do shell do v8 e o filtro por permissão.

O menu só esconde o que o usuário não usaria. Quem protege cada tela é a view
dela.
"""

from dataclasses import dataclass

from cmj.v8.services.s_global import SUPERUSUARIO, atende

# Entra na chave de cache do HTML do menu. Aumente ao mudar a árvore ou o
# template do menu.
VERSAO_MENU = 4


@dataclass(frozen=True)
class ItemMenu:
    """Item da árvore do menu.

    ``permissao`` é ``None`` (todos, inclusive anônimo), uma permissão, uma
    tupla de permissões em que basta uma, ou ``SUPERUSUARIO``.
    """

    id: str
    rotulo: str
    url: str = ""
    icone: str = ""
    permissao: object = None
    filhos: tuple = ()


MENU = (
    ItemMenu("inicio", "Início", "/v8/", "casa"),
    ItemMenu(
        "demo",
        "Demonstração",
        icone="grade",
        permissao=SUPERUSUARIO,
        filhos=(
            ItemMenu(
                "demo-clientes",
                "Clientes (página com ilhas)",
                "/v8/demo/clientes/",
                permissao=SUPERUSUARIO,
            ),
            ItemMenu(
                "demo-spa",
                "Clientes (zona SPA)",
                "/v8/demo/spa/",
                permissao=SUPERUSUARIO,
            ),
            ItemMenu(
                "demo-layout-landing",
                "Layout landing",
                "/v8/demo/layouts/landing/",
                permissao=SUPERUSUARIO,
            ),
            ItemMenu(
                "demo-layout-app_topbar",
                "Layout app_topbar",
                "/v8/demo/layouts/app_topbar/",
                permissao=SUPERUSUARIO,
            ),
            ItemMenu(
                "demo-layout-app_sidebar",
                "Layout app_sidebar",
                "/v8/demo/layouts/app_sidebar/",
                permissao=SUPERUSUARIO,
            ),
            ItemMenu(
                "demo-layout-minimal",
                "Layout minimal",
                "/v8/demo/layouts/minimal/",
                permissao=SUPERUSUARIO,
            ),
        ),
    ),
    # Público (docs/specs/v8/ds.md, D1).
    ItemMenu(
        "ds",
        "Design system",
        icone="paleta",
        filhos=(
            ItemMenu("ds-vitrine", "Vitrine", "/v8/ds/"),
            ItemMenu("ds-temas", "Temas", "/v8/ds/temas/"),
        ),
    ),
)


def _filtrar(itens, usuario, ativo):
    visiveis = []
    for item in itens:
        if not atende(usuario, item.permissao):
            continue
        filhos = _filtrar(item.filhos, usuario, ativo)
        if item.filhos and not filhos:
            # Grupo sem filho visível some.
            continue
        visiveis.append(
            {
                "id": item.id,
                "rotulo": item.rotulo,
                "url": item.url,
                "icone": item.icone,
                "ativo": ativo is not None and item.id == ativo,
                "aberto": any(f["ativo"] or f["aberto"] for f in filhos),
                "filhos": filhos,
            }
        )
    return visiveis


def menu_para(usuario, ativo=None):
    """Árvore do menu que o usuário pode ver, com o item ativo marcado.

    O item de ``id`` igual a ``ativo`` sai com ``ativo=True``, e os grupos
    acima dele, com ``aberto=True``.
    """
    return _filtrar(MENU, usuario, ativo)
