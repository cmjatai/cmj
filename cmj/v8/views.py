"""Views do v8: páginas, zonas SPA, fragmentos, endpoints JSON e o 404.

As views só autenticam, autorizam, validam a entrada, chamam o serviço e
respondem. Dados e decisões vêm de ``cmj/v8/services``.

As respostas HTML saem por ``django.shortcuts.render``. Não use
``TemplateResponse``: um middleware do legado reescreve o contexto dela.
"""

import hashlib
import json
from urllib.parse import quote, urlencode

from django.contrib import messages
from django.http import Http404, HttpResponseRedirect, JsonResponse
from django.middleware.csrf import get_token
from django.shortcuts import render
from django.urls import reverse
from django.utils.cache import patch_cache_control
from django.views import View

from cmj.v8.services import s_demo, s_ds, s_global, s_portal, s_respostas

PASTA_FRAGMENTOS = "v8/partials/"


def requisicao_do_cliente(request):
    """Diz se a requisição veio do cliente HTTP do frontend, e não de navegação."""
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return True
    aceita = request.headers.get("Accept", "")
    return "application/json" in aceita and "text/html" not in aceita


def dados_layout(titulo, menu_ativo=None, trilha=(), zona=None, tema=None):
    """Monta a variável de contexto ``v8``, a única que os layouts leem.

    ``tema`` fixa o tema da página, só na prévia de um tema; sem ele vale o do
    cookie.
    """
    return {
        "titulo": titulo,
        "menu_ativo": menu_ativo,
        "trilha": list(trilha),
        "zona": zona,
        "tema": tema,
    }


def responder_pagina(request, template, v8, contexto=None, status=200):
    """Resposta HTML de página: privada e com o cookie ``csrftoken`` garantido."""
    get_token(request)
    resposta = render(request, template, {**(contexto or {}), "v8": v8}, status=status)
    patch_cache_control(resposta, private=True)
    return resposta


def _inteiro(valor, padrao):
    try:
        return int(valor)
    except (TypeError, ValueError):
        return padrao


class AcessoV8Mixin:
    """Regra de acesso comum a todas as views do v8.

    ``exige`` é ``None`` (pública), ``s_global.AUTENTICADO``,
    ``s_global.SUPERUSUARIO`` ou uma permissão. A recusa sai em JSON para o
    cliente HTTP do frontend, e como redirecionamento ao login ou página de
    erro para a navegação comum. Views com ``responde_json`` respondem sempre
    em JSON.
    """

    exige = None
    responde_json = False

    def get_exige(self):
        return self.exige

    def quer_json(self):
        return self.responde_json or requisicao_do_cliente(self.request)

    def dispatch(self, request, *args, **kwargs):
        metodo = request.method.lower()
        if metodo not in self.http_method_names or not hasattr(self, metodo):
            return self.http_method_not_allowed(request, *args, **kwargs)
        situacao = s_global.situacao_acesso(request.user, self.get_exige())
        if situacao == s_global.NAO_AUTENTICADO:
            return self.responder_nao_autenticado()
        if situacao == s_global.SEM_PERMISSAO:
            return self.responder_sem_permissao()
        try:
            return super().dispatch(request, *args, **kwargs)
        except Http404:
            return self.responder_nao_encontrado()

    def responder_nao_autenticado(self):
        if self.quer_json():
            return JsonResponse(s_respostas.nao_autenticado(), status=401)
        # O retorno leva só o caminho e a query da página pedida, sem host.
        retorno = quote(self.request.get_full_path(), safe="/")
        return HttpResponseRedirect(f"{reverse('cmj.core:login')}?next={retorno}")

    def responder_sem_permissao(self):
        if self.quer_json():
            return JsonResponse(s_respostas.sem_permissao(), status=403)
        return responder_pagina(
            self.request,
            "v8/erros/403.html",
            dados_layout("Acesso negado"),
            status=403,
        )

    def responder_nao_encontrado(self):
        if self.quer_json():
            return JsonResponse(s_respostas.nao_encontrado(), status=404)
        # A página não reproduz o caminho pedido.
        return responder_pagina(
            self.request,
            "v8/erros/404.html",
            dados_layout("Página não encontrada"),
            status=404,
        )


