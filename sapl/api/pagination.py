from django.conf import settings
from django.core.paginator import EmptyPage
from rest_framework import pagination
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response


class StandardPagination(pagination.PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100

    def paginate_queryset(self, queryset, request, view=None):
        if request.query_params.get("get_all", "").lower() == "true":
            self.check_get_all_limit(queryset, request, view)
            return None
        return super().paginate_queryset(queryset, request, view=view)

    def check_get_all_limit(self, queryset, request, view=None):
        """``get_all`` só devolve a lista inteira até o teto configurado. Fica
        sem teto quem tem a permissão ``list_`` do model listado."""
        model = getattr(queryset, "model", None)
        if model is None:
            model = getattr(getattr(view, "queryset", None), "model", None)

        user = getattr(request, "user", None)
        if model is not None and user is not None and user.is_authenticated:
            if user.has_perm(f"{model._meta.app_label}.list_{model._meta.model_name}"):
                return

        limit = settings.API_GET_ALL_MAX_ITEMS
        if isinstance(queryset, (list, tuple)):
            total = len(queryset)
        else:
            # conta só até passar do teto, sem percorrer a tabela inteira
            total = queryset[: limit + 1].count()

        if total > limit:
            raise ValidationError(
                {
                    "get_all": [
                        f"A consulta devolveria mais de {limit} itens. Restrinja os "
                        "filtros ou use a paginação (page e page_size)."
                    ]
                }
            )

    def get_paginated_response_schema(self, schema):
        r = {
            "type": "object",
            "properties": {
                "pagination": {
                    "type": "object",
                    "properties": {
                        "links": {
                            "type": "object",
                            "properties": {
                                "next": {
                                    "type": "string",
                                    "nullable": True,
                                    "format": "uri",
                                    "example": "http://api.example.org/accounts/?{page_query_param}=4".format(
                                        page_query_param=self.page_query_param
                                    ),
                                },
                                "previous": {
                                    "type": "string",
                                    "nullable": True,
                                    "format": "uri",
                                    "example": "http://api.example.org/accounts/?{page_query_param}=2".format(
                                        page_query_param=self.page_query_param
                                    ),
                                },
                            },
                        },
                        "previous_page": {
                            "type": "integer",
                            "example": 123,
                        },
                        "next_page": {
                            "type": "integer",
                            "example": 123,
                        },
                        "start_index": {
                            "type": "integer",
                            "example": 123,
                        },
                        "end_index": {
                            "type": "integer",
                            "example": 123,
                        },
                        "total_entries": {
                            "type": "integer",
                            "example": 123,
                        },
                        "total_pages": {
                            "type": "integer",
                            "example": 123,
                        },
                        "page": {
                            "type": "integer",
                            "example": 123,
                        },
                    },
                },
                "results": schema,
            },
        }
        return r

    def get_paginated_response(self, data):
        try:
            previous_page_number = self.page.previous_page_number()
        except EmptyPage:
            previous_page_number = None

        try:
            next_page_number = self.page.next_page_number()
        except EmptyPage:
            next_page_number = None

        return Response(
            {
                "pagination": {
                    "links": {
                        "next": self.get_next_link(),
                        "previous": self.get_previous_link(),
                    },
                    "previous_page": previous_page_number,
                    "next_page": next_page_number,
                    "start_index": self.page.start_index(),
                    "end_index": self.page.end_index(),
                    "total_entries": self.page.paginator.count,
                    "total_pages": self.page.paginator.num_pages,
                    "page": self.page.number,
                },
                "results": data,
            }
        )
