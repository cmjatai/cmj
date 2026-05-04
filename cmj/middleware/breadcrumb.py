import logging

from cmj.utils import get_breadcrumb_classes

logger = logging.getLogger(__name__)


class BreadCrumbMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_view(self, request, func, args, kwargs):
        pass

    def process_exception(self, request, exception):
        pass

    def process_template_response(self, request, response):
        try:
            context = response.context_data

            if request.path.startswith("/api/") or not context:
                return response

            return get_breadcrumb_classes(context, request, response)
        except:
            return response