class PaginaV8View(AcessoV8Mixin, View):
    """Base das páginas renderizadas pelo Django. Só ``GET`` e ``HEAD``."""

    http_method_names = ["get", "head"]


class FragmentoV8View(AcessoV8Mixin, View):
    """Base dos fragmentos: só o HTML do template, sem layout.

    ``publico`` só vale em fragmento que não exige autenticação. Nos demais a
    resposta é sempre privada.
    """

    http_method_names = ["get", "head"]
    template_name = None
    publico = False

    def dispatch(self, request, *args, **kwargs):
        resposta = super().dispatch(request, *args, **kwargs)
        resposta["X-Robots-Tag"] = "noindex"
        if self.publico and self.get_exige() is None and resposta.status_code == 200:
            patch_cache_control(resposta, public=True)
        else:
            patch_cache_control(resposta, private=True)
        return resposta

    def responder_fragmento(self, contexto=None):
        if not self.template_name.startswith(PASTA_FRAGMENTOS):
            raise ValueError(f"Fragmento fora de {PASTA_FRAGMENTOS}")
        # Diferencia os ids das ilhas do fragmento dos ids da página que o recebe.
        resumo = hashlib.sha256(self.request.path.encode("utf-8")).hexdigest()[:8]
        contexto = {**(contexto or {}), "v8_ilha_prefixo": f"f{resumo}"}
        return render(self.request, self.template_name, contexto)


class JsonV8View(AcessoV8Mixin, View):
    """Base dos endpoints JSON. Erros de acesso e 404 saem sempre em JSON."""

    responde_json = True

    def ler_corpo(self):
        """Corpo da requisição como dict, ou ``None`` se não for um objeto JSON."""
        try:
            dados = json.loads(self.request.body)
        except ValueError:
            return None
        return dados if isinstance(dados, dict) else None


class InicioView(PaginaV8View):
    def get(self, request):
        return responder_pagina(
            request,
            "v8/paginas/inicio.html",
            dados_layout("Início", "inicio"),
        )


class ZonaV8View(PaginaV8View):
    """Entrega a página de uma zona SPA para o prefixo e qualquer subcaminho.

    O subcaminho é assunto do Vue Router: aqui ele não escolhe template nem é
    renderizado. O layout é o que a zona declara em ``s_global.ZONAS``.
    """

    zona = None

    def get_exige(self):
        return s_global.ZONAS[self.zona].exige

    def get(self, request, subcaminho=None):
        zona = s_global.ZONAS[self.zona]
        return responder_pagina(
            request,
            "v8/paginas/zona.html",
            dados_layout(
                zona.titulo,
                zona.menu_ativo,
                [("Início", s_global.URL_BASE), (zona.titulo, None)],
                zona.nome,
            ),
            {"v8_layout_zona": s_global.LAYOUTS[zona.layout]},
        )


class NaoEncontradoV8View(AcessoV8Mixin, View):
    """Todo caminho de ``/v8/`` que não é página, zona, fragmento nem endpoint."""

    def dispatch(self, request, *args, **kwargs):
        return self.responder_nao_encontrado()


# ---------------------------------------------------------------------------
# Demonstração: tudo exige superusuário e nada é gravado.
# ---------------------------------------------------------------------------


def _filtros_demo(request):
    return s_demo.normalizar_filtros(
        request.GET.get("q", ""),
        request.GET.get("situacao", ""),
        request.GET.get("cidade", ""),
    )


def _paginacao_demo(url, filtros, resultado):
    """Links de paginação que mantêm os filtros."""

    def link(pagina):
        parametros = {chave: valor for chave, valor in filtros.items() if valor}
        if pagina > 1:
            parametros["pagina"] = pagina
        return f"{url}?{urlencode(parametros)}" if parametros else url

    atual = resultado["pagina"]
    ultima = resultado["paginas"]
    return {
        "anterior": link(atual - 1) if atual > 1 else None,
        "proxima": link(atual + 1) if atual < ultima else None,
        "paginas": [
            {"numero": numero, "url": link(numero), "atual": numero == atual}
            for numero in range(1, ultima + 1)
        ],
    }


def _cliente_ou_404(pk):
    cliente = s_demo.obter(_inteiro(pk, None))
    if cliente is None:
        raise Http404
    return cliente


