class LoaContextDataMixin:

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        path = context.get("path", "")
        context["path"] = f"{path} container-loa"
        return context
