from django.conf import settings
from django.core.cache import cache
from django.http import HttpResponse
from drf_spectacular.views import SpectacularAPIView


class CachedSchemaAPIView(SpectacularAPIView):
    """Esquema OpenAPI servido do cache (docs/specs/api/paginacao-custo.md).

    O esquema é o mesmo para qualquer usuário e muda só com o código. Guarda-se
    a resposta já convertida, por formato e idioma, para que gerar e converter
    não se repitam a cada requisição.
    """

    cache_timeout = 60 * 60

    def get(self, request, *args, **kwargs):
        key = self.get_cache_key(request)
        cached = cache.get(key)
        if cached is not None:
            filename = self._get_filename(request, None)
            return HttpResponse(
                cached["content"],
                content_type=cached["content_type"],
                headers={"Content-Disposition": f'inline; filename="{filename}"'},
            )

        response = super().get(request, *args, **kwargs)
        if response.status_code == 200:
            response.add_post_render_callback(
                lambda rendered: self.store(key, rendered)
            )
        return response

    def get_cache_key(self, request):
        # `version` não entra na chave: sem versionamento na API ele não muda o
        # esquema, e o cliente pode mandar qualquer valor
        lang = request.GET.get("lang", "")
        if lang not in dict(settings.LANGUAGES):
            lang = ""
        renderer = request.accepted_renderer
        return ":".join(
            (
                "sapl.api.schema",
                str(settings.PORTALCMJ_VERSION),
                renderer.media_type,
                lang,
            )
        )

    def store(self, key, response):
        cache.set(
            key,
            {"content": response.content, "content_type": response["Content-Type"]},
            self.cache_timeout,
        )