class DemoClientesView(PaginaV8View):
    exige = s_global.SUPERUSUARIO

    def get(self, request):
        filtros = _filtros_demo(request)
        resultado = s_demo.listar(
            **filtros, pagina=_inteiro(request.GET.get("pagina"), 1)
        )
        url = reverse("cmj.v8:demo_clientes")
        return responder_pagina(
            request,
            "v8/demo/clientes.html",
            dados_layout(
                "Clientes",
                "demo-clientes",
                [("Início", s_global.URL_BASE), ("Clientes", None)],
            ),
            {
                "filtros": filtros,
                "situacoes": s_demo.SITUACOES,
                "cidades": s_demo.cidades(),
                "resultado": resultado,
                "paginacao": _paginacao_demo(url, filtros, resultado),
                "props_tabela": {
                    "clientes": resultado["itens"],
                    "formulario": "demo-arquivar",
                },
            },
        )


class DemoLayoutView(PaginaV8View):
    """Página de demonstração de um layout.

    O layout é fixado na rota, uma por layout, e nunca vem da requisição.
    """

    exige = s_global.SUPERUSUARIO
    layout = None

    def get(self, request):
        layout = s_demo.layout_demo(self.layout)
        titulo = f"Layout {layout['nome']}"
        return responder_pagina(
            request,
            f"v8/demo/layouts/{layout['nome']}.html",
            dados_layout(
                titulo,
                f"demo-layout-{layout['nome']}",
                [("Início", s_global.URL_BASE), (titulo, None)],
            ),
            {"layout": layout, "layouts": s_demo.layouts_demo()},
        )


class DemoArquivarView(AcessoV8Mixin, View):
    """Ação em massa da lista: ``POST`` com CSRF, mensagem e redirecionamento."""

    exige = s_global.SUPERUSUARIO
    http_method_names = ["post"]

    def post(self, request):
        total = s_demo.arquivar(request.POST.getlist("ids"))
        if total:
            messages.success(
                request,
                f"{total} cliente(s) arquivado(s). Demonstração: nada foi gravado.",
            )
        else:
            messages.warning(request, "Nenhum cliente selecionado para arquivar.")
        return HttpResponseRedirect(reverse("cmj.v8:demo_clientes"))


class DemoClienteView(PaginaV8View):
    exige = s_global.SUPERUSUARIO

    def get(self, request, pk):
        cliente = _cliente_ou_404(pk)
        return responder_pagina(
            request,
            "v8/demo/cliente.html",
            dados_layout(
                cliente["nome"],
                "demo-clientes",
                [
                    ("Início", s_global.URL_BASE),
                    ("Clientes", reverse("cmj.v8:demo_clientes")),
                    (cliente["nome"], None),
                ],
            ),
            {"cliente": cliente},
        )


class DemoClienteHistoricoFragmento(FragmentoV8View):
    exige = s_global.SUPERUSUARIO
    template_name = "v8/partials/demo/cliente_historico.html"

    def get(self, request, pk):
        cliente = _cliente_ou_404(pk)
        return self.responder_fragmento(
            {"cliente": cliente, "eventos": s_demo.historico(cliente["id"])}
        )


class DemoApiClientesView(JsonV8View):
    exige = s_global.SUPERUSUARIO
    http_method_names = ["get", "post"]

    def get(self, request):
        return JsonResponse(
            s_demo.listar(
                **_filtros_demo(request),
                pagina=_inteiro(request.GET.get("pagina"), 1),
                tamanho=_inteiro(request.GET.get("tamanho"), s_demo.TAMANHO_PADRAO),
            )
        )

    def post(self, request):
        dados = self.ler_corpo()
        if dados is None:
            return JsonResponse(s_respostas.erro_corpo_invalido(), status=400)
        cliente, form = s_demo.validar(dados)
        if cliente is None:
            return JsonResponse(s_respostas.erro_validacao(form), status=400)
        return JsonResponse(cliente, status=201)


class DemoApiClienteView(JsonV8View):
    exige = s_global.SUPERUSUARIO
    http_method_names = ["get", "put"]

    def get(self, request, pk):
        return JsonResponse(_cliente_ou_404(pk))

    def put(self, request, pk):
        atual = _cliente_ou_404(pk)
        dados = self.ler_corpo()
        if dados is None:
            return JsonResponse(s_respostas.erro_corpo_invalido(), status=400)
        cliente, form = s_demo.validar(dados, pk=atual["id"])
        if cliente is None:
            return JsonResponse(s_respostas.erro_validacao(form), status=400)
        return JsonResponse(cliente)


class DemoApiNegadoView(JsonV8View):
    """Responde sempre 403, para a demonstração do tratamento de ``sem_permissao``."""

    exige = s_global.SUPERUSUARIO
    http_method_names = ["get"]

    def get(self, request):
        return JsonResponse(s_respostas.sem_permissao(), status=403)


# ---------------------------------------------------------------------------
# Design system (docs/specs/v8/ds.md e temas.md): as páginas são públicas, e
# escolher o tema segue s_ds.EXIGE_USAR_TEMA, hoje também público.
# ---------------------------------------------------------------------------

_URL_DS = "/v8/ds/"


class DsVitrineView(PaginaV8View):
    """Vitrine do padrão visual, pública. Com ``tema``, a prévia desse tema.

    O tema da prévia é fixado na rota, uma por tema do registro, e nunca vem da
    requisição. A prévia não grava nada.
    """

    tema = None

    def get(self, request):
        contexto = {
            "secoes": s_ds.SECOES,
            "amostras": s_ds.amostras(),
            "pode_usar_tema": s_ds.pode_usar_tema(request.user),
        }
        if self.tema is None:
            v8 = dados_layout(
                "Design system",
                "ds-vitrine",
                [("Início", s_global.URL_BASE), ("Design system", None)],
            )
        else:
            em_vigor = s_global.tema_em_vigor(request.COOKIES)
            previa = s_ds.tema(self.tema, em_vigor)
            v8 = dados_layout(
                previa["rotulo"],
                "ds-temas",
                [
                    ("Início", s_global.URL_BASE),
                    ("Design system", _URL_DS),
                    ("Temas", reverse("cmj.v8:ds_temas")),
                    (previa["rotulo"], None),
                ],
                tema=self.tema,
            )
            contexto["previa"] = previa
        return responder_pagina(request, "v8/ds/vitrine.html", v8, contexto)


class DsTemasView(PaginaV8View):
    """Lista dos temas, pública."""

    def get(self, request):
        return responder_pagina(
            request,
            "v8/ds/temas.html",
            dados_layout(
                "Temas",
                "ds-temas",
                [
                    ("Início", s_global.URL_BASE),
                    ("Design system", _URL_DS),
                    ("Temas", None),
                ],
            ),
            {
                "temas": s_ds.temas(s_global.tema_em_vigor(request.COOKIES)),
                "pode_usar_tema": s_ds.pode_usar_tema(request.user),
            },
        )


class DsTemaUsarView(AcessoV8Mixin, View):
    """Escolhe o tema para o navegador: ``POST`` com CSRF, cookie e redirecionamento.

    O tema é fixado na rota. O destino é sempre a lista de temas.
    """

    exige = s_ds.EXIGE_USAR_TEMA
    http_method_names = ["post"]
    tema = None

    def post(self, request):
        resposta = HttpResponseRedirect(reverse("cmj.v8:ds_temas"))
        resposta.set_cookie(**s_global.cookie_tema(self.tema))
        messages.success(
            request, f"{s_global.TEMAS[self.tema]} em uso neste navegador."
        )
        return resposta


class PortalAtivarView(AcessoV8Mixin, View):
    """Liga o v8 na raiz do portal neste navegador (docs/specs/v8/portal.md).

    Só superusuário, só ``POST`` com CSRF. Volta para ``next`` se for caminho do
    mesmo host, senão para ``/``.
    """

    exige = s_global.SUPERUSUARIO
    http_method_names = ["post"]

    def post(self, request):
        resposta = HttpResponseRedirect(
            s_portal.destino(request.POST.get("next"), request.get_host())
        )
        resposta.set_cookie(**s_portal.cookie_ativar(request.user))
        return resposta


class PortalDesativarView(AcessoV8Mixin, View):
    """Desliga o v8 na raiz do portal neste navegador. Qualquer pessoa, só ``POST``."""

    http_method_names = ["post"]

    def post(self, request):
        resposta = HttpResponseRedirect(
            s_portal.destino(request.POST.get("next"), request.get_host())
        )
        resposta.delete_cookie(**s_portal.cookie_desativar())
        return resposta
